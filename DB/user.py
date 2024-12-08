from datetime import datetime, timedelta, timezone
import uuid
from jwt import encode
import os
import random
import string
from enum import Enum
from dotenv import load_dotenv

from werkzeug.security import generate_password_hash

from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker

from DB.DataBase import SessionMaker

from DB.models.user import Users
from DB.models.enums.user_roles import UserRoles
from DB.models.enums.regions import Regions

load_dotenv()

class User:
    def __init__(
        self,
        id: str | None = None,
        is_verified: bool = False,
        name: str | None = None,
        email: str = None,
        password: str = None,
        tg_id: int = None,
        username: str = None,
        region: Regions | None = None,
        role: UserRoles | None = None,
        notifications: list[dict | None] = None,
        auto_add: bool = False,
    ):
        self.sessionmaker: sessionmaker = SessionMaker().session_factory

        self.id: str | None = id
        self.is_verified: bool = is_verified

        self.name: str | None = name
        self.email: str = email
        self.password: str = password

        self.tg_id: int = tg_id
        self.username: str = username

        self.notifications: list = notifications if notifications is not None else []

        self.region: Regions | None = region
        self.role: UserRoles | None = role

        self.auto_add: bool = auto_add

        self.created_at: datetime | None = None
        self.updated_at: datetime | None = None

        self.convert_region_to_key()
        self.convert_role_to_key()

        if self.auto_add and self.get() is None:
            self.add()

    def get(self):
        try:
            with self.sessionmaker() as session:
                query = select(Users).filter_by(**self.get_filter_by())
                user: Users = session.scalar(query)
                if user is None:
                    return

                self.get_from_model(user)
                self.convert_region_to_key()
                self.convert_role_to_key()

                return self
        except Exception as e:
            print(e)
            raise e
        
    def get_by_role(self, role: UserRoles):
        try:
            with self.sessionmaker() as session:
                query = select(Users).filter_by(role=role)
                users = session.scalars(query).all()
                if users is None:
                    return []

                res = []
                for user in users:
                    temp_user = User()
                    temp_user.get_from_model(user)
                    res.append(temp_user)
                
                return res
        except Exception as e:
            print(e)
            raise e

    def add(self):
        try:
            with self.sessionmaker() as session:
                user: Users = Users(**self.get_self())
                session.add(user)
                session.flush()
                self.id = str(user.id)
                session.commit()
                return self

        except Exception as e:
            print(e)
            raise e
        
    def get_from_model(self, model: Users):
        self.id = str(model.id)
        self.is_verified = model.is_verified
        self.email = model.email
        self.name = model.name
        self.password = model.password
        self.tg_id = model.tg_id
        self.username = model.username
        self.region = model.region
        self.role = model.role
        self.notifications = model.notifications
        self.created_at = model.created_at
        self.updated_at = model.updated_at
        
    def convert_region_to_key(self):
        if isinstance(self.region, Enum):
            return
        
        for reg in Regions:
            if reg.value == self.region or reg.name == self.region:
                self.region = reg
                return
            
    def convert_role_to_key(self):
        if isinstance(self.role, Enum):
            return
        
        for role in UserRoles:
            if role.value == self.role or role.name == self.role:
                self.role = role
                return

    def add_fsp_admin(self):
        try:
            role = UserRoles.REGIONAL_ADMIN
            if self.region.name == Regions.MOSCOW.name:
                role = UserRoles.CENTRAL_ADMIN

            with self.sessionmaker() as session:
                password = self.gen_password()
                fsp_admin = Users(
                    email=self.email, 
                    region=self.region.name, 
                    name=self.name, 
                    password=self.password,
                    role=role,
                    is_verified=True,
                )
                session.add(fsp_admin)
                session.commit()

                return password
        except Exception as e:
            print(f"Error adding FSP admin: {e}")
            return None

    def update(self) -> bool:
        try:
            with self.sessionmaker() as session:
                session.query(Users).filter_by(**self.get_filter_by()).update(self.get_self())
                session.commit()

            return True
        except Exception as e:
            print(e)
            return False

    def delete(self) -> bool:
        try:
            with self.sessionmaker() as session:
                query = select(Users).filter_by(**self.get_filter_by())
                user: Users = session.scalar(query)
                if user is None:
                    raise Exception("Can't find user for deleting")

                session.delete(user)
                session.commit()
        except Exception as e:
            print(e)
            return False
        
    def add_notification(self, sport: str, search: str) -> list[dict]:
        try:
            with self.sessionmaker() as session:
                user = session.query(Users).filter_by(**self.get_filter_by()).first()
                if not user:
                    raise ValueError("User not found")
                
                current_notifications = user.notifications or []
                
                new_notification = {
                    "id": str(uuid.uuid4()),
                    "sport": sport,
                    "search": search
                }
                
                new_notifications = current_notifications + [new_notification]
                
                session.query(Users).filter_by(**self.get_filter_by()).update({
                    "notifications": new_notifications
                }, synchronize_session=False)
                
                session.commit()
                
                self.notifications = new_notifications
                
                return new_notifications
                
        except Exception as e:
            print(f"Error adding notification: {e}")
            raise e
        
    def get_notifications(self):
        try:
            with self.sessionmaker() as session:
                user = session.query(Users).filter_by(**self.get_filter_by()).first()
                if not user:
                    raise ValueError("User not found")
                
                return user.notifications
        except Exception as e:
            print(f"Error getting notifications: {e}")
            raise e

    def get_filter_by(self) -> dict:
        res = {}
        if self.id is not None:
            res["id"] = self.id

        if self.email is not None:
            res["email"] = self.email

        if self.tg_id is not None:
            res["tg_id"] = self.tg_id

        return res

    def get_self(self) -> dict:
        return {
            "is_verified": self.is_verified,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "tg_id": self.tg_id,
            "username": self.username,
            "notifications": self.notifications,
            "region": self.region.name if self.region is not None else None,
            "role": self.role.name if self.role is not None else None,
        }
    
    def get_self_api(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "tg_id": self.tg_id,
        }

    def gen_password(self) -> str:
        chars = string.ascii_letters + string.digits  # a-z + A-Z + 0-9
        password = ''.join(random.choice(chars) for _ in range(10))
        
        self.password = generate_password_hash(password)
        return password

    def login(self) -> dict:
        data = self.get_self_api()
        data["expired_at"] = int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp())
        self.token = encode(
            data, 
            key=os.environ.get("JWT_SECRET"), 
            algorithm="HS256"
        )
        return {
            "token": self.token,
            "user": self.get_self_api()
        }

    def remove_notification(self, notification_id: str):
        try:
            with self.sessionmaker() as session:
                user = session.query(Users).filter_by(**self.get_filter_by()).first()
                if not user:
                    raise ValueError("User not found")
                
                current_notifications = user.notifications or []
                
                new_notifications = [
                    notif for notif in current_notifications 
                    if notif.get('id') != notification_id
                ]
                
                if len(current_notifications) == len(new_notifications):
                    raise ValueError(f"Notification with id {notification_id} not found")
                
                session.query(Users).filter_by(**self.get_filter_by()).update({
                    "notifications": new_notifications
                }, synchronize_session=False)
                
                session.commit()
                
                self.notifications = new_notifications
                
                return True
                
        except Exception as e:
            print(f"Error removing notification: {e}")
            raise e

    def get_users_with_notifications(self):
        try:
            with self.sessionmaker() as session:
                query = select(Users).filter(
                    Users.notifications.is_not(None),
                    func.jsonb_array_length(Users.notifications) > 0
                )
                users = session.scalars(query).all()
                if users is None:
                    raise Exception("Users not found")
                return users
        except Exception as e:
            print(f"Error getting users with notifications: {e}")
            raise e


if __name__ == "__main__":
    user_manager: User = User(auto_add=False)
    print(user_manager.gen_password())
