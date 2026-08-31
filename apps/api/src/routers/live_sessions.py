"""HTTP boundary for Mentora's minimal course-scoped live classroom."""

from fastapi import APIRouter, Depends, Request

from src.core.events.database import get_db_session
from src.db.live_learning import LiveSessionCreate, LiveSessionJoinResponse, LiveSessionRead
from src.security.api_token_utils import get_authenticated_non_api_token_user
from src.services.live_learning.live_sessions import (
    create_live_session,
    end_live_session,
    get_live_session,
    join_live_session,
    list_course_live_sessions,
    start_live_session,
)

router = APIRouter()


@router.get("/course/{course_uuid}", response_model=list[LiveSessionRead])
async def api_list_course_live_sessions(request: Request, course_uuid: str, current_user=Depends(get_authenticated_non_api_token_user), db_session=Depends(get_db_session)):
    return await list_course_live_sessions(request, course_uuid, current_user, db_session)


@router.post("/course/{course_uuid}", response_model=LiveSessionRead)
async def api_create_live_session(request: Request, course_uuid: str, payload: LiveSessionCreate, current_user=Depends(get_authenticated_non_api_token_user), db_session=Depends(get_db_session)):
    return await create_live_session(request, course_uuid, payload, current_user, db_session)


@router.get("/{session_uuid}", response_model=LiveSessionRead)
async def api_get_live_session(request: Request, session_uuid: str, current_user=Depends(get_authenticated_non_api_token_user), db_session=Depends(get_db_session)):
    return await get_live_session(request, session_uuid, current_user, db_session)


@router.post("/{session_uuid}/start", response_model=LiveSessionRead)
async def api_start_live_session(request: Request, session_uuid: str, current_user=Depends(get_authenticated_non_api_token_user), db_session=Depends(get_db_session)):
    return await start_live_session(request, session_uuid, current_user, db_session)


@router.post("/{session_uuid}/end", response_model=LiveSessionRead)
async def api_end_live_session(request: Request, session_uuid: str, current_user=Depends(get_authenticated_non_api_token_user), db_session=Depends(get_db_session)):
    return await end_live_session(request, session_uuid, current_user, db_session)


@router.post("/{session_uuid}/join", response_model=LiveSessionJoinResponse)
async def api_join_live_session(request: Request, session_uuid: str, current_user=Depends(get_authenticated_non_api_token_user), db_session=Depends(get_db_session)):
    return await join_live_session(request, session_uuid, current_user, db_session)
