from app import app, Transaction, User
from utils.predictor import LSTMPredictor
import pandas as pd
from datetime import datetime, timedelta

def test_fixed_prediction():
    with app.app_context():
        user = User.query.first()
        if not user:
            print("No users found!")
            return
        
        # Get recent transactions
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        
        transactions = Transaction.query.filter(
            Transaction.user_id == user.id,
            Transaction.transaction_type == 'expense',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).order_by(Transaction.date.asc()).all()
        
        print(f"🧪 Testing with {len(transactions)} transactions")
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.date,
            'amount': float(t.amount)
        } for t in transactions])
        
        print(f"📊 Actual daily average: ₹{df['amount'].mean():.2f}")
        print(f"📊 Actual total: ₹{df['amount'].sum():.2f}")
        
        # Test predictor
        predictor = LSTMPredictor()
        result = predictor.predict_spending(df, days=30)
        
        if result:
            print(f"\n✅ Prediction Results:")
            print(f"   Method: {result.get('method', 'unknown')}")
            print(f"   Daily Average: ₹{result.get('daily_average', 0):,.2f}")
            print(f"   30-Day Total: ₹{result.get('total_predicted', 0):,.2f}")
            print(f"   Confidence: {result.get('confidence', 0):.1f}%")
            
            # Compare with actual
            actual_avg = df['amount'].mean()
            predicted_avg = result.get('daily_average', 0)
            difference_pct = ((predicted_avg - actual_avg) / actual_avg * 100) if actual_avg > 0 else 0
            
            print(f"\n📈 Comparison:")
            print(f"   Actual avg: ₹{actual_avg:.2f}")
            print(f"   Predicted avg: ₹{predicted_avg:.2f}")
            print(f"   Difference: {difference_pct:+.1f}%")
            
            if abs(difference_pct) < 20:
                print("   ✅ Prediction looks reasonable!")
            elif abs(difference_pct) < 50:
                print("   ⚠️ Prediction is somewhat off")
            else:
                print("   ❌ Prediction is way off")
        else:
            print("❌ Prediction failed!")

if __name__ == '__main__':
    test_fixed_prediction()