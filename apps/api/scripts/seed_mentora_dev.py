"""Create a small, idempotent dataset for local Mentora UI testing only.

Run from ``apps/api``:
    uv run python scripts/seed_mentora_dev.py --confirm-development
"""

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# ``python scripts/...`` puts only this directory on sys.path. Keep the command
# in this module's docstring usable without requiring callers to export PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlmodel import select

from src.core.events.database import _async_session_factory
from src.db.courses.activities import (
    Activity,
    ActivitySubTypeEnum,
    ActivityTypeEnum,
)
from src.db.courses.chapter_activities import ChapterActivity
from src.db.courses.chapters import Chapter
from src.db.courses.course_chapters import CourseChapter
from src.db.courses.courses import Course, ThumbnailType
from src.db.organizations import Organization
from src.db.resource_authors import (
    ResourceAuthor,
    ResourceAuthorshipEnum,
    ResourceAuthorshipStatusEnum,
)
from src.db.roles import Role
from src.db.user_organizations import UserOrganization
from src.db.users import User
from src.security.security import security_hash_password


DEV_PASSWORD = "MentoraDevOnly!2026"

COURSES = (
    (
        "python-backend",
        "Python Backend Developer",
        "Практический курс по созданию API на Python и FastAPI.",
        0,
        ("Основы Python", "FastAPI и REST", "PostgreSQL в приложении"),
    ),
    (
        "frontend-react",
        "Frontend React Developer",
        "Курс по современному React, TypeScript и пользовательским интерфейсам.",
        1,
        ("React и компоненты", "Состояние и данные", "Производственный frontend"),
    ),
    (
        "ai-business",
        "Искусственный интеллект для бизнеса",
        "Безопасное и практичное применение ИИ в бизнес-процессах.",
        0,
        ("Возможности ИИ", "Сценарии внедрения", "Оценка эффекта"),
    ),
)

INSTRUCTORS = (
    ("irina.instructor@school.dev", "irina-instructor", "Ирина", "Соколова"),
    ("denis.instructor@school.dev", "denis-instructor", "Денис", "Орлов"),
)

STUDENTS = (
    ("anna.student@school.dev", "anna-student", "Анна", "Иванова"),
    ("mikhail.student@school.dev", "mikhail-student", "Михаил", "Петров"),
    ("olga.student@school.dev", "olga-student", "Ольга", "Смирнова"),
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def ensure_user(
    session, *, email: str, username: str, first_name: str, last_name: str, role_id: int, org_id: int
) -> User:
    user = (await session.exec(select(User).where(User.email == email))).first()
    if user is None:
        timestamp = now()
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=security_hash_password(DEV_PASSWORD),
            user_uuid=f"user_{uuid4()}",
            email_verified=True,
            email_verified_at=timestamp,
            signup_method="email",
            creation_date=timestamp,
            update_date=timestamp,
        )
        session.add(user)
        await session.flush()

    membership = (
        await session.exec(
            select(UserOrganization).where(
                UserOrganization.user_id == user.id,
                UserOrganization.org_id == org_id,
            )
        )
    ).first()
    if membership is None:
        timestamp = now()
        session.add(
            UserOrganization(
                user_id=user.id,
                org_id=org_id,
                role_id=role_id,
                creation_date=timestamp,
                update_date=timestamp,
            )
        )
    return user


async def ensure_course(session, *, org_id: int, instructor: User, spec: tuple) -> None:
    slug, name, description, _, modules = spec
    course = (
        await session.exec(
            select(Course).where(Course.org_id == org_id, Course.name == name)
        )
    ).first()
    if course is not None:
        return

    timestamp = now()
    course = Course(
        name=name,
        description=description,
        about=description,
        learnings="Практика, материалы к урокам и итоговый проект.",
        tags="mentora,development",
        public=True,
        published=True,
        open_to_contributors=False,
        thumbnail_type=ThumbnailType.IMAGE,
        thumbnail_image="",
        thumbnail_video="",
        org_id=org_id,
        course_uuid=f"course_mentora_{slug}",
        creation_date=timestamp,
        update_date=timestamp,
    )
    session.add(course)
    await session.flush()
    session.add(
        ResourceAuthor(
            resource_uuid=course.course_uuid,
            user_id=instructor.id,
            authorship=ResourceAuthorshipEnum.CREATOR,
            authorship_status=ResourceAuthorshipStatusEnum.ACTIVE,
            creation_date=timestamp,
            update_date=timestamp,
        )
    )

    for chapter_order, module_name in enumerate(modules, start=1):
        chapter = Chapter(
            name=module_name,
            description=f"Модуль {chapter_order}: {module_name}.",
            thumbnail_image="",
            org_id=org_id,
            course_id=course.id,
            chapter_uuid=f"chapter_mentora_{slug}_{chapter_order}",
            creation_date=timestamp,
            update_date=timestamp,
        )
        session.add(chapter)
        await session.flush()
        session.add(
            CourseChapter(
                course_id=course.id,
                chapter_id=chapter.id,
                org_id=org_id,
                order=chapter_order,
                creation_date=timestamp,
                update_date=timestamp,
            )
        )
        for lesson_order in range(1, 3):
            lesson_name = f"Урок {chapter_order}.{lesson_order}: {module_name}"
            activity = Activity(
                name=lesson_name,
                activity_type=ActivityTypeEnum.TYPE_DYNAMIC,
                activity_sub_type=ActivitySubTypeEnum.SUBTYPE_DYNAMIC_MARKDOWN,
                content={"content": f"# {lesson_name}\n\nМатериал для локального тестирования Mentora."},
                details={"duration_minutes": 25},
                published=True,
                org_id=org_id,
                course_id=course.id,
                activity_uuid=f"activity_mentora_{slug}_{chapter_order}_{lesson_order}",
                creation_date=timestamp,
                update_date=timestamp,
                last_modified_by_id=instructor.id,
            )
            session.add(activity)
            await session.flush()
            session.add(
                ChapterActivity(
                    chapter_id=chapter.id,
                    activity_id=activity.id,
                    course_id=course.id,
                    org_id=org_id,
                    order=lesson_order,
                    creation_date=timestamp,
                    update_date=timestamp,
                )
            )


async def seed() -> None:
    async with _async_session_factory() as session:
        org = (
            await session.exec(select(Organization).where(Organization.slug == "default"))
        ).first()
        if org is None or org.id is None:
            raise RuntimeError("Default organization does not exist. Start LearnHouse before seeding.")

        roles = {
            role.name: role.id
            for role in (await session.exec(select(Role))).all()
        }
        instructor_role_id = roles.get("Instructor")
        student_role_id = roles.get("User")
        if instructor_role_id is None or student_role_id is None:
            raise RuntimeError("Default Instructor/User roles are missing. Complete LearnHouse auto-install first.")

        instructors = [
            await ensure_user(
                session,
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                role_id=instructor_role_id,
                org_id=org.id,
            )
            for email, username, first_name, last_name in INSTRUCTORS
        ]
        for email, username, first_name, last_name in STUDENTS:
            await ensure_user(
                session,
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                role_id=student_role_id,
                org_id=org.id,
            )
        for spec in COURSES:
            await ensure_course(session, org_id=org.id, instructor=instructors[spec[3]], spec=spec)
        await session.commit()

    print("Mentora development seed is ready: 3 courses, 2 instructors, 3 students.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed local Mentora development data")
    parser.add_argument("--confirm-development", action="store_true")
    args = parser.parse_args()
    if not args.confirm_development:
        parser.error("Refusing to seed without --confirm-development")
    asyncio.run(seed())
