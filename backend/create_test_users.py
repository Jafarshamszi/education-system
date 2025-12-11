#!/usr/bin/env python3
"""
Create test users for the Education Management System
"""

import sys
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Add the app directory to Python path
backend_dir = Path(__file__).parent
app_dir = backend_dir / "app"
sys.path.insert(0, str(backend_dir))

from app.core.database import sync_engine
from app.models import Person, Account, User
from app.auth import hash_password


def create_test_users():
    """Create test users for development"""
    
    # Create a database session
    SessionLocal = sessionmaker(bind=sync_engine)
    session = SessionLocal()
    
    try:
        print("🔄 Creating test users...")
        
        # Get the next ID by finding the max ID + 1
        from sqlalchemy import text
        result = session.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM persons"))
        next_person_id = result.scalar()
        
        result = session.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM accounts"))
        next_account_id = result.scalar()
        
        result = session.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM users"))
        next_user_id = result.scalar()
        
        # Test users data
        users_data = [
            {
                "username": "admin",
                "password": "admin123",
                "email": "admin@edu.com",
                "firstname": "Admin",
                "lastname": "User",
                "user_type": "admin"
            },
            {
                "username": "teacher1",
                "password": "teacher123",
                "email": "teacher@edu.com",
                "firstname": "John",
                "lastname": "Teacher",
                "user_type": "teacher"
            },
            {
                "username": "student1",
                "password": "student123",
                "email": "student@edu.com",
                "firstname": "Jane",
                "lastname": "Student",
                "user_type": "student"
            }
        ]
        
        for i, user_data in enumerate(users_data):
            # Check if user already exists
            existing_account = session.query(Account).filter(
                Account.username == user_data["username"]
            ).first()
            
            if existing_account:
                print(f"⚠️  User {user_data['username']} exists, skipping...")
                continue
            
            # Create Person with manual ID
            person = Person(
                id=next_person_id + i,
                firstname=user_data["firstname"],
                lastname=user_data["lastname"],
                active=1,
                create_date=datetime.utcnow(),
                update_date=datetime.utcnow()
            )
            session.add(person)
            session.flush()  # Get the ID
            
            # Create Account with manual ID
            hashed_password = hash_password(user_data["password"])
            account = Account(
                id=next_account_id + i,
                username=user_data["username"],
                email=user_data["email"],
                password=hashed_password,
                person_id=person.id,
                active=1,
                create_date=datetime.utcnow(),
                update_date=datetime.utcnow()
            )
            session.add(account)
            session.flush()  # Get the ID
            
            # Create User with manual ID
            user = User(
                id=next_user_id + i,
                user_type=user_data["user_type"],
                account_id=account.id,
                active=1,
                is_blocked=0,
                create_date=datetime.utcnow(),
                update_date=datetime.utcnow()
            )
            session.add(user)
            session.flush()  # Get the ID
            
            # Update account with default_user_id
            account.default_user_id = user.id
            
            print(f"✅ Created user: {user_data['username']} "
                  f"({user_data['user_type']})")
        
        # Commit all changes
        session.commit()
        print("🎉 Test users created successfully!")
        
        # Print login credentials
        print("\n📋 Test Credentials:")
        print("==================")
        for user_data in users_data:
            print(f"Username: {user_data['username']}")
            print(f"Password: {user_data['password']}")
            print(f"Role: {user_data['user_type']}")
            print("---")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating test users: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    create_test_users()