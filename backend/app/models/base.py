from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    refreshed_at: Mapped[datetime] = mapped_column(
        server_default="CURRENT_TIMESTAMP"
    )
