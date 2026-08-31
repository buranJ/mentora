"""Focused security and token tests for the Phase 2 classroom boundary."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from src.core.events.database import get_db_session
from src.db.live_learning import LiveSession, LiveSessionStatus
from src.routers.live_sessions import router as live_sessions_router
from src.services.live_learning.livekit import LiveKitService, LiveKitSettings, TOKEN_TTL
from src.services.live_learning.live_sessions import join_live_session


def _provider() -> LiveKitService:
    return LiveKitService(LiveKitSettings("ws://localhost:7880", "devkey", "local-test-secret-with-32-characters"))


async def _session(db, course, admin_user, status=LiveSessionStatus.LIVE) -> LiveSession:
    item = LiveSession(
        session_uuid="live_opaque_session",
        livekit_room_name="mentora_live_opaque_room",
        course_id=course.id,
        org_id=course.org_id,
        instructor_id=admin_user.id,
        title="Security test lesson",
        status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@pytest.mark.asyncio
async def test_authorized_instructor_receives_bounded_opaque_token(db, course, admin_user, mock_request):
    live_session = await _session(db, course, admin_user)
    with patch("src.services.live_learning.live_sessions.check_resource_access", new_callable=AsyncMock):
        response = await join_live_session(mock_request, live_session.session_uuid, admin_user, db, _provider())

    claims = jwt.decode(response.token, options={"verify_signature": False})
    grants = claims["video"]
    assert response.server_url == "ws://localhost:7880"
    assert claims["sub"] == "user_user_admin"
    assert "admin@test.com" not in response.token
    assert grants["room"] == "mentora_live_opaque_room"
    assert grants["roomAdmin"] is False
    assert grants["roomCreate"] is False
    assert grants["roomRecord"] is False
    assert "screen_share" in grants["canPublishSources"]
    assert claims["exp"] <= int(datetime.now(timezone.utc).timestamp() + TOKEN_TTL.total_seconds() + 2)


@pytest.mark.asyncio
async def test_authorized_student_receives_non_admin_token_without_screen_share(db, course, admin_user, regular_user, mock_request):
    live_session = await _session(db, course, admin_user)
    with patch("src.services.live_learning.live_sessions.check_resource_access", new_callable=AsyncMock):
        response = await join_live_session(mock_request, live_session.session_uuid, regular_user, db, _provider())

    grants = jwt.decode(response.token, options={"verify_signature": False})["video"]
    assert response.is_instructor is False
    assert grants["room"] == "mentora_live_opaque_room"
    assert grants["roomAdmin"] is False
    assert grants["roomCreate"] is False
    assert grants["ingressAdmin"] is False
    assert grants["canPublishSources"] == ["camera", "microphone"]


@pytest.mark.asyncio
async def test_unauthorized_student_cannot_join(db, course, admin_user, regular_user, mock_request):
    live_session = await _session(db, course, admin_user)
    denied = HTTPException(status_code=403, detail="Course access denied")
    with patch("src.services.live_learning.live_sessions.check_resource_access", new_callable=AsyncMock, side_effect=denied):
        with pytest.raises(HTTPException, match="Course access denied") as error:
            await join_live_session(mock_request, live_session.session_uuid, regular_user, db, _provider())
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_nonexistent_and_ended_sessions_cannot_join(db, course, admin_user, mock_request):
    with pytest.raises(HTTPException) as missing:
        await join_live_session(mock_request, "live_missing", admin_user, db, _provider())
    assert missing.value.status_code == 404

    ended = await _session(db, course, admin_user, LiveSessionStatus.ENDED)
    with patch("src.services.live_learning.live_sessions.check_resource_access", new_callable=AsyncMock):
        with pytest.raises(HTTPException) as ended_error:
            await join_live_session(mock_request, ended.session_uuid, admin_user, db, _provider())
    assert ended_error.value.status_code == 409


@pytest.mark.asyncio
async def test_unauthenticated_join_route_is_rejected(db):
    app = FastAPI()
    app.include_router(live_sessions_router, prefix="/api/v1/live-sessions")
    app.dependency_overrides[get_db_session] = lambda: db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/live-sessions/live_missing/join")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401
