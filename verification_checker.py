# verification_checker.py

from datetime import datetime, timedelta
import pytz

from config import (
    VERIFICATION_ON,
    VERIFICATION_FREE_LIMIT,
    VERIFICATION_RESET_HOUR,
)


def _today_reset_time():
    """
    Return today's reset time (midnight or configured hour) in UTC.
    Adjust here if you want IST explicitly.
    """
    now = datetime.now(pytz.UTC)
    reset = now.replace(
        hour=int(VERIFICATION_RESET_HOUR),
        minute=0,
        second=0,
        microsecond=0,
    )
    # If reset time is in the future, use yesterday's reset
    if reset > now:
        reset = reset - timedelta(days=1)
    return reset


def is_verification_enabled() -> bool:
    """
    Global toggle from config.
    """
    return bool(VERIFICATION_ON)


async def check_user_access(user_id: str, db):
    """
    Core function to check if a user can access a movie.

    Returns a dict:
      {
        "allowed": bool,
        "reason": str,
        "count": int,           # current count after possible increment
        "limit": int,           # free limit
        "need_verification": bool
      }

    Logic:
    - If VERIFICATION_ON is False -> always allowed.
    - If user verified for today -> allowed.
    - If count < free_limit -> increment count, allowed.
    - Else -> blocked, need verification.
    """
    if not VERIFICATION_ON:
        return {
            "allowed": True,
            "reason": "Verification disabled",
            "count": 0,
            "limit": int(VERIFICATION_FREE_LIMIT),
            "need_verification": False,
        }

    now = datetime.now(pytz.UTC)
    reset_time = _today_reset_time()
    limit = int(VERIFICATION_FREE_LIMIT)

    # verif_users collection structure:
    # {
    #   user_id: str,
    #   count: int,
    #   verified: bool,
    #   last_reset: datetime,
    #   last_verified: datetime
    # }

    row = await db.verif_users.find_one({"user_id": str(user_id)})

    if not row:
        # First time user today -> create doc with count=1
        doc = {
            "user_id": str(user_id),
            "count": 1,
            "verified": False,
            "last_reset": reset_time,
            "last_verified": None,
        }
        await db.verif_users.insert_one(doc)
        return {
            "allowed": True,
            "reason": "First visit today",
            "count": 1,
            "limit": limit,
            "need_verification": False,
        }

    # Existing user
    last_reset = row.get("last_reset")
    count = int(row.get("count", 0))
    verified = bool(row.get("verified", False))

    # Reset if last_reset is before today's reset_time
    if not last_reset or last_reset < reset_time:
        count = 0
        verified = False
        await db.verif_users.update_one(
            {"user_id": str(user_id)},
            {
                "$set": {
                    "count": 0,
                    "verified": False,
                    "last_reset": reset_time,
                }
            },
        )

    # If already verified for today, always allow
    if verified:
        return {
            "allowed": True,
            "reason": "Already verified",
            "count": count,
            "limit": limit,
            "need_verification": False,
        }

    # Free quota path
    if count < limit:
        count += 1
        await db.verif_users.update_one(
            {"user_id": str(user_id)},
            {"$set": {"count": count}},
        )
        return {
            "allowed": True,
            "reason": "Within free daily limit",
            "count": count,
            "limit": limit,
            "need_verification": False,
        }

    # Over the limit -> need verification
    return {
        "allowed": False,
        "reason": "Daily limit exceeded, verification required",
        "count": count,
        "limit": limit,
        "need_verification": True,
    }


async def mark_user_verified(user_id: str, db):
    """
    Mark user as verified for today.
    Call this after the user successfully completes the shortlink flow.
    """
    now = datetime.now(pytz.UTC)
    reset_time = _today_reset_time()

    await db.verif_users.update_one(
        {"user_id": str(user_id)},
        {
            "$set": {
                "verified": True,
                "last_verified": now,
                "last_reset": reset_time,
            }
        },
        upsert=True,
    )


async def reset_all_user_limits(db):
    """
    Optional helper if you ever want to run a scheduled global reset.
    In most cases _today_reset_time + per-user logic is enough.
    """
    reset_time = _today_reset_time()
    await db.verif_users.update_many(
        {},
        {
            "$set": {
                "count": 0,
                "verified": False,
                "last_reset": reset_time,
            }
        },
    )

