"""Add the minimal course-scoped LiveKit classroom session domain.

Revision ID: p2l1v3k1t001
Revises: c7d8e9f0a1b2
Create Date: 2026-08-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p2l1v3k1t001"
down_revision: Union[str, None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "live_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_uuid", sa.String(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("instructor_id", sa.Integer(), nullable=False),
        sa.Column("livekit_room_name", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["instructor_id"], ["user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["org_id"], ["organization.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("livekit_room_name"),
        sa.UniqueConstraint("session_uuid"),
    )
    op.create_index("ix_live_session_session_uuid", "live_session", ["session_uuid"])
    op.create_index("ix_live_session_course_id", "live_session", ["course_id"])
    op.create_index("ix_live_session_org_id", "live_session", ["org_id"])
    op.create_index("ix_live_session_instructor_id", "live_session", ["instructor_id"])
    op.create_index("ix_live_session_livekit_room_name", "live_session", ["livekit_room_name"])
    op.create_index("ix_live_session_status", "live_session", ["status"])
    op.create_index("ix_live_session_course_status", "live_session", ["course_id", "status"])
    op.create_index("ix_live_session_org_status", "live_session", ["org_id", "status"])


def downgrade() -> None:
    op.drop_table("live_session")
