"""
Script to train the initial LSTM model for BudgetWise AI
Run this once to create the model file
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

print("🚀 BudgetWise AI - Model Training Script")
print("=" * 50)

# Import model trainer
from utils.model_trainer import ModelTrainer

def generate_sample_data(days=365):
    """Generate sample transaction data for training"""
    print("📊 Generating sample training data...")
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Create realistic spending patterns
    base_spending = 2000
    weekly_pattern = np.array([1.2, 0.9, 0.8, 0.9, 1.3, 1.5, 1.4])  # Higher on weekends
    monthly_pattern = np.array([1.1, 0.9, 0.8, 1.2])  # Higher at month start/end
    
    amounts = []
    for i, date in enumerate(dates):
        # Apply patterns
        day_of_week = date.dayofweek
        week_of_month = (date.day - 1) // 7
        
        amount = base_spending
        amount *= weekly_pattern[day_of_week]
        amount *= monthly_pattern[min(week_of_month, 3)]
        
        # Add some randomness
        amount += np.random.normal(0, 300)
        amount = max(100, amount)  # Minimum spending
        
        amounts.append(amount)
    
    df = pd.DataFrame({
        'date': dates,
        'amount': amounts
    })
    
    print(f"✅ Generated {len(df)} days of transaction data")
    return df

def train_lstm_model():
    """Train the LSTM model"""
    print("\n🤖 Starting LSTM Model Training...")
    print("-" * 50)
    
    # Generate training data
    df = generate_sample_data(days=365)
    
    # Initialize trainer
    trainer = ModelTrainer(sequence_length=30)
    
    # Train model
    print("\n📈 Training model (this may take a few minutes)...")
    history = trainer.train(df, epochs=50, batch_size=32)
    
    # Save model
    model_path = 'models/lstm_model.h5'
    trainer.save_model(model_path)
    
    print("\n✅ Model training complete!")
    print(f"📁 Model saved to: {model_path}")
    
    # Evaluate model
    print("\n📊 Model Performance:")
    print(f"Final Loss: {history.history['loss'][-1]:.4f}")
    print(f"Final MAE: {history.history['mae'][-1]:.4f}")
    
    return trainer

def test_predictions():
    """Test the trained model with predictions"""
    print("\n🔮 Testing Predictions...")
    print("-" * 50)
    
    from utils.predictor import LSTMPredictor
    
    # Load the trained model
    predictor = LSTMPredictor('models/lstm_model.h5')
    
    # Generate test data
    test_data = generate_sample_data(days=60)
    test_data['category'] = 'General'
    
    # Make predictions
    predictions = predictor.predict_spending(test_data, days=30)
    
    print("\n📅 Next 30 Days Forecast:")
    print(f"Total Predicted Spending: ₹{predictions['total_forecast']:,.2f}")
    print(f"Average Daily Spending: ₹{predictions['total_forecast']/30:,.2f}")
    print(f"Model Confidence: {predictions['model_confidence']*100:.1f}%")
    
    # Show first 5 predictions
    print("\n📊 Sample Predictions (First 5 days):")
    for i in range(5):
        date = predictions['forecast_dates'][i]
        amount = predictions['forecast_values'][i]
        print(f"  {date}: ₹{amount:,.2f}")

if __name__ == "__main__":
    try:
        # Train the model
        trainer = train_lstm_model()
        
        # Test predictions
        test_predictions()
        
        print("\n" + "=" * 50)
        print("🎉 Model training and testing complete!")
        print("🚀 You can now run the application with: python app.py")
        
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        print("Please make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")