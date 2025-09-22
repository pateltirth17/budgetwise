"""
Test script to verify BudgetWise AI is working correctly
"""

import os
import sys

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    try:
        import flask
        import pandas
        import numpy
        import sqlalchemy
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database connection"""
    print("\nTesting database...")
    try:
        from app import app, db, User, Transaction
        with app.app_context():
            # Try to query
            users = User.query.all()
            print(f"✅ Database working. Found {len(users)} users")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def create_test_csv():
    """Create a test CSV file"""
    print("\nCreating test CSV...")
    
    csv_content = """Date,Description,Amount
2024-01-15,Swiggy Order,250
2024-01-15,Uber Ride,120
2024-01-16,Amazon Shopping,1500
2024-01-16,Electricity Bill,1200
2024-01-17,BigBasket Groceries,800
2024-01-17,Netflix Subscription,649
2024-01-18,Petrol Pump,2000
2024-01-18,Restaurant Dinner,1200
2024-01-19,Mobile Recharge,599
2024-01-20,Gym Membership,1500"""
    
    os.makedirs('data', exist_ok=True)
    with open('data/test_transactions.csv', 'w') as f:
        f.write(csv_content)
    
    print("✅ Created test_transactions.csv in data folder")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 BudgetWise AI - System Test")
    print("=" * 50)
    
    all_good = True
    
    all_good = test_imports() and all_good
    all_good = test_database() and all_good
    all_good = create_test_csv() and all_good
    
    print("\n" + "=" * 50)
    if all_good:
        print("✅ All tests passed! Your app is ready to use.")
        print("\n📝 Test credentials:")
        print("   Email: test@example.com")
        print("   Password: test123")
        print("\n📁 Test CSV file: data/test_transactions.csv")
    else:
        print("❌ Some tests failed. Please check the errors above.")