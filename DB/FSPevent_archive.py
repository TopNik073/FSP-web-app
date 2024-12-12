from datetime import datetime
from enum import Enum

from sqlalchemy import select, delete
from sqlalchemy.orm import sessionmaker

from DB.DataBase import SessionMaker
from DB.models.FSPevent_archive import FSPevent_archive as FSPevent_archive_model
from DB.models.enums.regions import Regions
from DB.models.FSPevent_status import FSPEventStatus


class FSPevent_archive:
    def __init__(
            self,
            id: str | None = None,
            sport: str | None = None,
            title: str | None = None,
            description: str | None = None,
            admin_description: str | None = None,
            participants: str | None = None,
            participants_num: str | None = None,
            discipline: str | None = None,
            region: Regions | None = None,
            representative: str | None = None,
            place: str | None = None,
            date_start: datetime | None = None,
            date_end: datetime | None = None,
            status: FSPEventStatus | None = None,
            files: list | None = None,
    ):
        self.sessionmaker: sessionmaker = SessionMaker().session_factory

        self.id: str | None = id

        self.sport: str | None = sport
        self.title: str | None = title
        self.description: str | None = description
        self.admin_description: str | None = admin_description
        self.discipline: str | None = discipline

        self.participants: str | None = participants
        self.participants_num: str | None = participants_num

        self.region: Regions | None = region
        self.place: str | None = place
        self.representative: str | None = representative

        self.date_start: datetime | None = date_start
        self.date_end: datetime | None = date_end

        self.status: FSPEventStatus | None = status
        self.files: list | None = files

        self.convert_region_to_key()
        self.convert_status_to_key()

    def add(self) -> bool:
        try:
            with self.sessionmaker() as session:
                event = FSPevent_archive_model(**self.get_self())
                session.add(event)
                session.flush()
                self.id = str(event.id)
                session.commit()
                return True
        except Exception as e:
            print(f"Error in add: {e}")
            return False

    def get(self):
        try:
            with self.sessionmaker() as session:
                query = session.query(FSPevent_archive_model).filter_by(id=self.id)
                event = session.scalar(query)
                if event is None:
                    return None

                self.id = str(event.id)
                self.sport = event.sport
                self.title = event.title
                self.description = event.description
                self.admin_description = event.admin_description
                self.participants = event.participants
                self.participants_num = event.participants_num
                self.discipline = event.discipline
                self.region = event.region
                self.representative = event.representative
                self.files = event.files if event.files is not None and len(event.files) > 0 else []
                self.place = event.place
                self.date_start = event.date_start
                self.date_end = event.date_end
                self.status = event.status

                self.convert_region_to_key()
                self.convert_status_to_key()

                return self
        except Exception as e:
            print(f"Error in get: {e}")
            return None
        
    def get_by_self(self):
        try:
            with self.sessionmaker() as session:
                query = select(FSPevent_archive_model).filter(
                    FSPevent_archive_model.title == self.title,
                    FSPevent_archive_model.place == self.place,
                    FSPevent_archive_model.participants == self.participants,
                    FSPevent_archive_model.discipline == self.discipline,
                    FSPevent_archive_model.date_start == self.date_start,
                    FSPevent_archive_model.date_end == self.date_end,
                )
                event = session.execute(query).scalar()
                return event
        except Exception as e:
            print(f"Error in get_by_self: {e}")
            return None

    def convert_region_to_key(self):
        if isinstance(self.region, Enum):
            return

        for reg in Regions:
            if reg.value == self.region or reg.name == self.region:
                self.region = reg
                return

    def convert_status_to_key(self):
        if isinstance(self.status, Enum):
            return

        for status in FSPEventStatus:
            if status.value == self.status or status.name == self.status:
                self.status = status
                return

    def get_self(self) -> dict:
        return {
            "sport": "Спортивное программирование",
            "title": self.title,
            "description": self.description,
            "admin_description": self.admin_description,
            "participants": self.participants,
            "participants_num": self.participants_num,
            "discipline": self.discipline,
            "region": self.region.name if self.region is not None else None,
            "representative": self.representative,
            "place": self.place,
            "date_start": self.date_start,
            "date_end": self.date_end,
            "status": self.status.name if self.status else None,
            "files": self.files if self.files is not None and len(self.files) > 0 else [],
        }

    def get_self_restore(self) -> dict:
        return {
            "sport": "Спортивное программирование",
            "title": self.title if self.title is not None else "",
            "description": self.description if self.description is not None else "",
            "admin_description": self.admin_description if self.admin_description is not None else "",
            "participants": self.participants if self.participants is not None else "",
            "participants_num": self.participants_num if self.participants_num is not None else "",
            "discipline": self.discipline if self.discipline is not None else "",
            "region": self.region.name if self.region is not None else Regions.NONE.name,
            "representative": self.representative if self.representative is not None else "",
            "place": self.place if self.place is not None else "",
            "date_start": self.date_start if self.date_start is not None else "",
            "date_end": self.date_end if self.date_end is not None else "",
            "status": self.status.name if self.status else FSPEventStatus.CONSIDERATION.name,
            "files": self.files if self.files is not None and len(self.files) > 0 else [],
        }

    def get_by_filters(self):
        try:
            with self.sessionmaker() as session:
                query = select(FSPevent_archive_model)
                filters = self.get_filters()
                if filters:
                    query = query.filter_by(**filters)

                if self.date_start is not None:
                    query = query.filter(FSPevent_archive_model.date_start >= self.date_start)
                if self.date_end is not None:
                    query = query.filter(FSPevent_archive_model.date_end <= self.date_end)

                events: list[FSPevent_archive_model] = session.scalars(query).all()
                if events is None:
                    return []

                return [FSPevent_archive(**self.get_from_model(event)) for event in events]
        except Exception as e:
            print(f"Error in get_by_filters: {e}")
            return []

    def get_from_model(self, model):
        return {
            "id": model.id,
            "sport": model.sport,
            "title": model.title,
            "description": model.description,
            "admin_description": model.admin_description,
            "participants": model.participants,
            "participants_num": model.participants_num,
            "discipline": model.discipline,
            "region": model.region,
            "representative": model.representative,
            "files": model.files,
            "place": model.place,
            "date_start": model.date_start,
            "date_end": model.date_end,
            "status": model.status,
        }

    def get_filters(self) -> dict:
        res = {}
        if self.discipline is not None and self.discipline != "":
            res["discipline"] = self.discipline

        if self.region is not None:
            res["region"] = self.region

        return res

    def delete(self) -> bool:
        try:
            with self.sessionmaker() as session:
                query = delete(FSPevent_archive_model).filter_by(id=self.id)
                session.execute(query)
                session.commit()
                return True
        except Exception as e:
            print(e)
            return False
