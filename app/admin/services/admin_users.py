"""Admin user management services"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, delete, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.attendees.models import Attendee, AttendeeStatus
from app.common.exceptions import NotFoundException, ValidationException, ForbiddenException
from app.events.models import Event, EventStatus, event_organizers
from app.social.models import Review, SavedEvent
from app.users.models import (
    User, UserProfile, UserRole, UserStatus,
    LoginHistory, UserSession, RefreshToken, TwoFactorAuth,
)
from app.admin.models import AdminAuditLog, AdminNote, ImpersonationSession
from app.admin.services import log_admin_action


async def list_users(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    role: Optional[str] = None,
    status: Optional[str] = None,
    email_verified: Optional[bool] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    last_login_after: Optional[datetime] = None,
    last_login_before: Optional[datetime] = None,
    location: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[User], int]:
    """List users with advanced filtering, search, and pagination"""

    query = select(User).options(selectinload(User.profile))

    if role:
        query = query.where(User.role == UserRole(role))
    if status:
        query = query.where(User.status == UserStatus(status))
    if email_verified is not None:
        query = query.where(User.email_verified == email_verified)
    if date_from:
        query = query.where(User.created_at >= date_from)
    if date_to:
        query = query.where(User.created_at <= date_to)
    if last_login_after:
        query = query.where(User.last_login_at >= last_login_after)
    if last_login_before:
        query = query.where(User.last_login_at <= last_login_before)
    if location:
        query = query.join(UserProfile, User.id == UserProfile.user_id).where(
            UserProfile.location.ilike(f"%{location}%")
        )
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term),
                User.full_name.ilike(search_term),
            )
        )

    count_result = await session.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    users = result.scalars().all()

    return users, total


async def get_user_detail(session: AsyncSession, user_id: uuid.UUID) -> dict:
    """Get complete user detail with all related data"""

    result = await session.execute(
        select(User)
        .options(selectinload(User.profile), selectinload(User.preferences))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    twofa_result = await session.execute(
        select(TwoFactorAuth).where(
            TwoFactorAuth.user_id == user_id,
            TwoFactorAuth.enabled == True,
        )
    )
    has_2fa = twofa_result.scalar_one_or_none() is not None

    login_result = await session.execute(
        select(LoginHistory)
        .where(LoginHistory.user_id == user_id)
        .order_by(LoginHistory.timestamp.desc())
        .limit(50)
    )
    login_history = [
        {
            "ip_address": lh.ip_address,
            "user_agent": lh.user_agent,
            "location": lh.location,
            "success": lh.success,
            "failure_reason": lh.failure_reason,
            "timestamp": lh.timestamp.isoformat(),
        }
        for lh in login_result.scalars().all()
    ]

    sessions_result = await session.execute(
        select(UserSession)
        .where(UserSession.user_id == user_id, UserSession.expires_at > datetime.utcnow())
        .order_by(UserSession.last_active_at.desc())
    )
    active_sessions = [
        {
            "id": str(s.id),
            "device_info": s.device_info,
            "ip_address": s.ip_address,
            "last_active_at": s.last_active_at.isoformat(),
            "expires_at": s.expires_at.isoformat(),
        }
        for s in sessions_result.scalars().all()
    ]

    created_events_result = await session.execute(
        select(Event)
        .where(Event.created_by_id == user_id)
        .order_by(Event.created_at.desc())
        .limit(20)
    )
    created_events = [
        {
            "id": str(e.id),
            "title": e.title,
            "status": e.status.value if e.status else None,
            "start_date": e.start_date.isoformat() if e.start_date else None,
            "created_at": e.created_at.isoformat(),
        }
        for e in created_events_result.scalars().all()
    ]

    attended_result = await session.execute(
        select(Attendee, Event)
        .join(Event, Attendee.event_id == Event.id)
        .where(
            Attendee.user_id == user_id,
            Attendee.status.in_([AttendeeStatus.REGISTERED, AttendeeStatus.CHECKED_IN]),
        )
        .order_by(Attendee.registered_at.desc())
        .limit(20)
    )
    attended_events = [
        {
            "event_id": str(event.id),
            "title": event.title,
            "status": attendee.status.value,
            "registered_at": attendee.registered_at.isoformat(),
        }
        for attendee, event in attended_result.all()
    ]

    reviews_given_result = await session.execute(
        select(Review, Event)
        .join(Event, Review.event_id == Event.id)
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .limit(20)
    )
    reviews_given = [
        {
            "event_title": event.title,
            "rating": review.rating,
            "content": review.content[:100],
            "created_at": review.created_at.isoformat(),
        }
        for review, event in reviews_given_result.all()
    ]

    reviews_received_result = await session.execute(
        select(Review, Event)
        .join(Event, Review.event_id == Event.id)
        .join(event_organizers, event_organizers.c.event_id == Event.id)
        .where(event_organizers.c.user_id == user_id)
        .order_by(Review.created_at.desc())
        .limit(20)
    )
    reviews_received = [
        {
            "event_title": event.title,
            "rating": review.rating,
            "content": review.content[:100],
            "created_at": review.created_at.isoformat(),
        }
        for review, event in reviews_received_result.all()
    ]

    notes_result = await session.execute(
        select(AdminNote, User)
        .join(User, AdminNote.admin_id == User.id)
        .where(AdminNote.user_id == user_id)
        .order_by(AdminNote.created_at.desc())
    )
    admin_notes = [
        {
            "id": str(note.id),
            "admin_email": admin.email,
            "content": note.content,
            "created_at": note.created_at.isoformat(),
        }
        for note, admin in notes_result.all()
    ]

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "status": user.status.value,
        "email_verified": user.email_verified,
        "is_active": user.is_active,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "bio": user.bio,
        "phone": user.phone if user.profile else None,
        "location": user.location,
        "avatar_url": user.avatar_url,
        "cover_photo_url": user.cover_photo_url,
        "social_links": user.social_links,
        "has_2fa": has_2fa,
        "login_history": login_history,
        "active_sessions": active_sessions,
        "created_events": created_events,
        "attended_events": attended_events,
        "reviews_given": reviews_given,
        "reviews_received": reviews_received,
        "admin_notes": admin_notes,
    }


async def update_user(
    session: AsyncSession,
    admin: User,
    user_id: uuid.UUID,
    update_data: dict,
) -> User:
    """Update user information with audit logging"""

    result = await session.execute(
        select(User).options(selectinload(User.profile)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    before_state = {
        "full_name": user.full_name,
        "email": user.email,
        "username": user.username,
        "role": user.role.value,
        "email_verified": user.email_verified,
    }

    if "username" in update_data and update_data["username"]:
        existing = await session.execute(
            select(User).where(
                User.username == update_data["username"],
                User.id != user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationException("Username already taken")

    if "email" in update_data and update_data["email"]:
        existing = await session.execute(
            select(User).where(
                User.email == update_data["email"],
                User.id != user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationException("Email already taken")

    for field, value in update_data.items():
        if value is not None:
            if field == "role":
                setattr(user, field, UserRole(value))
            else:
                setattr(user, field, value)

    after_state = {
        "full_name": user.full_name,
        "email": user.email,
        "username": user.username,
        "role": user.role.value,
        "email_verified": user.email_verified,
    }

    await log_admin_action(
        session,
        admin_id=admin.id,
        action="update_user",
        resource_type="user",
        resource_id=str(user_id),
        before_state=before_state,
        after_state=after_state,
        changes={k: {"from": before_state.get(k), "to": after_state.get(k)}
                 for k in update_data if before_state.get(k) != after_state.get(k)},
    )

    await session.commit()
    await session.refresh(user)
    return user


async def invalidate_user_sessions(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Invalidate all sessions and refresh tokens for a user"""

    sessions_result = await session.execute(
        delete(UserSession).where(UserSession.user_id == user_id)
    )
    tokens_result = await session.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
        )
    )

    return (sessions_result.rowcount or 0) + (tokens_result.rowcount or 0)


