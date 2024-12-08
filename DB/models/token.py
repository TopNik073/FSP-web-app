import uuid
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from DB.models.Base import Base, get_datetime_UTC
from DB.models.enums.token_types import TokenTypes


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    user_email: Mapped[str] = mapped_column(nullable=False)
    token_type: Mapped[TokenTypes] = mapped_column(nullable=False)
    token: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=get_datetime_UTC)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

