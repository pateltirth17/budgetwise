from app import app, db, Transaction, User
from datetime import datetime, timedelta
import random

def check_and_populate_database():
    with app.app_context():
        print("=" * 50)
        print("DATABASE CHECK AND POPULATE")
        print("=" * 50)
        
        # Check users
        users = User.query.all()
        print(f"\n📊 Total users in database: {len(users)}")
        
        if not users:
            print("❌ No users found! Please create a user account first.")
            return
        
        for user in users:
            print(f"\n👤 User: {user.username} (ID: {user.id}, Email: {user.email})")
            
            # Check existing transactions
            existing_transactions = Transaction.query.filter_by(user_id=user.id).count()
            print(f"   Current transactions: {existing_transactions}")
            
            if existing_transactions == 0:
                print(f"   ⚠️ No transactions found for {user.username}")
                
                # Ask to add test data
                add_test = input(f"\n   Add test transactions for {user.username}? (y/n): ").lower()
                
                if add_test == 'y':
                    # Categories and descriptions
                    expense_data = {
                        'Food & Dining': [
                            ('Swiggy Order', 250, 450),
                            ('Zomato Lunch', 150, 350),
                            ('Coffee at Starbucks', 150, 250),
                            ('Dinner at Restaurant', 500, 1200),
                            ('Breakfast', 50, 150)
                        ],
                        'Transportation': [
                            ('Uber Ride', 100, 300),
                            ('Petrol', 500, 1000),
                            ('Metro Card Recharge', 200, 500),
                            ('Ola Cab', 150, 400)
                        ],
                        'Shopping': [
                            ('Amazon Purchase', 500, 2000),
                            ('Flipkart Shopping', 300, 1500),
                            ('Clothes Shopping', 1000, 3000),
                            ('Grocery Shopping', 500, 1500)
                        ],
                        'Entertainment': [
                            ('Netflix Subscription', 199, 199),
                            ('Movie Tickets', 300, 600),
                            ('Spotify Premium', 119, 119)
                        ],
                        'Utilities': [
                            ('Electricity Bill', 1000, 2000),
                            ('Internet Bill', 800, 1200),
                            ('Mobile Recharge', 299, 599),
                            ('Water Bill', 200, 400)
                        ],
                        'Healthcare': [
                            ('Doctor Consultation', 500, 1000),
                            ('Medicine', 200, 800),
                            ('Gym Membership', 1500, 2000)
                        ]
                    }
                    
                    income_data = [
                        ('Salary', 50000, 80000),
                        ('Freelance Work', 5000, 15000),
                        ('Cashback', 50, 200),
                        ('Refund', 100, 500)
                    ]
                    
                    transactions_added = 0
                    
                    # Add transactions for the last 60 days
                    for days_ago in range(60):
                        date = (datetime.now() - timedelta(days=days_ago)).date()
                        
                        # Add 1-3 expense transactions per day
                        num_expenses = random.randint(1, 3)
                        for _ in range(num_expenses):
                            category = random.choice(list(expense_data.keys()))
                            desc, min_amt, max_amt = random.choice(expense_data[category])
                            
                            transaction = Transaction(
                                user_id=user.id,
                                date=date,
                                description=f"{desc} - {date.strftime('%d %b')}",
                                amount=round(random.uniform(min_amt, max_amt), 2),
                                category=category,
                                transaction_type='expense'
                            )
                            db.session.add(transaction)
                            transactions_added += 1
                        
                        # Add income occasionally (every 15 days for salary, random for others)
                        if days_ago % 30 == 0:  # Monthly salary
                            desc, min_amt, max_amt = income_data[0]  # Salary
                            transaction = Transaction(
                                user_id=user.id,
                                date=date,
                                description=desc,
                                amount=random.uniform(min_amt, max_amt),
                                category='Income',
                                transaction_type='income'
                            )
                            db.session.add(transaction)
                            transactions_added += 1
                        elif random.random() > 0.9:  # 10% chance of other income
                            desc, min_amt, max_amt = random.choice(income_data[1:])
                            transaction = Transaction(
                                user_id=user.id,
                                date=date,
                                description=desc,
                                amount=round(random.uniform(min_amt, max_amt), 2),
                                category='Income',
                                transaction_type='income'
                            )
                            db.session.add(transaction)
                            transactions_added += 1
                    
                    db.session.commit()
                    print(f"   ✅ Added {transactions_added} test transactions for {user.username}")
            else:
                print(f"   ✅ User has {existing_transactions} transactions")
                
                # Show sample transactions
                sample_transactions = Transaction.query.filter_by(user_id=user.id).limit(5).all()
                print("\n   Sample transactions:")
                for t in sample_transactions:
                    print(f"      - {t.date}: {t.description[:30]} - ₹{t.amount} ({t.transaction_type})")
        
        print("\n" + "=" * 50)
        print("DATABASE CHECK COMPLETE")
        print("=" * 50)

if __name__ == '__main__':
    check_and_populate_database()