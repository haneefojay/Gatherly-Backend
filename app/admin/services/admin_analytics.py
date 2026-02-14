"""Admin user analytics services"""

from datetime import datetime, timedelta

from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User, UserRole, UserStatus, LoginHistory, TwoFactorAuth


async def get_user_stats(session: AsyncSession) -> dict:
    """Get aggregated user statistics"""

    total_result = await session.execute(select(func.count()).select_from(User))
    total_users = total_result.scalar() or 0

    active_result = await session.execute(
        select(func.count()).select_from(User).where(User.status == UserStatus.ACTIVE)
    )
    active_users = active_result.scalar() or 0

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    new_today_result = await session.execute(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    )
    new_today = new_today_result.scalar() or 0

    new_week_result = await session.execute(
        select(func.count()).select_from(User).where(User.created_at >= week_start)
    )
    new_this_week = new_week_result.scalar() or 0

    new_month_result = await session.execute(
        select(func.count()).select_from(User).where(User.created_at >= month_start)
    )
    new_this_month = new_month_result.scalar() or 0

    role_result = await session.execute(
        select(User.role, func.count()).group_by(User.role)
    )
    by_role = {row[0].value: row[1] for row in role_result.all()}

    status_result = await session.execute(
        select(User.status, func.count()).group_by(User.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}

    verified_result = await session.execute(
        select(func.count()).select_from(User).where(User.email_verified == True)
    )
    verified_count = verified_result.scalar() or 0
    email_verified_rate = (verified_count / total_users * 100) if total_users > 0 else 0

    twofa_result = await session.execute(
        select(func.count(func.distinct(TwoFactorAuth.user_id)))
        .select_from(TwoFactorAuth)
        .where(TwoFactorAuth.enabled == True)
    )
    twofa_count = twofa_result.scalar() or 0
    twofa_adoption_rate = (twofa_count / total_users * 100) if total_users > 0 else 0

    dau_result = await session.execute(
        select(func.count(func.distinct(LoginHistory.user_id)))
        .select_from(LoginHistory)
        .where(LoginHistory.timestamp >= today_start, LoginHistory.success == True)
    )
    dau = dau_result.scalar() or 0

    wau_result = await session.execute(
        select(func.count(func.distinct(LoginHistory.user_id)))
        .select_from(LoginHistory)
        .where(LoginHistory.timestamp >= week_start, LoginHistory.success == True)
    )
    wau = wau_result.scalar() or 0

    mau_result = await session.execute(
        select(func.count(func.distinct(LoginHistory.user_id)))
        .select_from(LoginHistory)
        .where(LoginHistory.timestamp >= month_start, LoginHistory.success == True)
    )
    mau = mau_result.scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "new_today": new_today,
        "new_this_week": new_this_week,
        "new_this_month": new_this_month,
        "by_role": by_role,
        "by_status": by_status,
        "email_verified_rate": round(email_verified_rate, 1),
        "twofa_adoption_rate": round(twofa_adoption_rate, 1),
        "dau": dau,
        "wau": wau,
        "mau": mau,
    }


async def get_user_growth(
    session: AsyncSession,
    days: int = 30,
) -> dict:
    """Get daily user registration counts for growth chart"""

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    result = await session.execute(
        select(
            cast(User.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(User.created_at >= start_date)
        .group_by(cast(User.created_at, Date))
        .order_by(cast(User.created_at, Date))
    )
    daily_counts = {str(row.date): row.count for row in result.all()}

    cumulative_base_result = await session.execute(
        select(func.count()).select_from(User).where(User.created_at < start_date)
    )
    cumulative = cumulative_base_result.scalar() or 0

    data_points = []
    current = start_date.date()
    end = end_date.date()

    while current <= end:
        date_str = str(current)
        count = daily_counts.get(date_str, 0)
        cumulative += count
        data_points.append({
            "date": date_str,
            "count": count,
            "cumulative": cumulative,
        })
        current += timedelta(days=1)

    return {
        "data_points": data_points,
        "period": f"{days}_days",
    }