async def suspend_user(
    session: AsyncSession,
    admin: User,
    user_id: uuid.UUID,
    reason: str,
    duration_days: Optional[int] = None,
) -> User:
    """Suspend a user account"""

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    if user.role == UserRole.ADMIN:
        raise ForbiddenException("Cannot suspend an admin user")

    before_status = user.status.value
    user.status = UserStatus.SUSPENDED
    user.is_active = False

    await invalidate_user_sessions(session, user_id)

    await log_admin_action(
        session,
        admin_id=admin.id,
        action="suspend_user",
        resource_type="user",
        resource_id=str(user_id),
        before_state={"status": before_status},
        after_state={"status": "suspended"},
        changes={
            "reason": reason,
            "duration_days": duration_days,
            "permanent": duration_days is None,
        },
    )

    await session.commit()
    await session.refresh(user)
    return user


async def ban_user(
    session: AsyncSession,
    admin: User,
    user_id: uuid.UUID,
    reason: str,
) -> User:
    """Ban a user account permanently"""

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    if user.role == UserRole.ADMIN:
        raise ForbiddenException("Cannot ban an admin user")

    before_status = user.status.value
    user.status = UserStatus.BANNED
    user.is_active = False

    await invalidate_user_sessions(session, user_id)

    await log_admin_action(
        session,
        admin_id=admin.id,
        action="ban_user",
        resource_type="user",
        resource_id=str(user_id),
        before_state={"status": before_status},
        after_state={"status": "banned"},
        changes={"reason": reason},
    )

    await session.commit()
    await session.refresh(user)
    return user


