"""
Database management utilities for BudgetWise AI
Handles all database operations and queries
"""

import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from contextlib import contextmanager

class DatabaseManager:
    """Manage SQLite database operations for transactions"""
    
    def __init__(self, db_path='transactions.db'):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_db(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database tables"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL,
                    category TEXT,
                    transaction_type TEXT DEFAULT 'debit',
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_date 
                ON transactions(user_id, date DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_category 
                ON transactions(category)
            ''')
            
            # Predictions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    prediction_date DATE NOT NULL,
                    forecast_data TEXT,
                    accuracy_score REAL,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Budgets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    period TEXT DEFAULT 'monthly',
                    start_date DATE,
                    end_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    currency TEXT DEFAULT 'INR',
                    notification_enabled BOOLEAN DEFAULT 1,
                    weekly_report BOOLEAN DEFAULT 1,
                    monthly_report BOOLEAN DEFAULT 1,
                    theme TEXT DEFAULT 'light',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def store_transactions(self, user_id, processed_data):
        """Store processed transactions in database"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            for transaction in processed_data['transactions']:
                # Check if transaction already exists
                cursor.execute('''
                    SELECT id FROM transactions 
                    WHERE user_id = ? AND date = ? AND description = ? AND amount = ?
                ''', (user_id, transaction['date'], transaction['description'], 
                     transaction['amount']))
                
                if cursor.fetchone() is None:
                    # Insert new transaction
                    cursor.execute('''
                        INSERT INTO transactions 
                        (user_id, date, description, amount, category, tags)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        transaction['date'],
                        transaction.get('description', ''),
                        transaction['amount'],
                        transaction.get('category', 'Others'),
                        json.dumps(transaction.get('tags', []))
                    ))
            
            conn.commit()
            return cursor.rowcount
    
    def get_user_transactions(self, user_id, days=30, category=None):
        """Retrieve user transaction history"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            query = '''
                SELECT date, description, amount, category, tags
                FROM transactions
                WHERE user_id = ? AND date >= ?
            '''
            params = [user_id, start_date.strftime('%Y-%m-%d')]
            
            if category:
                query += ' AND category = ?'
                params.append(category)
            
            query += ' ORDER BY date DESC'
            
            cursor.execute(query, params)
            transactions = cursor.fetchall()
            
            # Convert to list of dictionaries
            result = []
            for trans in transactions:
                result.append({
                    'date': trans['date'],
                    'description': trans['description'],
                    'amount': trans['amount'],
                    'category': trans['category'],
                    'tags': json.loads(trans['tags']) if trans['tags'] else []
                })
            
            return result
    
    def get_spending_summary(self, user_id, period='month'):
        """Get spending summary for user"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            if period == 'month':
                start_date = datetime.now().replace(day=1)
            elif period == 'week':
                start_date = datetime.now() - timedelta(days=7)
            elif period == 'year':
                start_date = datetime.now().replace(month=1, day=1)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Total spending
            cursor.execute('''
                SELECT SUM(amount) as total
                FROM transactions
                WHERE user_id = ? AND date >= ?
            ''', (user_id, start_date.strftime('%Y-%m-%d')))
            
            total = cursor.fetchone()['total'] or 0
            
            # Category breakdown
            cursor.execute('''
                SELECT category, SUM(amount) as amount
                FROM transactions
                WHERE user_id = ? AND date >= ?
                GROUP BY category
                ORDER BY amount DESC
            ''', (user_id, start_date.strftime('%Y-%m-%d')))
            
            categories = cursor.fetchall()
            
            # Daily average
            days_diff = (datetime.now() - start_date).days + 1
            daily_avg = total / days_diff if days_diff > 0 else 0
            
            return {
                'total': total,
                'daily_average': daily_avg,
                'categories': {cat['category']: cat['amount'] for cat in categories},
                'period': period,
                'start_date': start_date.strftime('%Y-%m-%d')
            }
    
    def get_category_trends(self, user_id, category, days=90):
        """Get spending trends for a specific category"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT DATE(date) as date, SUM(amount) as daily_total
                FROM transactions
                WHERE user_id = ? AND category = ? AND date >= ?
                GROUP BY DATE(date)
                ORDER BY date
            ''', (user_id, category, start_date.strftime('%Y-%m-%d')))
            
            trends = cursor.fetchall()
            
            return {
                'dates': [t['date'] for t in trends],
                'amounts': [t['daily_total'] for t in trends],
                'category': category
            }
    
    def store_prediction(self, user_id, prediction_data, accuracy_score=None):
        """Store model predictions"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO predictions 
                (user_id, prediction_date, forecast_data, accuracy_score, model_version)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().strftime('%Y-%m-%d'),
                json.dumps(prediction_data),
                accuracy_score,
                '1.0.0'
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_latest_prediction(self, user_id):
        """Get the most recent prediction for a user"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM predictions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,))
            
            prediction = cursor.fetchone()
            
            if prediction:
                return {
                    'id': prediction['id'],
                    'prediction_date': prediction['prediction_date'],
                    'forecast_data': json.loads(prediction['forecast_data']),
                    'accuracy_score': prediction['accuracy_score'],
                    'created_at': prediction['created_at']
                }
            
            return None
    
    def manage_budget(self, user_id, category, amount, period='monthly'):
        """Create or update budget for a category"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Check if budget exists
            cursor.execute('''
                SELECT id FROM budgets
                WHERE user_id = ? AND category = ? AND period = ?
            ''', (user_id, category, period))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing budget
                cursor.execute('''
                    UPDATE budgets
                    SET amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (amount, existing['id']))
            else:
                # Create new budget
                if period == 'monthly':
                    start_date = datetime.now().replace(day=1)
                    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                else:
                    start_date = datetime.now()
                    end_date = start_date + timedelta(days=30)
                
                cursor.execute('''
                    INSERT INTO budgets 
                    (user_id, category, amount, period, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, category, amount, period, 
                     start_date.strftime('%Y-%m-%d'),
                     end_date.strftime('%Y-%m-%d')))
            
            conn.commit()
    
    def get_budget_status(self, user_id):
        """Get budget vs actual spending status"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Get all budgets
            cursor.execute('''
                SELECT * FROM budgets
                WHERE user_id = ?
            ''', (user_id,))
            
            budgets = cursor.fetchall()
            
            budget_status = []
            
            for budget in budgets:
                # Get actual spending for this category
                cursor.execute('''
                    SELECT SUM(amount) as spent
                    FROM transactions
                    WHERE user_id = ? AND category = ? 
                    AND date >= ? AND date <= ?
                ''', (user_id, budget['category'], 
                     budget['start_date'], budget['end_date']))
                
                spent = cursor.fetchone()['spent'] or 0
                
                budget_status.append({
                    'category': budget['category'],
                    'budget': budget['amount'],
                    'spent': spent,
                    'remaining': budget['amount'] - spent,
                    'percentage': (spent / budget['amount'] * 100) if budget['amount'] > 0 else 0,
                    'period': budget['period']
                })
            
            return budget_status
    
    def get_insights(self, user_id):
        """Generate financial insights for user"""
        summary = self.get_spending_summary(user_id, 'month')
        budget_status = self.get_budget_status(user_id)
        
        insights = []
        
        # Spending trend insight
        last_month_summary = self.get_spending_summary(user_id, 'month')
        if last_month_summary['total'] > 0:
            insights.append({
                'type': 'info',
                'title': 'Monthly Spending',
                'message': f"You've spent ₹{last_month_summary['total']:,.2f} this month",
                'icon': 'bi-wallet2'
            })
        
        # Budget alerts
        for budget in budget_status:
            if budget['percentage'] > 90:
                insights.append({
                    'type': 'warning',
                    'title': 'Budget Alert',
                    'message': f"You've used {budget['percentage']:.0f}% of your {budget['category']} budget",
                    'icon': 'bi-exclamation-triangle'
                })
            elif budget['percentage'] > 100:
                insights.append({
                    'type': 'danger',
                    'title': 'Budget Exceeded',
                    'message': f"You've exceeded your {budget['category']} budget by ₹{abs(budget['remaining']):,.2f}",
                    'icon': 'bi-x-circle'
                })
        
        # Top spending category
        if summary['categories']:
            top_category = max(summary['categories'].items(), key=lambda x: x[1])
            insights.append({
                'type': 'info',
                'title': 'Top Spending Category',
                'message': f"Your highest expense is {top_category[0]} at ₹{top_category[1]:,.2f}",
                'icon': 'bi-graph-up'
            })
        
        # Savings opportunity
        daily_avg = summary['daily_average']
        if daily_avg > 2000:  # High daily spending
            potential_savings = daily_avg * 0.1 * 30  # 10% reduction
            insights.append({
                'type': 'success',
                'title': 'Savings Opportunity',
                'message': f"Reducing daily spending by 10% could save you ₹{potential_savings:,.2f} monthly",
                'icon': 'bi-piggy-bank'
            })
        
        return insights