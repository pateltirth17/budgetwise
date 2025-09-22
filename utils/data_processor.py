"""
Data Processing Utilities for BudgetWise AI
Handles CSV parsing, transaction categorization, and data preparation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

class DataProcessor:
    """Process and categorize financial transaction data"""
    
    def __init__(self):
        """Initialize with Indian expense categories"""
        self.categories = {
            'Food & Dining': [
                'swiggy', 'zomato', 'restaurant', 'cafe', 'food',
                'dining', 'lunch', 'dinner', 'breakfast', 'snacks',
                'pizza', 'burger', 'coffee', 'tea', 'dominos', 'mcdonalds'
            ],
            'Transportation': [
                'uber', 'ola', 'rapido', 'metro', 'bus', 'fuel',
                'petrol', 'diesel', 'parking', 'toll', 'cab', 'auto',
                'train', 'irctc', 'flight', 'indigo', 'spicejet'
            ],
            'Shopping': [
                'amazon', 'flipkart', 'myntra', 'ajio', 'shopping',
                'mall', 'store', 'market', 'clothes', 'shoes', 'fashion',
                'electronics', 'gadget', 'decathlon', 'ikea'
            ],
            'Entertainment': [
                'movie', 'netflix', 'hotstar', 'prime', 'spotify',
                'book', 'game', 'pvr', 'inox', 'cinema', 'concert',
                'event', 'amusement', 'park', 'museum'
            ],
            'Utilities': [
                'electricity', 'water', 'gas', 'internet', 'broadband',
                'mobile', 'recharge', 'bill', 'airtel', 'jio', 'vodafone',
                'wifi', 'dth', 'tatasky', 'maintenance'
            ],
            'Healthcare': [
                'medical', 'doctor', 'hospital', 'pharmacy', 'medicine',
                'clinic', 'health', 'gym', 'fitness', 'yoga', 'insurance',
                'apollo', 'fortis', 'medplus', '1mg', 'pharmeasy'
            ],
            'Groceries': [
                'grocery', 'supermarket', 'bigbasket', 'grofers', 'blinkit',
                'zepto', 'dunzo', 'vegetable', 'fruit', 'milk', 'bread',
                'reliance fresh', 'more', 'dmart', 'spencer'
            ],
            'Education': [
                'school', 'college', 'university', 'course', 'tuition',
                'book', 'udemy', 'coursera', 'upgrad', 'byju', 'unacademy',
                'fees', 'exam', 'certification'
            ],
            'Investment': [
                'mutual fund', 'sip', 'stock', 'trading', 'zerodha',
                'groww', 'upstox', 'investment', 'fd', 'rd', 'ppf',
                'nps', 'gold', 'crypto', 'bitcoin'
            ],
            'Transfer': [
                'upi', 'transfer', 'neft', 'imps', 'rtgs', 'paytm',
                'phonepe', 'gpay', 'bhim', 'send', 'received'
            ]
        }
    
    def process_transactions(self, df):
        """
        Process raw transaction data from CSV
        
        Args:
            df: Pandas DataFrame with transaction data
            
        Returns:
            Dictionary with processed data
        """
        try:
            # Standardize column names
            df.columns = [col.lower().strip() for col in df.columns]
            
            # Identify and parse relevant columns
            df = self._identify_columns(df)
            
            # Clean and preprocess data
            df = self._clean_data(df)
            
            # Categorize transactions
            df['category'] = df['description'].apply(self._categorize_transaction)
            
            # Calculate daily totals
            daily_totals = df.groupby('date')['amount'].sum().reset_index()
            
            # Category breakdown
            category_breakdown = df.groupby('category')['amount'].sum().to_dict()
            
            # Prepare response
            result = {
                'transactions': df.to_dict('records'),
                'total_spending': float(df['amount'].sum()),
                'category_breakdown': {k: float(v) for k, v in category_breakdown.items()},
                'dates': daily_totals['date'].dt.strftime('%Y-%m-%d').tolist(),
                'daily_totals': daily_totals['amount'].tolist(),
                'start_date': df['date'].min().strftime('%Y-%m-%d'),
                'end_date': df['date'].max().strftime('%Y-%m-%d')
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error processing transactions: {str(e)}")
    
    def _identify_columns(self, df):
        """Identify and map relevant columns from various bank formats"""
        
        # Common column mappings for Indian banks
        column_mappings = {
            'date': ['date', 'transaction date', 'trans date', 'txn date', 'value date'],
            'description': ['description', 'narration', 'remarks', 'particulars', 'details'],
            'amount': ['amount', 'debit', 'withdrawal', 'txn amount', 'transaction amount'],
            'balance': ['balance', 'closing balance', 'available balance']
        }
        
        result_df = pd.DataFrame()
        
        for target_col, possible_names in column_mappings.items():
            for col in df.columns:
                if any(name in col.lower() for name in possible_names):
                    result_df[target_col] = df[col]
                    break
            
            # If column not found, try to infer
            if target_col not in result_df.columns:
                if target_col == 'date':
                    # Find date column by checking for date patterns
                    for col in df.columns:
                        if pd.to_datetime(df[col], errors='coerce').notna().sum() > len(df) * 0.8:
                            result_df['date'] = pd.to_datetime(df[col], errors='coerce')
                            break
                elif target_col == 'amount':
                    # Find numeric column that likely represents amount
                    for col in df.columns:
                        if df[col].dtype in ['float64', 'int64']:
                            result_df['amount'] = df[col]
                            break
        
        # Ensure required columns exist
        if 'description' not in result_df.columns:
            result_df['description'] = 'Transaction'
        
        if 'amount' not in result_df.columns:
            raise ValueError("Could not identify amount column in CSV")
        
        if 'date' not in result_df.columns:
            # Use current date if date column not found
            result_df['date'] = pd.Timestamp.now()
        
        return result_df
    
    def _clean_data(self, df):
        """Clean and preprocess transaction data"""
        
        # Remove NaN values
        df = df.dropna(subset=['amount'])
        
        # Convert amount to absolute value (handle both debit and credit)
        df['amount'] = df['amount'].abs()
        
        # Remove zero transactions
        df = df[df['amount'] > 0]
        
        # Clean description text
        df['description'] = df['description'].fillna('')
        df['description'] = df['description'].str.lower().str.strip()
        
        # Sort by date
        df = df.sort_values('date')
        
        return df
    
    def _categorize_transaction(self, description):
        """
        Categorize a transaction based on its description
        
        Args:
            description: Transaction description string
            
        Returns:
            Category name
        """
        description = description.lower()
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in description:
                    return category
        
        # Default category if no match found
        return 'Others'
    
    def prepare_lstm_data(self, df, sequence_length=30):
        """
        Prepare data for LSTM model training/prediction
        
        Args:
            df: DataFrame with daily spending totals
            sequence_length: Number of days to use for prediction
            
        Returns:
            Numpy arrays for LSTM input
        """
        # Ensure data is sorted by date
        df = df.sort_values('date')
        
        # Fill missing dates with 0
        date_range = pd.date_range(start=df['date'].min(), 
                                  end=df['date'].max(), 
                                  freq='D')
        df_complete = pd.DataFrame({'date': date_range})
        df_complete = df_complete.merge(df, on='date', how='left')
        df_complete['amount'] = df_complete['amount'].fillna(0)
        
        # Normalize data
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df_complete['amount'].values.reshape(-1, 1))
        
        # Create sequences
        X, y = [], []
        for i in range(sequence_length, len(scaled_data)):
            X.append(scaled_data[i-sequence_length:i, 0])
            y.append(scaled_data[i, 0])
        
        return np.array(X), np.array(y), scaler