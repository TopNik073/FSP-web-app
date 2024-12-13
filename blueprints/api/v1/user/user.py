import os
import logging
from datetime import datetime, timedelta, timezone
import jwt

from flask import Blueprint, request
from DB.user import User
from DB.models.enums.user_roles import UserRoles
from DB.FSPevent import FSPevent

from blueprints.api.v1.responses import get_200, get_400, get_401, get_403, get_404, get_500
from blueprints.jwt_guard import jwt_guard, check_user, check_admin

from emailer.EmailService import EmailService

user = Blueprint("user", __name__)
logger = logging.getLogger(__name__)
emailer = EmailService()


@user.post("/profile")
@jwt_guard
@check_user
def get_user():
    """Получение информации о пользователе (профиль)"""
    try:
        user: User = request.user
        data = user.get_self_response()

        return get_200(data)
    except Exception as e:
        logger.error(f"Error in get_user: {e}")
        return get_500("Error in get_user")


@user.post("/add")
@jwt_guard
@check_admin
def add_user():
    """Добавление нового пользователя админом"""
    try:
        user: User = User(**request.form.to_dict())
        new_password = user.gen_password()
        user.is_verified = True
        if user.get() is not None:
            return get_400("User already exists")

        if not user.add():
            return get_500("Error in add_user")

        emailer.send_send_password_email(user.email, new_password)

        data = user.get_self_response()

        return get_200(data)
    except Exception as e:
        logger.error(f"Error in add_user: {e}")
        return get_500("Error in add_user")


@user.post("/update")
@jwt_guard
@check_user
def update_user():
    """Обновление информации о пользователе"""
    try:
        user: User = request.user
        user_data = request.form.to_dict()

        if not user.update(user_data):
            return get_500("Error in update_user")

        data = user.get_self_response(user.generate_token())

        return get_200(data)
    except Exception as e:
        logger.error(f"Error in update_user: {e}")
        return get_500("Error in update_user")


@user.post("/update_admin")
@jwt_guard
@check_admin
def update_admin():
    """Обновление информации о пользователе админом"""
    try:
        admin: User = request.user
        user_data = request.form.to_dict()

        if admin.role != UserRoles.ADMIN:
            return get_403("Access denied")

        if not user_data.get("id"):
            return get_400("User id is required")

        user: User = User(id=user_data.get("id"))
        if user.get() is None:
            return get_404("User not found")

        if not user.update(user_data):
            return get_500("Error in update_user")

        data = user.get_self_response()

        return get_200(data)
    except Exception as e:
        logger.error(f"Error in update_admin: {e}")
        return get_500("Error in update_admin")


@user.post("/get")
def get_users_by_role():
    """Получение пользователей по роли"""
    try:
        role = request.form.get("role")

        if role == "USER":
            token = request.headers.get('Authorization')
            if not token:
                return get_401("No token provided")

            
            payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])

            # Проверяем срок действия
            if 'expired_at' in payload:
                exp_timestamp = payload['expired_at']
                if datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) < datetime.now(timezone.utc):
                    return get_401("Token has expired")
                
            user_admin = User(id=payload.get("id"))
            if user_admin.get() is None:
                return get_401("User not found")
            
            if user_admin.role not in [UserRoles.ADMIN, UserRoles.REGIONAL_ADMIN, UserRoles.CENTRAL_ADMIN]:
                return get_403("Access denied")
            
        users: list[User] = User().get_by_role(role)
        data = []
        for user in users:
            data.append(user.get_self_response())

        return get_200(data)
    except Exception as e:
        logger.error(f"Error in get_users_by_role: {e}")
        return get_500("Error in get_users_by_role")
    

@user.post("/delete")
@jwt_guard
@check_admin
def delete_user():
    """Удаление пользователя админом"""
    try:
        user_id = request.form.get("id")
        if not user_id:
            return get_400("User id is required")

        user: User = User(id=user_id)
        if user.get() is None:
            return get_404("User not found")

        user.delete()
        return get_200("Successfully deleted")
    except Exception as e:
        logger.error(f"Error in delete_user: {e}")
        return get_500("Error in delete_user")


