"""
Fix database schema issues for BudgetWise AI
This script will backup your data and recreate the database with correct schema
"""

import os
import shutil
from datetime import datetime
import sqlite3
import json

def backup_database():
    """Backup existing database"""
    if os.path.exists('budgetwise.db'):
        backup_name = f'budgetwise_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy('budgetwise.db', backup_name)
        print(f"✅ Database backed up to: {backup_name}")
        return backup_name
    return None

def extract_user_data():
    """Extract existing user data before reset"""
    users_data = []
    
    if os.path.exists('budgetwise.db'):
        try:
            conn = sqlite3.connect('budgetwise.db')
            cursor = conn.cursor()
            
            # Try to get users
            try:
                cursor.execute("SELECT id, username, email, password_hash FROM user")
                users = cursor.fetchall()
                for user in users:
                    users_data.append({
                        'id': user[0],
                        'username': user[1],
                        'email': user[2],
                        'password_hash': user[3]
                    })
                print(f"📊 Found {len(users_data)} users to preserve")
            except:
                print("⚠️ No user data found or table doesn't exist")
            
            conn.close()
        except Exception as e:
            print(f"⚠️ Could not extract data: {e}")
    
    return users_data

def fix_database_schema():
    """Fix the database by adding missing columns"""
    print("\n🔧 Fixing database schema...")
    
    # Step 1: Backup
    backup_file = backup_database()
    
    # Step 2: Extract user data
    users_data = extract_user_data()
    
    # Step 3: Delete old database
    if os.path.exists('budgetwise.db'):
        os.remove('budgetwise.db')
        print("🗑️ Old database removed")
    
    # Step 4: Create new database with correct schema
    from app import app, db, User, Transaction
    
    with app.app_context():
        # Create all tables with new schema
        db.create_all()
        print("✅ New database created with correct schema")
        
        # Step 5: Restore users if any
        if users_data:
            for user_data in users_data:
                user = User(
                    username=user_data['username'],
                    email=user_data['email']
                )
                user.password_hash = user_data['password_hash']
                db.session.add(user)
            
            db.session.commit()
            print(f"✅ Restored {len(users_data)} users")
    
    print("\n✨ Database fixed successfully!")
    print("🚀 You can now run the app: python app.py")

def add_missing_column():
    """Alternative: Just add the missing column without data loss"""
    print("\n🔧 Adding missing column to existing database...")
    
    if not os.path.exists('budgetwise.db'):
        print("❌ Database doesn't exist. Run the app first.")
        return
    
    try:
        conn = sqlite3.connect('budgetwise.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(transaction)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'transaction_type' not in columns:
            # Add the missing column
            cursor.execute("""
                ALTER TABLE transaction 
                ADD COLUMN transaction_type VARCHAR(20) DEFAULT 'expense'
            """)
            conn.commit()
            print("✅ Added 'transaction_type' column to transaction table")
        else:
            print("ℹ️ Column 'transaction_type' already exists")
        
        conn.close()
        print("\n✨ Database fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🏦 BudgetWise AI - Database Fix Tool")
    print("=" * 50)
    
    print("\nChoose fix method:")
    print("1. Quick Fix - Add missing column (keeps data)")
    print("2. Full Reset - Recreate database (fresh start)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        add_missing_column()
    elif choice == '2':
        confirm = input("\n⚠️ This will reset your database. Continue? (yes/no): ").strip().lower()
        if confirm == 'yes':
            fix_database_schema()
        else:
            print("❌ Cancelled")
    else:
        print("👋 Goodbye!")