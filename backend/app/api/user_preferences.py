"""
User Preferences API endpoints
"""

import os
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings
from app.auth import get_current_user, CurrentUser

router = APIRouter(prefix="/user-preferences", tags=["user-preferences"])


def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=RealDictCursor
    )


class UserPreferences(BaseModel):
    """User preferences model"""
    language: str = "az"
    timezone: str = "Asia/Baku"
    theme: str = "light"
    notifications_enabled: bool = True
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True


class LanguageUpdate(BaseModel):
    """Language update model"""
    language: str


@router.get("/")
def get_user_preferences(
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's preferences

    Returns:
        User preferences object
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get user preferences
        cur.execute("""
            SELECT
                language,
                timezone,
                theme,
                notifications_enabled,
                email_notifications,
                sms_notifications,
                push_notifications,
                preferences
            FROM user_preferences
            WHERE user_id = %s
        """, (current_user.id,))

        result = cur.fetchone()

        if not result:
            # Create default preferences if they don't exist
            cur.execute("""
                INSERT INTO user_preferences (user_id, language, timezone, theme)
                VALUES (%s, 'az', 'Asia/Baku', 'light')
                RETURNING
                    language,
                    timezone,
                    theme,
                    notifications_enabled,
                    email_notifications,
                    sms_notifications,
                    push_notifications,
                    preferences
            """, (current_user.id,))
            result = cur.fetchone()
            conn.commit()

        return dict(result)

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cur.close()
        conn.close()


@router.put("/language")
def update_language(
    language_data: LanguageUpdate,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update user's language preference

    Args:
        language_data: Language preference data

    Returns:
        Success message with updated language
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Validate language
        if language_data.language not in ['en', 'ru', 'az']:
            raise HTTPException(
                status_code=400,
                detail="Invalid language. Must be one of: en, ru, az"
            )

        # Check if preferences exist
        cur.execute("""
            SELECT id FROM user_preferences WHERE user_id = %s
        """, (current_user.id,))

        exists = cur.fetchone()

        if exists:
            # Update existing preferences
            cur.execute("""
                UPDATE user_preferences
                SET language = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                RETURNING language
            """, (language_data.language, current_user.id))
        else:
            # Create new preferences
            cur.execute("""
                INSERT INTO user_preferences (user_id, language)
                VALUES (%s, %s)
                RETURNING language
            """, (current_user.id, language_data.language))

        result = cur.fetchone()
        conn.commit()

        return {
            "message": "Language preference updated successfully",
            "language": result['language']
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cur.close()
        conn.close()


@router.put("/")
def update_user_preferences(
    preferences: UserPreferences,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update user's preferences

    Args:
        preferences: User preferences data

    Returns:
        Updated preferences
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Validate language
        if preferences.language not in ['en', 'ru', 'az']:
            raise HTTPException(
                status_code=400,
                detail="Invalid language. Must be one of: en, ru, az"
            )

        # Validate theme
        if preferences.theme not in ['light', 'dark', 'auto']:
            raise HTTPException(
                status_code=400,
                detail="Invalid theme. Must be one of: light, dark, auto"
            )

        # Check if preferences exist
        cur.execute("""
            SELECT id FROM user_preferences WHERE user_id = %s
        """, (current_user.id,))

        exists = cur.fetchone()

        if exists:
            # Update existing preferences
            cur.execute("""
                UPDATE user_preferences
                SET
                    language = %s,
                    timezone = %s,
                    theme = %s,
                    notifications_enabled = %s,
                    email_notifications = %s,
                    sms_notifications = %s,
                    push_notifications = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                RETURNING
                    language,
                    timezone,
                    theme,
                    notifications_enabled,
                    email_notifications,
                    sms_notifications,
                    push_notifications
            """, (
                preferences.language,
                preferences.timezone,
                preferences.theme,
                preferences.notifications_enabled,
                preferences.email_notifications,
                preferences.sms_notifications,
                preferences.push_notifications,
                current_user.id
            ))
        else:
            # Create new preferences
            cur.execute("""
                INSERT INTO user_preferences (
                    user_id,
                    language,
                    timezone,
                    theme,
                    notifications_enabled,
                    email_notifications,
                    sms_notifications,
                    push_notifications
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    language,
                    timezone,
                    theme,
                    notifications_enabled,
                    email_notifications,
                    sms_notifications,
                    push_notifications
            """, (
                current_user.id,
                preferences.language,
                preferences.timezone,
                preferences.theme,
                preferences.notifications_enabled,
                preferences.email_notifications,
                preferences.sms_notifications,
                preferences.push_notifications
            ))

        result = cur.fetchone()
        conn.commit()

        return dict(result)

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cur.close()
        conn.close()
