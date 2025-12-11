#!/usr/bin/env python3
"""
Script to fix all hardcoded 'edu' database connections to use 'lms' database
"""

import os
import re
from pathlib import Path

# Files that need fixing
files_to_fix = [
    "app/api/academic_schedule.py",
    "app/api/class_schedule.py",
    "app/api/curriculum.py",
    "app/api/curriculum_simplified.py",
    "app/api/evaluation_system.py",
    "app/api/student_groups.py",
    "app/api/student_orders.py",
    "app/api/students_comprehensive.py",
]

# Pattern to match
old_pattern = re.compile(r'database\s*=\s*["\']edu["\']')
new_text = 'database=os.getenv("DB_NAME", "lms")'

def fix_file(filepath):
    """Fix database connection in a file"""
    full_path = Path(__file__).parent / filepath

    if not full_path.exists():
        print(f"⚠️  File not found: {filepath}")
        return False

    with open(full_path, 'r') as f:
        content = f.read()

    # Check if file needs import os
    needs_import = 'import os' not in content and old_pattern.search(content)

    # Replace database connection
    new_content = old_pattern.sub(new_text, content)

    # Add import if needed
    if needs_import and new_content != content:
        # Find first import and add after it
        import_pattern = re.compile(r'^(import .+|from .+ import .+)$', re.MULTILINE)
        match = import_pattern.search(new_content)
        if match:
            insert_pos = match.end()
            new_content = new_content[:insert_pos] + '\nimport os' + new_content[insert_pos:]

    if new_content != content:
        with open(full_path, 'w') as f:
            f.write(new_content)
        print(f"✅ Fixed: {filepath}")
        return True
    else:
        print(f"⏭️  No changes needed: {filepath}")
        return False

def main():
    print("=" * 70)
    print("FIXING DATABASE CONNECTIONS")
    print("=" * 70)
    print(f"\nChanging all 'database=\"edu\"' to 'database=os.getenv(\"DB_NAME\", \"lms\")'")
    print()

    fixed_count = 0
    for filepath in files_to_fix:
        if fix_file(filepath):
            fixed_count += 1

    print()
    print("=" * 70)
    print(f"SUMMARY: Fixed {fixed_count} / {len(files_to_fix)} files")
    print("=" * 70)
    print()
    print("✅ All endpoints should now use the LMS database")
    print("🔄 Restart your backend server for changes to take effect")

if __name__ == "__main__":
    main()
