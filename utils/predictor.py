import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# Optional imports with error handling
try:
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    import joblib
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠️ Scikit-learn not installed. Using basic predictions.")

try:
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')  # Suppress TensorFlow warnings
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    print("⚠️ TensorFlow not installed. Using statistical predictions.")

class LSTMPredictor:
    """Enhanced LSTM Predictor with fallback to statistical methods"""
    
    def __init__(self, model_path='models/lstm_model.h5', scaler_path='models/lstm_model_scaler.pkl'):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = None
        self.scaler = None
        self.sequence_length = 7  # Fixed to 7 days
        
        # Try to load existing model
        self.load_model()
    
    def load_model(self):
        """Load trained model and scaler if they exist"""
        try:
            if HAS_TENSORFLOW and os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
                print("✅ LSTM model loaded successfully")
            
            if HAS_SKLEARN and os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                print("✅ Scaler loaded successfully")
                
        except Exception as e:
            print(f"⚠️ Could not load model: {e}")
            self.model = None
            self.scaler = None
    
    def prepare_data(self, df):
        """Prepare data for prediction"""
        try:
            # Ensure we have a date column
            if 'date' not in df.columns:
                raise ValueError("DataFrame must have a 'date' column")
            
            # Convert date column to datetime if it's not already
            df = df.copy()
            df['date'] = pd.to_datetime(df['date'])
            
            # Sort by date
            df = df.sort_values('date')
            
            # Create daily spending aggregation
            daily_spending = df.groupby('date')['amount'].sum().reset_index()
            
            # Fill missing dates with 0 spending
            date_range = pd.date_range(
                start=daily_spending['date'].min(),
                end=daily_spending['date'].max(),
                freq='D'
            )
            
            full_range = pd.DataFrame({'date': date_range})
            daily_spending = full_range.merge(daily_spending, on='date', how='left')
            daily_spending['amount'] = daily_spending['amount'].fillna(0)
            
            return daily_spending
            
        except Exception as e:
            print(f"Data preparation error: {e}")
            return None
    
    def create_sequences(self, data, sequence_length):
        """Create sequences for LSTM training/prediction"""
        sequences = []
        targets = []
        
        for i in range(len(data) - sequence_length):
            seq = data[i:(i + sequence_length)]
            target = data[i + sequence_length]
            sequences.append(seq)
            targets.append(target)
        
        return np.array(sequences), np.array(targets)
    
    def lstm_prediction(self, daily_data, days=30):
        """LSTM-based prediction"""
        try:
            if not self.model or not self.scaler:
                print("⚠️ LSTM model or scaler not available")
                return None
            
            amounts = daily_data['amount'].values.reshape(-1, 1)
            
            # Scale the data
            scaled_data = self.scaler.transform(amounts)
            
            # Check if we have enough data for the sequence
            if len(scaled_data) < self.sequence_length:
                print(f"⚠️ Not enough data for LSTM: need {self.sequence_length}, have {len(scaled_data)}")
                return None
            
            # Use the last sequence to predict
            last_sequence = scaled_data[-self.sequence_length:].reshape(1, self.sequence_length, 1)
            
            predictions = []
            current_sequence = last_sequence.copy()
            
            for _ in range(days):
                # Predict next value
                next_pred = self.model.predict(current_sequence, verbose=0)
                predictions.append(next_pred[0, 0])
                
                # Update sequence for next prediction
                current_sequence = np.roll(current_sequence, -1, axis=1)
                current_sequence[0, -1, 0] = next_pred[0, 0]
            
            # Inverse transform predictions
            predictions = np.array(predictions).reshape(-1, 1)
            predictions = self.scaler.inverse_transform(predictions).flatten()
            
            # Ensure non-negative predictions
            predictions = np.maximum(predictions, 0)
            
            daily_avg = np.mean(predictions)
            total_predicted = sum(predictions)
            
            print(f"🤖 LSTM prediction: Daily avg = ₹{daily_avg:.2f}")
            
            return {
                'predictions': predictions.tolist(),
                'daily_average': float(daily_avg),
                'total_predicted': float(total_predicted),
                'method': 'lstm',
                'confidence': 85.0,
                'confidence_level': 'high'
            }
            
        except Exception as e:
            print(f"LSTM prediction error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def statistical_prediction(self, daily_data, days=30):
        """Improved statistical prediction method"""
        try:
            amounts = daily_data['amount'].values
            
            if len(amounts) == 0:
                return {
                    'predictions': [100.0] * days,
                    'daily_average': 100.0,
                    'total_predicted': 100.0 * days,
                    'method': 'fallback',
                    'confidence': 30.0,
                    'confidence_level': 'low'
                }
            
            # Basic statistics
            overall_avg = np.mean(amounts)
            median_spending = np.median(amounts)
            
            print(f"📊 Overall average: ₹{overall_avg:.2f}")
            print(f"📊 Median spending: ₹{median_spending:.2f}")
            
            # Use different approaches based on data length
            if len(amounts) < 7:
                # Very limited data - use simple average
                base_prediction = overall_avg
                confidence = 40.0
                method_detail = 'simple_average'
                
            elif len(amounts) < 14:
                # Limited data - use recent average with slight trend
                recent_avg = np.mean(amounts[-7:])
                base_prediction = (recent_avg * 0.7 + overall_avg * 0.3)
                confidence = 55.0
                method_detail = 'recent_weighted'
                
            else:
                # Sufficient data - use more sophisticated approach
                recent_7 = np.mean(amounts[-7:])
                recent_14 = np.mean(amounts[-14:])
                recent_30 = np.mean(amounts[-30:]) if len(amounts) >= 30 else recent_14
                
                print(f"📊 Recent 7 days: ₹{recent_7:.2f}")
                print(f"📊 Recent 14 days: ₹{recent_14:.2f}")
                print(f"📊 Recent 30 days: ₹{recent_30:.2f}")
                
                # Calculate trend (conservative)
                trend = (recent_7 - recent_14) * 0.1  # Very small trend impact
                
                # Weighted average favoring recent data but not too much
                base_prediction = (recent_7 * 0.4 + recent_14 * 0.3 + recent_30 * 0.2 + overall_avg * 0.1)
                
                # Calculate confidence based on consistency
                std_dev = np.std(amounts)
                cv = std_dev / overall_avg if overall_avg > 0 else 1
                
                if cv < 0.3:
                    confidence = 80.0
                elif cv < 0.5:
                    confidence = 70.0
                elif cv < 0.8:
                    confidence = 60.0
                else:
                    confidence = 50.0
                    
                method_detail = 'weighted_trend'
                
                print(f"📊 Trend: ₹{trend:.2f}")
                print(f"📊 Coefficient of variation: {cv:.2f}")
            
            print(f"📊 Base prediction: ₹{base_prediction:.2f}")
            
            # Generate daily predictions with some variation
            predictions = []
            
            # Simple weekly pattern (weekends might be different)
            weekly_multipliers = [1.0, 0.9, 0.9, 0.9, 0.9, 1.1, 1.2]  # Mon-Sun
            
            for day in range(days):
                day_of_week = day % 7
                weekly_factor = weekly_multipliers[day_of_week]
                
                # Start with base prediction
                daily_pred = base_prediction * weekly_factor
                
                # Add small trend if we have enough data
                if len(amounts) >= 14:
                    trend_adjustment = trend * (day + 1) * 0.02  # Very small trend
                    daily_pred += trend_adjustment
                
                # Add small random variation (±10%)
                variation = np.random.normal(0, daily_pred * 0.1)
                daily_pred = max(0, daily_pred + variation)
                
                predictions.append(daily_pred)
            
            # Calculate final statistics
            daily_avg = np.mean(predictions)
            total_predicted = sum(predictions)
            
            print(f"📊 Final daily average: ₹{daily_avg:.2f}")
            print(f"📊 Total predicted: ₹{total_predicted:.2f}")
            
            return {
                'predictions': [float(p) for p in predictions],
                'daily_average': float(daily_avg),
                'total_predicted': float(total_predicted),
                'base_prediction': float(base_prediction),
                'overall_average': float(overall_avg),
                'method': 'statistical',
                'method_detail': method_detail,
                'confidence': float(confidence),
                'confidence_level': 'high' if confidence > 75 else 'medium' if confidence > 60 else 'low'
            }
            
        except Exception as e:
            print(f"Statistical prediction error: {e}")
            import traceback
            traceback.print_exc()
            
            # Safe fallback
            fallback_daily = np.mean(amounts) if len(amounts) > 0 else 100.0
            return {
                'predictions': [fallback_daily] * days,
                'daily_average': fallback_daily,
                'total_predicted': fallback_daily * days,
                'method': 'error_fallback',
                'confidence': 30.0,
                'confidence_level': 'low',
                'error': str(e)
            }
    
    def predict_spending(self, df, days=30):
        """Main prediction method with LSTM priority"""
        try:
            # Prepare data
            daily_data = self.prepare_data(df)
            
            if daily_data is None or len(daily_data) == 0:
                raise ValueError("No valid data for prediction")
            
            print(f"📊 Prepared {len(daily_data)} days of data for prediction")
            print(f"📈 Date range: {daily_data['date'].min()} to {daily_data['date'].max()}")
            print(f"💰 Total spending in data: ₹{daily_data['amount'].sum():,.2f}")
            print(f"📅 Average daily spending: ₹{daily_data['amount'].mean():,.2f}")
            
            # Try LSTM prediction first (if model exists and is compatible)
            if HAS_TENSORFLOW and self.model and self.scaler:
                print("🤖 Attempting LSTM prediction...")
                
                # Check if we have enough data for LSTM
                if len(daily_data) >= self.sequence_length:
                    lstm_result = self.lstm_prediction(daily_data, days)
                    if lstm_result and lstm_result.get('daily_average', 0) > 0:
                        print("✅ LSTM prediction successful!")
                        return lstm_result
                    else:
                        print("⚠️ LSTM prediction failed, falling back to statistical method")
                else:
                    print(f"⚠️ Not enough data for LSTM (need {self.sequence_length}, have {len(daily_data)})")
            else:
                print("ℹ️ LSTM model not available, using statistical prediction")
            
            # Fall back to statistical prediction
            print("📊 Using statistical prediction method...")
            result = self.statistical_prediction(daily_data, days)
            
            # Validate result
            if result.get('daily_average', 0) <= 0:
                print("⚠️ Invalid daily average, using fallback calculation")
                avg_spending = daily_data['amount'].mean()
                result['daily_average'] = float(avg_spending)
                result['total_predicted'] = float(avg_spending * days)
                result['predictions'] = [float(avg_spending)] * days
            
            print(f"✅ Prediction complete - Daily avg: ₹{result['daily_average']:,.2f}")
            print(f"📊 Total predicted: ₹{result['total_predicted']:,.2f}")
            print(f"🎯 Confidence: {result['confidence']:.1f}%")
            print(f"🔧 Method: {result['method']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            import traceback
            traceback.print_exc()
            
            # Return safe fallback
            fallback_daily = 150.0
            return {
                'predictions': [fallback_daily] * days,
                'daily_average': fallback_daily,
                'total_predicted': fallback_daily * days,
                'method': 'error_fallback',
                'confidence': 30.0,
                'confidence_level': 'low',
                'error': str(e)
            }
    
    def train_model(self, df, epochs=50, batch_size=32):
        """Train LSTM model on historical data"""
        if not HAS_TENSORFLOW or not HAS_SKLEARN:
            print("⚠️ Cannot train model: TensorFlow or Scikit-learn not available")
            return False
        
        try:
            # Prepare data
            daily_data = self.prepare_data(df)
            if daily_data is None or len(daily_data) < 30:
                print("❌ Not enough data to train model (need at least 30 days)")
                return False
            
            amounts = daily_data['amount'].values.reshape(-1, 1)
            
            # Scale data
            self.scaler = MinMaxScaler()
            scaled_data = self.scaler.fit_transform(amounts)
            
            # Create sequences
            X, y = self.create_sequences(scaled_data.flatten(), self.sequence_length)
            
            if len(X) < 10:
                print("❌ Not enough sequences for training")
                return False
            
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Reshape for LSTM
            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
            
            # Build model
            self.model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(self.sequence_length, 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            self.model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
            
            # Train model
            print(f"🚀 Training LSTM model with {len(X_train)} sequences...")
            history = self.model.fit(
                X_train, y_train,
                batch_size=batch_size,
                epochs=epochs,
                validation_data=(X_test, y_test),
                verbose=1
            )
            
            # Save model and scaler
            os.makedirs('models', exist_ok=True)
            self.model.save(self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            print("✅ Model training completed and saved")
            return True
            
        except Exception as e:
            print(f"❌ Training error: {e}")
            return False