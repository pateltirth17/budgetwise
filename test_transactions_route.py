from app import app, Transaction, User
from datetime import datetime, timedelta

def test_transactions_route():
    with app.app_context():
        # Get first user
        user = User.query.first()
        if not user:
            print("No users found!")
            return
        
        print(f"\nTesting transactions for user: {user.username} (ID: {user.id})")
        
        # Query all transactions
        all_transactions = Transaction.query.filter_by(user_id=user.id).all()
        print(f"Total transactions: {len(all_transactions)}")
        
        # Query with date filter (last 30 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        filtered_transactions = Transaction.query.filter(
            Transaction.user_id == user.id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        print(f"Transactions in last 30 days: {len(filtered_transactions)}")
        
        # Calculate statistics
        if filtered_transactions:
            total_spending = sum(t.amount for t in filtered_transactions if t.transaction_type == 'expense')
            total_income = sum(t.amount for t in filtered_transactions if t.transaction_type == 'income')
            
            dates = [t.date for t in filtered_transactions]
            min_date = min(dates)
            max_date = max(dates)
            days_range = (max_date - min_date).days + 1
            avg_per_day = total_spending / days_range if days_range > 0 else 0
            
            print(f"\nStatistics:")
            print(f"  Total Spending: ₹{total_spending:,.2f}")
            print(f"  Total Income: ₹{total_income:,.2f}")
            print(f"  Date Range: {min_date} to {max_date} ({days_range} days)")
            print(f"  Average per day: ₹{avg_per_day:,.2f}")
            
            # Category breakdown
            categories = {}
            for t in filtered_transactions:
                if t.transaction_type == 'expense':
                    if t.category not in categories:
                        categories[t.category] = 0
                    categories[t.category] += t.amount
            
            print(f"\nCategory Breakdown:")
            for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: ₹{amount:,.2f}")

if __name__ == '__main__':
    test_transactions_route()