from sqlalchemy import select, delete
from sqlalchemy.orm import sessionmaker

from datetime import datetime, timedelta
from enum import Enum
import random

from DB.DataBase import SessionMaker
from DB.models.token import Token as Token_model
from DB.models.enums.token_types import TokenTypes


class Token:
    def __init__(
            self,
            id: str | None = None,
            token: int | None = None,
            token_type: TokenTypes | None = None,
            user_email: str | None = None,
            created_at: datetime | None = None,
            expires_at: datetime | None = None
    ):
        self.sessionmaker: sessionmaker = SessionMaker().session_factory

        self.id: str | None = id

        self.token: int | None = token
        self.token_type: TokenTypes | None = token_type
        self.user_email: str | None = user_email

        self.created_at: datetime | None = created_at
        self.expires_at: datetime | None = expires_at

        self.get_token_type()

    def add(self) -> bool:
        try:
            with self.sessionmaker() as session:
                data = self.get_self()
                data["expires_at"] = (datetime.now() + timedelta(minutes=15))
                data["token"] = random.randint(100000, 999999)
                
                token = Token_model(**data)
                session.add(token)
                
                session.flush()
                self.id = token.id
                self.token = token.token
                self.expires_at = token.expires_at
                
                session.commit()
                return True
        except Exception as e:
            print(f"Error adding token: {e}")
            return False

    def get(self) -> bool:
        try:
            with self.sessionmaker() as session:
                query = select(Token_model).filter_by(**self.get_filter_by())
                token = session.execute(query).scalars().first()
                if token is None:
                    return None

                self.token = token.token
                self.token_type = token.token_type
                self.user_email = token.user_email
                self.created_at = token.created_at
                self.expires_at = token.expires_at

                return self
        except Exception as e:
            print(f"Error getting token: {e}")
            return False

    def delete(self) -> bool:
        try:
            with self.sessionmaker() as session:
                query = delete(Token_model).filter_by(**self.get_filter_by())
                session.execute(query)
                session.commit()
                return True
        except Exception as e:
            print(f"Error deleting token: {e}")
            return False

    def get_token_type(self) -> None:
        if isinstance(self.token_type, Enum):
            return

        for token_type in TokenTypes:
            if token_type.name == self.token_type or token_type.value == self.token_type:
                self.token_type = token_type
                return

    def get_filter_by(self) -> dict:
        res = {}
        if self.id is not None:
            res["id"] = self.id

        if self.token is not None:
            res["token"] = self.token

        if self.token_type is not None:
            res["token_type"] = self.token_type.name

        if self.user_email is not None:
            res["user_email"] = self.user_email

        return res

    def get_self(self) -> dict:
        return {
            "token": self.token,
            "token_type": self.token_type.name if self.token_type else None,
            "user_email": self.user_email,
            "created_at": self.created_at,
            "expires_at": self.expires_at
        }
