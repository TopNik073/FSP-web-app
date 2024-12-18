import logging
from datetime import datetime

from flask import Blueprint, request

from DB.FSPevent import FSPevent
from DB.FSPevent_archive import FSPevent_archive
from DB.models.enums.user_roles import UserRoles
from DB.user import User
from DB.models.enums.FSPevent_status import FSPEventStatus

from blueprints.api.v1.responses import get_200, get_400, get_404, get_500
from blueprints.jwt_guard import jwt_guard, check_admin

from S3Manager.S3Manager import S3Manager

fsp_events = Blueprint("fsp_events", __name__)
logger = logging.getLogger(__name__)

# Создаем экземпляр S3Manager
s3_manager = S3Manager()


@fsp_events.post("/events")
def api_get_fsp_events():
    try:
        archive = True if request.form.get("archive") == "true" else False
        date_start = request.form.get("date_start")
        date_end = request.form.get("date_end")
        discipline = request.form.get("discipline")
        region = request.form.get("region")
        status = request.form.get("status")

        if date_start:
            date_start = datetime.strptime(date_start, "%Y-%m-%d")
        if date_end:
            date_end = datetime.strptime(date_end, "%Y-%m-%d")

        if archive:
            event = FSPevent_archive(date_start=date_start, date_end=date_end, discipline=discipline, region=region)
        else:
            event = FSPevent(date_start=date_start, date_end=date_end, discipline=discipline, status=status,
                             region=region)

        events = event.get_by_filters()
        res = []
        for event in events:
            if event.representative is not None:
                user = User(event.representative)
                if user.get():
                    event.representative = user.get_self_response()

            data = event.get_self()
            data["id"] = event.id
            data["date_start"] = event.date_start.strftime('%d.%m.%Y %H:%M')
            data["date_end"] = event.date_end.strftime('%d.%m.%Y %H:%M')
            data["region"] = event.region.value if event.region is not None else None
            data["files"] = event.files or []

            res.append(data)

        return get_200(res)
    except Exception as e:
        logger.error(f"Error in api_get_fsp_events: {e}")
        return get_500("Error in api_get_fsp_events")


@fsp_events.post("/events/add")
@jwt_guard
@check_admin
def api_add_fsp_event():
    try:
        event_data = request.form.to_dict()
        event_data["status"] = FSPEventStatus.CONSIDERATION
        event_data["representative"] = request.user.id
        files = request.files.getlist("files")

        event: FSPevent = FSPevent(**event_data)
        user = request.user

        if event.region is None:
            return get_400("Region is required")

        if (user.role == UserRoles.REGIONAL_ADMIN and user.region != event.region) or user.role == UserRoles.USER:
            return get_400("You don't have permission to add event in this region")

        if event.date_start is None or event.date_end is None:
            return get_400("Date start and date end are required")

        event.date_start = datetime.strptime(event.date_start, "%Y-%m-%d")
        event.date_end = datetime.strptime(event.date_end, "%Y-%m-%d")

        if event.date_start > event.date_end:
            return get_400("Date start is greater than date end")

        if event.date_start < datetime.now() or event.date_end < datetime.now():
            return get_400("Date start or date end is in the past")

        if not event.add():
            return get_500("Error adding event")

        uploaded_files = []
        if files:
            uploaded_files = s3_manager.upload_files(
                files,
                f"fsp_events/{event.id}"
            )

            if uploaded_files:
                # Обновляем событие с информацией о файлах
                event.files = uploaded_files
                if not event.update({"files": uploaded_files}):
                    # Если не удалось обновить событие, удаляем загруженные файлы
                    file_paths = [f["path"] for f in uploaded_files]
                    s3_manager.delete_files(file_paths)
                    return get_500("Error updating event with files")

        if event.representative is not None:
            user = User(event.representative)
            if user.get():
                event.representative = user.get_self_response()

        data = event.get_self()
        data["id"] = event.id
        data["date_start"] = event.date_start.strftime('%d.%m.%Y %H:%M')
        data["date_end"] = event.date_end.strftime('%d.%m.%Y %H:%M')
        data["files"] = event.files or []

        return get_200(data)

    except Exception as e:
        logger.error(f"Error in api_add_fsp_event: {e}")
        return get_500("Error in api_add_fsp_event")


