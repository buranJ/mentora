"""Application state and course-RBAC for live classrooms."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, Request, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.courses.courses import Course
from src.db.live_learning import (
    LiveSession,
    LiveSessionCreate,
    LiveSessionJoinResponse,
    LiveSessionRead,
    LiveSessionStatus,
)
from src.db.users import PublicUser, User
from src.security.rbac import AccessAction, check_resource_access
from src.services.live_learning.livekit import LiveKitConfigurationError, LiveKitService


def _display_name(user: User) -> str:
    """Keep e-mail and phone numbers out of LiveKit claims."""
    return user.first_name.strip() or user.username


def _as_read(live_session: LiveSession, course: Course, instructor: User) -> LiveSessionRead:
    return LiveSessionRead(
        id=live_session.id,
        session_uuid=live_session.session_uuid,
        course_uuid=course.course_uuid,
        instructor_id=live_session.instructor_id,
        instructor_name=_display_name(instructor),
        title=live_session.title,
        description=live_session.description,
        scheduled_start_at=live_session.scheduled_start_at,
        scheduled_end_at=live_session.scheduled_end_at,
        status=live_session.status,
        started_at=live_session.started_at,
        ended_at=live_session.ended_at,
        created_at=live_session.created_at,
        updated_at=live_session.updated_at,
    )


async def _load_session(db_session: AsyncSession, session_uuid: str) -> tuple[LiveSession, Course, User]:
    result = await db_session.execute(
        select(LiveSession, Course, User)
        .join(Course, Course.id == LiveSession.course_id)
        .join(User, User.id == LiveSession.instructor_id)
        .where(LiveSession.session_uuid == session_uuid)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Live session not found")
    return row[0], row[1], row[2]


async def _load_course(db_session: AsyncSession, course_uuid: str) -> Course:
    course = (await db_session.execute(select(Course).where(Course.course_uuid == course_uuid))).scalars().first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


async def create_live_session(
    request: Request,
    course_uuid: str,
    payload: LiveSessionCreate,
    current_user: PublicUser,
    db_session: AsyncSession,
) -> LiveSessionRead:
    course = await _load_course(db_session, course_uuid)
    await check_resource_access(request, db_session, current_user, course.course_uuid, AccessAction.UPDATE)

    opaque_id = uuid4().hex
    now = datetime.now(timezone.utc)
    live_session = LiveSession(
        session_uuid=f"live_{opaque_id}",
        livekit_room_name=f"mentora_live_{opaque_id}",
        course_id=course.id,
        org_id=course.org_id,
        instructor_id=current_user.id,
        title=payload.title,
        description=payload.description,
        scheduled_start_at=payload.scheduled_start_at,
        scheduled_end_at=payload.scheduled_end_at,
        created_at=now,
        updated_at=now,
    )
    db_session.add(live_session)
    await db_session.commit()
    await db_session.refresh(live_session)
    instructor = (await db_session.execute(select(User).where(User.id == current_user.id))).scalars().one()
    return _as_read(live_session, course, instructor)


async def list_course_live_sessions(
    request: Request,
    course_uuid: str,
    current_user: PublicUser,
    db_session: AsyncSession,
) -> list[LiveSessionRead]:
    course = await _load_course(db_session, course_uuid)
    await check_resource_access(request, db_session, current_user, course.course_uuid, AccessAction.READ)
    rows = (await db_session.execute(
        select(LiveSession, User)
        .join(User, User.id == LiveSession.instructor_id)
        .where(LiveSession.course_id == course.id)
        .order_by(LiveSession.created_at.desc())
    )).all()
    return [_as_read(live_session, course, instructor) for live_session, instructor in rows]


async def get_live_session(
    request: Request,
    session_uuid: str,
    current_user: PublicUser,
    db_session: AsyncSession,
) -> LiveSessionRead:
    live_session, course, instructor = await _load_session(db_session, session_uuid)
    await check_resource_access(request, db_session, current_user, course.course_uuid, AccessAction.READ)
    return _as_read(live_session, course, instructor)


async def _set_status(
    request: Request,
    session_uuid: str,
    current_user: PublicUser,
    db_session: AsyncSession,
    target_status: LiveSessionStatus,
) -> LiveSessionRead:
    live_session, course, instructor = await _load_session(db_session, session_uuid)
    await check_resource_access(request, db_session, current_user, course.course_uuid, AccessAction.UPDATE)
    if live_session.status == LiveSessionStatus.ENDED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Live session has ended")
    now = datetime.now(timezone.utc)
    live_session.status = target_status
    live_session.updated_at = now
    if target_status == LiveSessionStatus.LIVE and live_session.started_at is None:
        live_session.started_at = now
    if target_status == LiveSessionStatus.ENDED:
        live_session.ended_at = now
    db_session.add(live_session)
    await db_session.commit()
    await db_session.refresh(live_session)
    return _as_read(live_session, course, instructor)


async def start_live_session(request, session_uuid, current_user, db_session) -> LiveSessionRead:
    return await _set_status(request, session_uuid, current_user, db_session, LiveSessionStatus.LIVE)


async def end_live_session(request, session_uuid, current_user, db_session) -> LiveSessionRead:
    return await _set_status(request, session_uuid, current_user, db_session, LiveSessionStatus.ENDED)


async def join_live_session(
    request: Request,
    session_uuid: str,
    current_user: PublicUser,
    db_session: AsyncSession,
    provider: LiveKitService | None = None,
) -> LiveSessionJoinResponse:
    live_session, course, instructor = await _load_session(db_session, session_uuid)
    await check_resource_access(request, db_session, current_user, course.course_uuid, AccessAction.READ)
    is_instructor = current_user.id == live_session.instructor_id
    if live_session.status == LiveSessionStatus.ENDED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Live session has ended")
    if live_session.status != LiveSessionStatus.LIVE and not is_instructor:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Live session has not started")

    user = (await db_session.execute(select(User).where(User.id == current_user.id))).scalars().one()
    try:
        livekit = provider or LiveKitService()
        token = livekit.create_join_token(
            room_name=live_session.livekit_room_name,
            participant_identity=f"user_{user.user_uuid}",
            display_name=_display_name(user),
            is_instructor=is_instructor,
        )
    except LiveKitConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Live classroom is temporarily unavailable",
        )
    return LiveSessionJoinResponse(
        server_url=livekit.settings.server_url,
        token=token,
        session=_as_read(live_session, course, instructor),
        is_instructor=is_instructor,
    )
