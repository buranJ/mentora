"""Persistence and response schemas for Mentora live classrooms."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LiveSessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"


class LiveSessionBase(SQLModel):
    title: str = Field(min_length=1, max_length=180)
    description: Optional[str] = Field(default=None, max_length=2_000)
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None


class LiveSession(LiveSessionBase, table=True):
    """A course-scoped classroom. LiveKit remains an external media provider."""

    __table_args__ = (
        Index("ix_live_session_course_status", "course_id", "status"),
        Index("ix_live_session_org_status", "org_id", "status"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    session_uuid: str = Field(sa_column=Column(String, nullable=False, unique=True, index=True))
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    instructor_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"), nullable=False, index=True)
    )
    # Opaque by design: never derive a room name from a course title or PII.
    livekit_room_name: str = Field(sa_column=Column(String, nullable=False, unique=True, index=True))
    status: LiveSessionStatus = Field(
        default=LiveSessionStatus.SCHEDULED,
        sa_column=Column(String(16), nullable=False, index=True),
    )
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    ended_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class LiveSessionCreate(LiveSessionBase):
    pass


class LiveSessionRead(LiveSessionBase):
    id: int
    session_uuid: str
    course_uuid: str
    instructor_id: int
    instructor_name: str
    status: LiveSessionStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class LiveSessionJoinResponse(SQLModel):
    server_url: str
    token: str
    session: LiveSessionRead
    is_instructor: bool