@fsp_events.post("/events/update")
@jwt_guard
@check_admin
def api_update_fsp_event():
    try:
        event_data = request.form.to_dict()
        files = request.files.getlist("files")
        user = request.user

        if user.role == UserRoles.REGIONAL_ADMIN and user.region != event_data.get("region"):
            return get_400("You don't have permission to update event in this region")

        if event_data.get("id") is None:
            return get_400("Event id is required")

        event: FSPevent = FSPevent(event_data["id"])
        if not event.get():
            return get_404("Event not found")

        # Удаляем все существующие файлы
        if event.files:
            file_paths = [f["path"] for f in event.files]
            s3_manager.delete_files(file_paths)
            event.files = []

        # Загружаем новые файлы
        if files:
            uploaded_files = s3_manager.upload_files(
                files,
                f"fsp_events/{event.id}"
            )
            if uploaded_files:
                event.files = uploaded_files

        if not event.update(event_data):
            return get_500("Error in update")

        if event.representative is not None:
            user = User(event.representative)
            if user.get():
                event.representative = user.get_self_response()

        data = event.get_self()
        data["id"] = event.id
        data["date_start"] = event.date_start.strftime('%d.%m.%Y %H:%M')
        data["date_end"] = event.date_end.strftime('%d.%m.%Y %H:%M')
        data["files"] = event.files or []

        return get_200(data)
    except Exception as e:
        logger.error(f"Error in api_update_fsp_event: {e}")
        return get_500("Error in api_update_fsp_event")


@fsp_events.post("/events/archive")
@jwt_guard
@check_admin
def api_archive_fsp_event():
    try:
        event_id = request.form.get("id")
        user = request.user
        if not event_id:
            return get_400("Event id is required")

        event: FSPevent = FSPevent(id=event_id)
        if not event.get():
            return get_404("Event not found")

        if user.role == UserRoles.REGIONAL_ADMIN and user.region != event.region:
            return get_400("You don't have permission to archive event in this region")

        archive_event = FSPevent_archive(**event.get_self())

        if not archive_event.add():
            return get_500("Error in archive event")

        event.delete()

        if archive_event.representative is not None:
            user = User(archive_event.representative)
            if user.get():
                archive_event.representative = user.get_self_response()

        data = archive_event.get_self()
        data["id"] = archive_event.id
        data["date_start"] = archive_event.date_start.strftime('%d.%m.%Y %H:%M')
        data["date_end"] = archive_event.date_end.strftime('%d.%m.%Y %H:%M')

        return get_200(data)
    except Exception as e:
        logger.error(f"Error in api_archive_fsp_event: {e}")
        return get_500("Error in api_archive_fsp_event")


@fsp_events.post("/events/restore")
@jwt_guard
@check_admin
def api_restore_fsp_event():
    try:
        event_id = request.form.get("id")
        user = request.user
        if not event_id:
            return get_400("Event id is required")

        archive_event: FSPevent_archive = FSPevent_archive(id=event_id)
        if not archive_event.get():
            return get_404("Archive event not found")

        if user.role == UserRoles.REGIONAL_ADMIN and user.region != archive_event.region:
            return get_400("You don't have permission to restore event in this region")

        event = FSPevent(**archive_event.get_self_restore())

        if not event.add():
            return get_500("Error in restore event")

        archive_event.delete()

        if event.representative is not None:
            user = User(event.representative)
            if user.get():
                event.representative = user.get_self_response()

        data = event.get_self()
        data["id"] = event.id
        data["date_start"] = event.date_start.strftime('%d.%m.%Y %H:%M')
        data["date_end"] = event.date_end.strftime('%d.%m.%Y %H:%M')

        return get_200(data)
    except Exception as e:
        logger.error(f"Error in api_restore_fsp_event: {e}")
        return get_500("Error in api_restore_fsp_event")