@user.post("/subscribe")
@jwt_guard
@check_user
def get_subscriber():
    """Подписка на событие"""
    try:
        user: User = request.user
        event_id = request.form.get("id")

        if not event_id:
            return get_400("Event id is required")

        event = FSPevent(id=event_id)
        if event.get() is None:
            return get_400("Event not found")

        now = datetime.now()
        days_until_event = (event.date_start - now).days

        if days_until_event > 7:
            notification_time = event.date_start - timedelta(days=7)
        elif days_until_event == 1:
            notification_time = now + timedelta(hours=1)
        else:
            notification_time = now + timedelta(days=1)

        notification = {
            "sport": "Спортивное программирование",
            "search_query": event.title,
            "notification_time": notification_time.isoformat(),
            "notification_sent": False,
            "event_category": "FSP",
            "event_id": event.id,
            "email": True,
            "telegram": True,
        }

        user.notifications.append(notification)
        user.update({})

        res = []
        for notification in user.notifications:
            event = FSPevent(id=notification["event_id"])
            if event.get() is None:
                continue

            if event.representative is not None:
                representative = User(event.representative)
                if representative.get():
                    event.representative = representative.get_self_response()

            data = event.get_self()
            data["id"] = event.id
            data.pop("admin_description")
            res.append(data)

        return get_200(res)
    except Exception as e:
        logger.error(f"Error in get_subscriber: {e}")
        return get_500("Error in get_subscriber")


@user.post("/unsubscribe")
@jwt_guard
@check_user
def unsubscribe():
    """Отписка от события"""
    try:
        user: User = request.user
        event_id = request.form.get("id")
        res = []

        for notification in user.notifications:
            if notification["event_id"] == event_id:
                user.notifications.remove(notification)
                user.update({})

                event = FSPevent(id=notification["event_id"])
                if event.get() is None:
                    return get_200(res)
                
                if event.representative is not None:
                    representative = User(event.representative)
                    if user.get():
                        event.representative = representative.get_self_response()

                data = event.get_self()
                data["id"] = event.id
                data.pop("admin_description")
                res.append(data)
                break

        return get_200(res)
    except Exception as e:
        logger.error(f"Error in unsubscribe: {e}")
        return get_500("Error in unsubscribe")


@user.post("/set-up-notification")
@jwt_guard
@check_user
def set_up_notification():
    """Настройка уведомлений о событии"""
    try:
        user: User = request.user
        event_id = request.form.get("id")
        notification_time = request.form.get("notification_time")
        telegram = True if request.form.get("telegram") == "true" else False
        email = True if request.form.get("email") == "true" else False

        if telegram and user.tg_id is None:
            return get_400("User has no telegram id")

        for notification in user.notifications:
            if notification["event_id"] == event_id:
                notification["telegram"] = telegram
                notification["email"] = email
                if notification_time:
                    notification["notification_time"] = datetime.strptime(notification_time,
                                                                          "%Y-%m-%d %H:%M").isoformat()

                user.update({})
                break

        res = []
        for notification in user.notifications:
            event = FSPevent(id=notification["event_id"])
            if event.get() is None:
                continue

            if event.representative is not None:
                representative = User(event.representative)
                if user.get():
                    event.representative = representative.get_self_response()

            data = event.get_self()
            data["id"] = event.id
            data.pop("admin_description")
            res.append(data)

        return get_200(res)
    except Exception as e:
        logger.error(f"Error in set_up_notification: {e}")
        return get_500("Error in set_up_notification")


@user.post("/get_notifications")
@jwt_guard
@check_user
def get_notifications():
    """Получение событий по уведомлениям"""
    try:
        user: User = request.user
        res = []
        for notification in user.notifications:
            event = FSPevent(id=notification["event_id"])
            if event.get() is None:
                continue

            if event.representative is not None:
                representative = User(event.representative)
                if representative.get():
                    event.representative = representative.get_self_response()

            data = event.get_self()
            data["id"] = event.id
            data.pop("admin_description")
            res.append(data)

        return get_200(res)
    except Exception as e:
        logger.error(f"Error in get_notifications: {e}")
        return get_500("Error in get_notifications")

# notifications = [{
#     "sport": str,
#     "search_query": str,
#     "notification_time": datetime,
#     "notification_sent": bool,
#     "event_category": "event" | "category" | "FSP",
#     "event_id": int | None,
#     "email": bool,
#     "telegram": bool,
# }]
