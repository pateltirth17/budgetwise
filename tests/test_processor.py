"""
Unit tests for data processor module
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = DataProcessor()
        
        # Create sample transaction data
        self.sample_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'description': [
                'swiggy order', 'uber ride', 'amazon shopping',
                'electricity bill', 'netflix subscription', 'grocery store',
                'petrol pump', 'restaurant dinner', 'mobile recharge',
                'gym membership'
            ] * 3,
            'amount': np.random.uniform(100, 5000, 30)
        })
    
    def test_categorization(self):
        """Test transaction categorization"""
        categories = {
            'swiggy order': 'Food & Dining',
            'uber ride': 'Transportation',
            'amazon shopping': 'Shopping',
            'electricity bill': 'Utilities',
            'netflix subscription': 'Entertainment'
        }
        
        for description, expected_category in categories.items():
            result = self.processor._categorize_transaction(description)
            self.assertEqual(result, expected_category,
                           f"Failed to categorize '{description}' as '{expected_category}'")
    
    def test_process_transactions(self):
        """Test transaction processing"""
        result = self.processor.process_transactions(self.sample_data)
        
        self.assertIn('transactions', result)
        self.assertIn('total_spending', result)
        self.assertIn('category_breakdown', result)
        self.assertIn('dates', result)
        self.assertIn('daily_totals', result)
        
        # Check if all transactions are processed
        self.assertEqual(len(result['transactions']), len(self.sample_data))
        
        # Check if total spending is calculated correctly
        expected_total = self.sample_data['amount'].sum()
        self.assertAlmostEqual(result['total_spending'], expected_total, places=2)
    
    def test_clean_data(self):
        """Test data cleaning"""
        # Add some dirty data
        dirty_data = self.sample_data.copy()
        dirty_data.loc[5, 'amount'] = np.nan
        dirty_data.loc[10, 'amount'] = 0
        dirty_data.loc[15, 'description'] = None
        
        cleaned = self.processor._clean_data(dirty_data)
        
        # Check if NaN values are removed
        self.assertFalse(cleaned['amount'].isna().any())
        
        # Check if zero amounts are removed
        self.assertTrue((cleaned['amount'] > 0).all())
        
        # Check if descriptions are filled
        self.assertFalse(cleaned['description'].isna().any())
    
    def test_prepare_lstm_data(self):
        """Test LSTM data preparation"""
        daily_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=60, freq='D'),
            'amount': np.random.uniform(1000, 5000, 60)
        })
        
        X, y, scaler = self.processor.prepare_lstm_data(daily_data, sequence_length=30)
        
        # Check shapes
        self.assertEqual(X.shape[0], y.shape[0])  # Same number of samples
        self.assertEqual(X.shape[1], 30)  # Sequence length
        
        # Check if data is normalized
        self.assertTrue((X >= 0).all() and (X <= 1).all())
        self.assertTrue((y >= 0).all() and (y <= 1).all())

if __name__ == '__main__':
    unittest.main()