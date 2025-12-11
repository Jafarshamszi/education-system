#!/usr/bin/env python3
"""
Quick script to convert async API endpoints to sync for Python 3.13 compatibility
"""

import os
import re

def fix_file(filepath):
    """Fix a single file to convert from async to sync operations"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace imports
    content = re.sub(r'from sqlalchemy\.ext\.asyncio import AsyncSession', 
                     'from sqlalchemy.orm import Session', content)
    
    # Replace AsyncSession type hints
    content = re.sub(r': AsyncSession = ', ': Session = ', content)
    content = re.sub(r'AsyncSession\b', 'Session', content)
    
    # Remove async from function definitions
    content = re.sub(r'async def ([a-zA-Z_][a-zA-Z0-9_]*)\(', r'def \1(', content)
    
    # Remove await from database operations
    content = re.sub(r'await db\.execute\(', 'db.execute(', content)
    content = re.sub(r'await db\.get\(', 'db.get(', content)
    content = re.sub(r'await db\.merge\(', 'db.merge(', content)
    content = re.sub(r'await db\.delete\(', 'db.delete(', content)
    content = re.sub(r'await db\.commit\(\)', 'db.commit()', content)
    content = re.sub(r'await db\.rollback\(\)', 'db.rollback()', content)
    content = re.sub(r'await db\.refresh\(', 'db.refresh(', content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
    else:
        print(f"No changes needed for {filepath}")

# Fix all API files
api_dir = "app/api"
for filename in os.listdir(api_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        filepath = os.path.join(api_dir, filename)
        fix_file(filepath)