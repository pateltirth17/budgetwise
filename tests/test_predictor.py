from app import app, Transaction, User
from utils.predictor import LSTMPredictor
import pandas as pd
from datetime import datetime, timedelta

def test_predictor():
    with app.app_context():
        # Get first user
        user = User.query.first()
        if not user:
            print("❌ No users found!")
            return
        
        print(f"🧪 Testing predictor for user: {user.username}")
        
        # Get transactions
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        
        transactions = Transaction.query.filter(
            Transaction.user_id == user.id,
            Transaction.transaction_type == 'expense',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).order_by(Transaction.date.asc()).all()
        
        print(f"📊 Found {len(transactions)} transactions")
        
        if len(transactions) < 7:
            print("❌ Not enough transactions for testing")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.date,
            'amount': t.amount
        } for t in transactions])
        
        print(f"📈 Data summary:")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Total spending: ₹{df['amount'].sum():,.2f}")
        print(f"   Average daily: ₹{df['amount'].mean():,.2f}")
        
        # Test predictor
        predictor = LSTMPredictor()
        result = predictor.predict_spending(df, days=30)
        
        if result:
            print(f"\n✅ Prediction successful!")
            print(f"   Method: {result.get('method', 'unknown')}")
            print(f"   Daily average: ₹{result.get('daily_average', 0):,.2f}")
            print(f"   Total predicted (30 days): ₹{result.get('total_predicted', 0):,.2f}")
            print(f"   Confidence: {result.get('confidence', 'unknown')}")
            
            # Show first 7 days of predictions
            predictions = result.get('predictions', [])
            if predictions:
                print(f"\n📅 First 7 days predictions:")
                for i, pred in enumerate(predictions[:7]):
                    future_date = end_date + timedelta(days=i+1)
                    print(f"   {future_date}: ₹{pred:.2f}")
        else:
            print("❌ Prediction failed!")

if __name__ == '__main__':
    test_predictor()