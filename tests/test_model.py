"""
Unit tests for model training and prediction
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.model_trainer import ModelTrainer
from utils.predictor import LSTMPredictor

class TestModelTrainer(unittest.TestCase):
    """Test cases for ModelTrainer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.trainer = ModelTrainer(sequence_length=10)
        
        # Create sample data
        self.sample_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=100, freq='D'),
            'amount': np.random.uniform(1000, 5000, 100)
        })
    
    def test_create_model(self):
        """Test model creation"""
        model = self.trainer.create_model((10, 1))
        
        self.assertIsNotNone(model)
        self.assertEqual(len(model.layers), 7)  # Check number of layers
        
        # Check input shape
        input_shape = model.layers[0].input_shape
        self.assertEqual(input_shape[1:], (10, 1))
    
    def test_prepare_sequences(self):
        """Test sequence preparation"""
        data = np.random.uniform(1000, 5000, 50)
        X, y = self.trainer.prepare_sequences(data)
        
        # Check shapes
        expected_samples = len(data) - self.trainer.sequence_length
        self.assertEqual(len(X), expected_samples)
        self.assertEqual(len(y), expected_samples)
        
        # Check sequence length
        self.assertEqual(X.shape[1], self.trainer.sequence_length)
    
    def test_model_save_load(self):
        """Test model saving and loading"""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'test_model.h5')
            
            # Create and train a simple model
            data = np.random.uniform(1000, 5000, 50)
            X, y = self.trainer.prepare_sequences(data)
            X = X.reshape((X.shape[0], X.shape[1], 1))
            
            self.trainer.model = self.trainer.create_model((self.trainer.sequence_length, 1))
            self.trainer.model.fit(X, y, epochs=1, verbose=0)
            
            # Save model
            self.trainer.save_model(model_path)
            
            # Check if files are created
            self.assertTrue(os.path.exists(model_path))
            self.assertTrue(os.path.exists(model_path.replace('.h5', '_scaler.pkl')))
            
            # Load model in predictor
            predictor = LSTMPredictor(model_path)
            self.assertIsNotNone(predictor.model)

class TestLSTMPredictor(unittest.TestCase):
    """Test cases for LSTMPredictor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.predictor = LSTMPredictor('models/lstm_model.h5')
        
        # Create sample transaction data
        self.sample_df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=60, freq='D'),
            'amount': np.random.uniform(1000, 5000, 60),
            'category': ['Food & Dining'] * 60
        })
    
    def test_predict_spending(self):
        """Test spending prediction"""
        predictions = self.predictor.predict_spending(self.sample_df, days=30)
        
        self.assertIn('forecast_values', predictions)
        self.assertIn('forecast_dates', predictions)
        self.assertIn('total_forecast', predictions)
        self.assertIn('confidence_interval', predictions)
        
        # Check prediction length
        self.assertEqual(len(predictions['forecast_values']), 30)
        self.assertEqual(len(predictions['forecast_dates']), 30)
        
        # Check if dates are properly formatted
        for date_str in predictions['forecast_dates']:
            datetime.strptime(date_str, '%Y-%m-%d')
    
    def test_dummy_predictions(self):
        """Test dummy predictions when model is not available"""
        predictor = LSTMPredictor('non_existent_model.h5')
        predictions = predictor._generate_dummy_predictions(30)
        
        self.assertEqual(len(predictions['forecast_values']), 30)
        self.assertEqual(len(predictions['forecast_dates']), 30)
        self.assertIsInstance(predictions['total_forecast'], (int, float))

if __name__ == '__main__':
    unittest.main()