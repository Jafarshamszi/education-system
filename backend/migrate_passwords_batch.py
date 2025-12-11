#!/usr/bin/env python3
"""
Fast batch migration script to hash all plain text passwords.

This version commits in batches for better performance.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models import User
from app.auth import hash_password
from sqlalchemy import select

def migrate_passwords_batch():
    """Migrate passwords in batches"""

    db = SessionLocal()

    try:
        print("=" * 60)
        print("BATCH PASSWORD MIGRATION")
        print("=" * 60)

        # Find users with plain text passwords
        stmt = select(User).where(~User.password_hash.startswith('$2'))
        result = db.execute(stmt)
        users_to_migrate = result.scalars().all()

        total = len(users_to_migrate)
        print(f"🔓 Users to migrate: {total}")

        if total == 0:
            print("✅ All passwords already hashed")
            return

        response = input(f"\n⚠️  Migrate {total} passwords? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return

        print(f"\n🔄 Migrating {total} passwords in batches...")

        batch_size = 100
        migrated = 0
        errors = 0

        for i in range(0, total, batch_size):
            batch = users_to_migrate[i:i + batch_size]

            for user in batch:
                try:
                    plain = user.password_hash
                    # Truncate if needed (bcrypt 72-byte limit)
                    if len(plain.encode('utf-8')) > 72:
                        plain = plain.encode('utf-8')[:72].decode('utf-8', errors='ignore')

                    user.password_hash = hash_password(plain)
                    migrated += 1
                except Exception as e:
                    errors += 1
                    print(f"  ✗ Error: {user.username}: {e}")

            # Commit batch
            db.commit()
            print(f"  ✓ Processed {min(i + batch_size, total)}/{total} users")

        print(f"\n✅ Migration complete!")
        print(f"   Migrated: {migrated}")
        print(f"   Errors: {errors}")

    except Exception as e:
        db.rollback()
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    migrate_passwords_batch()
