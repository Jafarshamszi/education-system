#!/usr/bin/env python3
"""
Script to identify all files with hardcoded API URLs and database credentials
This helps track which files still need to be updated.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Patterns to search for
PATTERNS = {
    'hardcoded_api_url': r'["\']http://localhost:8000["\']',
    'hardcoded_db_password': r'password\s*=\s*["\']1111["\']',
    'hardcoded_db_user': r'user\s*=\s*["\']postgres["\']',
    'hardcoded_db_name': r'database\s*=\s*["\']lms["\']',
}

# Directories to search
SEARCH_DIRS = [
    'frontend-teacher',
    'frontend-student',
    'frontend/src',
    'backend/app/api',
]

# Files to exclude
EXCLUDE_PATTERNS = [
    '.next',
    'node_modules',
    '__pycache__',
    '.git',
    'dist',
    'build',
    '.env',
    'api-config.ts',  # Our new config files
    'HARDCODED_VALUES_REMOVAL_GUIDE.md',  # Our documentation
]

def should_exclude(file_path):
    """Check if file should be excluded from search"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(file_path):
            return True
    return False

def search_files():
    """Search for hardcoded values in files"""
    results = defaultdict(lambda: defaultdict(list))
    root_dir = Path('/home/axel/Developer/Education-system')
    
    for search_dir in SEARCH_DIRS:
        dir_path = root_dir / search_dir
        if not dir_path.exists():
            continue
            
        # Search for .tsx, .ts, .js, .jsx, .py files
        for ext in ['*.tsx', '*.ts', '*.js', '*.jsx', '*.py']:
            for file_path in dir_path.rglob(ext):
                if should_exclude(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern_name, pattern in PATTERNS.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            # Get line number
                            line_num = content[:match.start()].count('\n') + 1
                            results[pattern_name][str(file_path.relative_to(root_dir))].append(line_num)
                            
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return results

def print_results(results):
    """Print formatted results"""
    print("\n" + "="*80)
    print("HARDCODED VALUES DETECTION REPORT")
    print("="*80)
    
    total_files = set()
    for pattern_name, files in results.items():
        total_files.update(files.keys())
    
    print(f"\nTotal files with hardcoded values: {len(total_files)}\n")
    
    for pattern_name, files in results.items():
        if not files:
            print(f"✅ {pattern_name}: No instances found")
            continue
            
        print(f"\n❌ {pattern_name}: Found in {len(files)} files")
        print("-" * 80)
        
        for file_path, line_numbers in sorted(files.items()):
            print(f"  📄 {file_path}")
            print(f"     Lines: {', '.join(map(str, sorted(line_numbers)))}")
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print("""
1. Frontend API URLs:
   - Use: import { API_ENDPOINTS } from '@/lib/api-config'
   - Replace: 'http://localhost:8000' with API_ENDPOINTS.XXX.XXX

2. Backend Database Credentials:
   - Use: from app.core.config import get_settings
   - Replace: password='1111' with settings.DB_PASSWORD

3. Environment Variables:
   - Ensure .env.local files exist in frontend directories
   - Ensure backend/.env is configured properly
   
See HARDCODED_VALUES_REMOVAL_GUIDE.md for detailed migration instructions.
""")

if __name__ == '__main__':
    results = search_files()
    print_results(results)