async def unsuspend_user(
    session: AsyncSession,
    admin: User,
    user_id: uuid.UUID,
) -> User:
    """Restore a suspended or banned user"""

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    if user.status not in (UserStatus.SUSPENDED, UserStatus.BANNED):
        raise ValidationException("User is not suspended or banned")

    before_status = user.status.value
    user.status = UserStatus.ACTIVE
    user.is_active = True

    await log_admin_action(
        session,
        admin_id=admin.id,
        action="unsuspend_user",
        resource_type="user",
        resource_id=str(user_id),
        before_state={"status": before_status},
        after_state={"status": "active"},
    )

    await session.commit()
    await session.refresh(user)
    return user


async def verify_user(
    session: AsyncSession,
    admin: User,
    user_id: uuid.UUID,
) -> User:
    """Manually verify a user's email"""

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    user.email_verified = True

    await log_admin_action(
        session,
        admin_id=admin.id,
        action="verify_user",
        resource_type="user",
        resource_id=str(user_id),
        before_state={"email_verified": False},
        after_state={"email_verified": True},
    )

    await session.commit()
    await session.refresh(user)
    return user


async def soft_delete_user(
    session: AsyncSession,
    admin: User,
    user_id: uuid.UUID,
) -> None:
    """Soft delete user (GDPR compliant — anonymize PII)"""

    result = await session.execute(
        select(User).options(selectinload(User.profile)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    if user.role == UserRole.ADMIN:
        raise ForbiddenException("Cannot delete an admin user")

    await invalidate_user_sessions(session, user_id)

    before_state = {
        "email": user.email,
        "full_name": user.full_name,
        "username": user.username,
        "status": user.status.value,
    }

    anon_id = str(uuid.uuid4())[:8]
    user.email = f"deleted_{anon_id}@deleted.local"
    user.full_name = "Deleted User"
    user.username = f"deleted_{anon_id}"
    user.hashed_password = "DELETED"
    user.status = UserStatus.DELETED
    user.is_active = False
    user.email_verified = False

    if user.profile:
        user.profile.bio = None
        user.profile.phone = None
        user.profile.location = None
        user.profile.avatar_url = None
        user.profile.cover_photo_url = None
        user.profile.social_links = None

    await log_admin_action(
        session,
        admin_id=admin.id,
        action="delete_user",
        resource_type="user",
        resource_id=str(user_id),
        before_state=before_state,
        after_state={"status": "deleted", "anonymized": True},
    )

    await session.commit()


async def export_user_data(session: AsyncSession, user_id: uuid.UUID) -> dict:
    """Export all user data (GDPR data portability)"""

    result = await session.execute(
        select(User).options(selectinload(User.profile)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    events_result = await session.execute(
        select(Event).where(Event.created_by_id == user_id)
    )
    events = [
        {"id": str(e.id), "title": e.title, "status": e.status.value if e.status else None,
         "created_at": e.created_at.isoformat()}
        for e in events_result.scalars().all()
    ]

    attendees_result = await session.execute(
        select(Attendee, Event)
        .join(Event, Attendee.event_id == Event.id)
        .where(Attendee.user_id == user_id)
    )
    registrations = [
        {"event_title": event.title, "status": att.status.value,
         "registered_at": att.registered_at.isoformat()}
        for att, event in attendees_result.all()
    ]

    reviews_result = await session.execute(
        select(Review, Event)
        .join(Event, Review.event_id == Event.id)
        .where(Review.user_id == user_id)
    )
    reviews = [
        {"event_title": event.title, "rating": r.rating, "content": r.content,
         "created_at": r.created_at.isoformat()}
        for r, event in reviews_result.all()
    ]

    login_result = await session.execute(
        select(LoginHistory).where(LoginHistory.user_id == user_id)
        .order_by(LoginHistory.timestamp.desc())
    )
    logins = [
        {"ip_address": lh.ip_address, "success": lh.success,
         "timestamp": lh.timestamp.isoformat()}
        for lh in login_result.scalars().all()
    ]

    return {
        "profile": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "bio": user.bio,
            "phone": user.phone if user.profile else None,
            "location": user.location,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat(),
        },
        "events_created": events,
        "event_registrations": registrations,
        "reviews": reviews,
        "login_history": logins,
        "exported_at": datetime.utcnow().isoformat(),
    }


async def admin_reset_password(
    session: AsyncSession,
    admin: User,
    user_id: uuid.UUID,
) -> str:
    """Generate password reset token for a user (admin-initiated)"""

    from app.users.models import PasswordResetToken

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    session.add(reset_token)

    await log_admin_action(
        session,
        admin_id=admin.id,
        action="reset_password",
        resource_type="user",
        resource_id=str(user_id),
    )

    await session.commit()
    return token


async def create_impersonation(
    session: AsyncSession,
    admin: User,
    user_id: uuid.UUID,
) -> dict:
    """Create a time-limited impersonation session"""

    from app.users.services.users import create_access_token

    result = await session.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise NotFoundException("User not found")

    if target_user.role == UserRole.ADMIN:
        raise ForbiddenException("Cannot impersonate an admin user")

    session_token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(minutes=30)

    impersonation = ImpersonationSession(
        admin_id=admin.id,
        target_user_id=user_id,
        session_token=session_token,
        expires_at=expires_at,
    )
    session.add(impersonation)

    access_token = await create_access_token(target_user)

    await log_admin_action(
        session,
        admin_id=admin.id,
        action="impersonate_user",
        resource_type="user",
        resource_id=str(user_id),
        changes={
            "target_email": target_user.email,
            "expires_at": expires_at.isoformat(),
        },
    )

    await session.commit()

    return {
        "access_token": access_token,
        "target_user_id": str(user_id),
        "target_email": target_user.email,
        "expires_at": expires_at.isoformat(),
        "session_id": str(impersonation.id),
    }


async def add_admin_note(
    session: AsyncSession,
    admin: User,
    user_id: uuid.UUID,
    content: str,
) -> AdminNote:
    """Add an admin note to a user account"""

    result = await session.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise NotFoundException("User not found")

    note = AdminNote(
        admin_id=admin.id,
        user_id=user_id,
        content=content,
    )
    session.add(note)

    await log_admin_action(
        session,
        admin_id=admin.id,
        action="add_note",
        resource_type="user",
        resource_id=str(user_id),
    )

    await session.commit()
    await session.refresh(note)
    return note
