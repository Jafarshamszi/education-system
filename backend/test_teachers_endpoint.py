#!/usr/bin/env python3
"""
Test script for the teachers endpoint
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.api.teachers import get_teachers
from app.core.database import SessionLocal


async def test_endpoint():
    """Test the teachers endpoint"""
    db = SessionLocal()
    try:
        # Test the get_teachers function
        result = await get_teachers(
            page=1,
            per_page=10,
            search=None,
            organization_id=None,
            active=None,
            db=db
        )

        print('✅ Teachers endpoint executed successfully!')
        print(f'   Total count: {result.count}')
        print(f'   Total pages: {result.total_pages}')
        print(f'   Current page: {result.current_page}')
        print(f'   Results: {len(result.results)}')

        if result.results:
            print('\n📋 Sample teachers:')
            for i, teacher in enumerate(result.results[:3], 1):
                print(f'\n   {i}. ID: {teacher.id}')
                print(f'      Employee Number: {teacher.employee_number}')
                print(f'      Person: {teacher.person.full_name if teacher.person else "N/A"}')
                print(f'      Position: {teacher.position_title or "N/A"}')
                print(f'      Organization: {teacher.organization.name if teacher.organization else "N/A"}')
                print(f'      Active: {teacher.is_active}')

        return True

    except Exception as e:
        print(f'❌ Error testing endpoint: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = asyncio.run(test_endpoint())
    sys.exit(0 if success else 1)
