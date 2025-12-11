#!/usr/bin/env python3
"""
Migration script to hash all plain text passwords in the users table.

This script:
1. Finds all users with plain text passwords (not starting with $2)
2. Hashes each password using bcrypt
3. Updates the password_hash column with the hashed version
4. Provides progress tracking and summary

Run with: python migrate_passwords_to_hash.py
"""

import sys
from pathlib import Path

# Add backend to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models import User
from app.auth import hash_password
from sqlalchemy import select, text


def migrate_passwords():
    """Migrate all plain text passwords to hashed passwords"""

    db = SessionLocal()

    try:
        print("=" * 60)
        print("PASSWORD MIGRATION SCRIPT")
        print("=" * 60)
        print()

        # Count total users
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        total_users = result.scalar()
        print(f"📊 Total users in database: {total_users}")

        # Find users with plain text passwords (not hashed)
        # Bcrypt hashes always start with $2a$ or $2b$
        stmt = select(User).where(~User.password_hash.startswith('$2'))
        result = db.execute(stmt)
        users_to_migrate = result.scalars().all()

        plain_text_count = len(users_to_migrate)
        print(f"🔓 Users with plain text passwords: {plain_text_count}")

        if plain_text_count == 0:
            print("✅ All passwords are already hashed. No migration needed.")
            return

        # Confirm migration
        print()
        response = input(f"⚠️  Migrate {plain_text_count} passwords to bcrypt hashes? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Migration cancelled.")
            return

        print()
        print(f"🔄 Starting migration of {plain_text_count} passwords...")
        print()

        # Migrate passwords
        migrated_count = 0
        error_count = 0

        for i, user in enumerate(users_to_migrate, 1):
            try:
                # Store the original plain text password
                plain_password = user.password_hash

                # Bcrypt has a 72-byte limit - truncate if necessary
                # Convert to bytes, truncate, then back to string
                if len(plain_password.encode('utf-8')) > 72:
                    plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')

                # Hash the password
                hashed_password = hash_password(plain_password)

                # Update the user's password
                user.password_hash = hashed_password

                # Show progress every 500 users
                if i % 500 == 0:
                    print(f"  ✓ Processed {i}/{plain_text_count} users...")

                migrated_count += 1

            except Exception as e:
                error_count += 1
                print(f"  ✗ Error migrating user {user.username}: {e}")

        # Commit all changes
        db.commit()

        # Summary
        print()
        print("=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print(f"✅ Successfully migrated: {migrated_count} passwords")
        if error_count > 0:
            print(f"❌ Errors encountered: {error_count} passwords")
        print(f"📊 Total users: {total_users}")
        print(f"🔒 Users with hashed passwords: {migrated_count}")

        # Verify migration
        print()
        print("Verifying migration...")
        result = db.execute(text("SELECT COUNT(*) FROM users WHERE password_hash LIKE '$2%'"))
        hashed_count = result.scalar()
        print(f"✓ Verified {hashed_count} users have bcrypt hashed passwords")

        # Show sample of migrated passwords
        print()
        print("Sample of migrated password hashes:")
        stmt = select(User).where(User.password_hash.startswith('$2')).limit(3)
        result = db.execute(stmt)
        sample_users = result.scalars().all()
        for user in sample_users:
            hash_preview = user.password_hash[:50] + "..." if len(user.password_hash) > 50 else user.password_hash
            print(f"  - {user.username}: {hash_preview}")

    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    migrate_passwords()
