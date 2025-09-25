"""
BudgetWise AI - Fixed Version 2.3
All issues resolved: Routes, Imports, Error Handling + Password Reset
"""

import os
import json
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from utils.predictor import LSTMPredictor
from sqlalchemy import text, inspect, func
import warnings
warnings.filterwarnings('ignore')

# Import for PDF generation (moved to top)
from io import BytesIO
import base64

# Import for password reset functionality
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from threading import Thread
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
# Optional imports with error handling
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ Matplotlib not installed. Some features may be limited.")

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("⚠️ ReportLab not installed. PDF generation will be limited.")

# ============= FLASK APP CONFIGURATION =============

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-budgetwise-2024')
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///instance/budgetwise.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx', 'xls'}

# Email configuration - with fallback values
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

# Important: Make sure MAIL_DEFAULT_SENDER is set
if app.config['MAIL_USERNAME']:
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
else:
    # Fallback for testing - replace with your email
    app.config['MAIL_DEFAULT_SENDER'] = 'noreply@budgetwiseai.com'

# Debug: Print to verify
print(f"Mail config: Server={app.config['MAIL_SERVER']}, Port={app.config['MAIL_PORT']}")
print(f"Mail sender: {app.config['MAIL_DEFAULT_SENDER']}")

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
CORS(app)
mail = Mail(app)

with app.app_context():
    try:
        db.create_all()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"Warning: Could not create tables: {e}")
        
# Create necessary directories
for folder in ['uploads', 'models', 'static/images', 'data', 'templates/email']:
    os.makedirs(folder, exist_ok=True)

# ============= FORMS =============

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
               message='Password must contain uppercase, lowercase, number and special character')
    ])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
               message='Password must contain uppercase, lowercase, number and special character')
    ])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
               message='Password must contain uppercase, lowercase, number and special character')
    ])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

# ============= EMAIL FUNCTIONS =============

from flask import current_app

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)
        
def send_email(subject, sender, recipients, text_body, html_body):
    # Ensure sender is set
    if not sender:
        sender = app.config.get('MAIL_DEFAULT_SENDER', 'noreply@budgetwiseai.com')
    
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[BudgetWise AI] Reset Your Password',
               sender=app.config['MAIL_DEFAULT_SENDER'],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                       user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                       user=user, token=token))

# ============= DATABASE MODELS =============

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})
    
    @staticmethod
    def verify_reset_password_token(token, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Transaction(db.Model):
    """Transaction model"""
    __tablename__ = 'transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), default='Others')
    transaction_type = db.Column(db.String(20), default='expense', server_default='expense')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'description': self.description,
            'amount': self.amount,
            'category': self.category,
            'type': self.transaction_type
        }

class Budget(db.Model):
    """Budget model for category-wise budgets"""
    __tablename__ = 'budget'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), default=lambda: datetime.now().strftime('%Y-%m'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'amount': self.amount,
            'month': self.month
        }

# ============= DATABASE HELPERS =============

def init_database():
    """Initialize database with proper schema"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check and fix schema issues
        fix_database_schema()
        
        print("✅ Database initialized successfully")

def fix_database_schema():
    """Fix any database schema issues"""
    try:
        inspector = inspect(db.engine)
        
        # Check if transaction table exists
        if 'transaction' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('transaction')]
            
            # Add missing transaction_type column if needed
            if 'transaction_type' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text(
                        "ALTER TABLE 'transaction' ADD COLUMN transaction_type VARCHAR(20) DEFAULT 'expense'"
                    ))
                    conn.commit()
                print("✅ Added missing transaction_type column")
        
        return True
    except Exception as e:
        print(f"⚠️ Schema check: {e}")
        return False

# ============= DATA PROCESSING =============

class DataProcessor:
    """Enhanced data processor for multiple CSV formats"""
    
    @staticmethod
    def categorize_transaction(description):
        """Categorize transaction based on description"""
        if not description:
            return 'Others'
            
        description = str(description).lower()
        
        categories = {
            'Food & Dining': ['swiggy', 'zomato', 'restaurant', 'food', 'coffee', 'lunch', 'dinner', 
                            'breakfast', 'cafe', 'pizza', 'burger', 'biryani', 'meals', 'eat',
                            'dominos', 'mcdonalds', 'kfc', 'subway', 'starbucks', 'hotel', 'dhaba',
                            'canteen', 'mess', 'tiffin', 'snacks', 'juice', 'bakery', 'sweet'],
            'Transportation': ['uber', 'ola', 'rapido', 'petrol', 'fuel', 'metro', 'bus', 'train',
                             'cab', 'taxi', 'auto', 'parking', 'toll', 'irctc', 'flight',
                             'diesel', 'cng', 'transit', 'transport', 'travel'],
            'Shopping': ['amazon', 'flipkart', 'myntra', 'shopping', 'mall', 'store', 'market',
                        'fashion', 'clothes', 'shoes', 'ajio', 'nykaa', 'meesho', 'shop',
                        'purchase', 'buy', 'ebay', 'walmart', 'retail'],
            'Entertainment': ['movie', 'netflix', 'hotstar', 'spotify', 'game', 'cinema', 'pvr',
                            'inox', 'bookmyshow', 'youtube', 'prime', 'sony', 'zee5',
                            'theater', 'concert', 'event', 'party', 'club'],
            'Utilities': ['electricity', 'water', 'gas', 'internet', 'mobile', 'bill', 'recharge',
                         'broadband', 'wifi', 'jio', 'airtel', 'vodafone', 'dth', 'electric',
                         'postpaid', 'prepaid', 'landline', 'maintenance'],
            'Healthcare': ['medical', 'doctor', 'hospital', 'pharmacy', 'medicine', 'health',
                          'clinic', 'apollo', 'fortis', '1mg', 'pharmeasy', 'gym', 'fitness',
                          'diagnostic', 'lab', 'test', 'consultation', 'treatment'],
            'Groceries': ['grocery', 'bigbasket', 'zepto', 'blinkit', 'vegetable', 'fruit',
                         'milk', 'grofers', 'dmart', 'more', 'reliance', 'fresh', 'mart',
                         'supermarket', 'kirana', 'provision', 'ration'],
            'Education': ['course', 'udemy', 'coursera', 'school', 'college', 'book', 'training',
                         'class', 'tuition', 'fees', 'exam', 'study', 'university',
                         'academy', 'institute', 'education', 'learning'],
            'Investment': ['mutual fund', 'sip', 'stock', 'trading', 'fd', 'ppf', 'investment',
                          'zerodha', 'groww', 'upstox', 'insurance', 'lic', 'policy',
                          'deposit', 'savings', 'nps', 'gold'],
            'Transfer': ['transfer', 'upi', 'neft', 'imps', 'paytm', 'phonepe', 'gpay',
                        'google pay', 'sent', 'payment', 'razorpay', 'cashback', 'refund']
        }
        
        # Check for keywords in description
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in description:
                    return category
        
        return 'Others'
    
    @staticmethod
    def process_csv(filepath):
        """Process CSV with support for multiple formats"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    print(f"Successfully read CSV with {encoding} encoding")
                    break
                except:
                    continue
            
            if df is None:
                raise ValueError("Could not read CSV file with any encoding")
            
            print(f"CSV Columns found: {list(df.columns)}")
            print(f"CSV Shape: {df.shape}")
            
            # Clean column names - remove spaces and convert to lowercase
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            print(f"Cleaned columns: {list(df.columns)}")
            
            transactions = []
            
            # Process based on detected format
            for idx, row in df.iterrows():
                try:
                    # Parse date - try multiple formats
                    date_col = next((col for col in df.columns if 'date' in col), None)
                    if date_col:
                        date_str = str(row[date_col]).strip()
                        parsed_date = pd.to_datetime(date_str, dayfirst=True).date()
                    else:
                        continue
                    
                    # Get amount
                    amount_col = next((col for col in df.columns if 'amount' in col or 'debit' in col or 'credit' in col), None)
                    if amount_col:
                        amount_str = str(row[amount_col]).replace(',', '').replace('₹', '').replace('Rs', '').strip()
                        amount = abs(float(amount_str))
                    else:
                        continue
                    
                    if amount <= 0:
                        continue
                    
                    # Get description
                    desc_col = next((col for col in df.columns if 'description' in col or 'narration' in col or 'particular' in col), None)
                    description = str(row[desc_col]) if desc_col and pd.notna(row[desc_col]) else 'Transaction'
                    
                    # Categorize
                    category = DataProcessor.categorize_transaction(description)
                    
                    # Determine transaction type
                    trans_type = 'expense'
                    if any(word in description.lower() for word in ['credit', 'received', 'refund', 'cashback', 'salary']):
                        trans_type = 'income'
                    
                    transactions.append({
                        'date': parsed_date,
                        'description': description[:200],
                        'amount': amount,
                        'category': category,
                        'type': trans_type
                    })
                    
                except Exception as e:
                    print(f"Error processing row {idx}: {e}")
                    continue
            
            print(f"Successfully processed {len(transactions)} transactions")
            
            if not transactions:
                raise ValueError("No valid transactions could be processed from the CSV")
            
            return transactions
            
        except Exception as e:
            print(f"CSV processing error: {str(e)}")
            raise Exception(f"CSV processing error: {str(e)}")

# ============= AUTHENTICATION HANDLERS =============

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============= ROUTES =============

@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/create-tables-now')
def create_tables():
    try:
        db.create_all()
        # Check what tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if tables:
            return f"✅ Success! Tables created: {tables}"
        else:
            return "⚠️ No tables found. Check DATABASE_URL in environment variables."
    except Exception as e:
        return f"❌ Error: {str(e)}"
        
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = SignUpForm()
    if form.validate_on_submit():
        # Check existing user
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return render_template('signup.html', form=form)
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken', 'danger')
            return render_template('signup.html', form=form)
        
        try:
            # Create new user
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
            print(f"Signup error: {e}")
    
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                send_password_reset_email(user)
                flash('Check your email for instructions to reset your password.', 'info')
                return redirect(url_for('login'))
            except Exception as e:
                print(f"Email sending error: {e}")
                flash('Error sending email. Please check your email configuration.', 'danger')
        else:
            flash('Email not found. Please check and try again.', 'danger')
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged-in users"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been changed successfully!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    return render_template('change_password.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - Enhanced with more data"""
    try:
        # Get date ranges
        today = datetime.now()
        month_start = today.replace(day=1)
        last_30_days = today - timedelta(days=30)
        
        # Get transactions for different periods
        month_transactions = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= month_start.date()
        ).all()
        
        last_30_transactions = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= last_30_days.date()
        ).all()
        
        # Calculate totals
        total_spending = sum(t.amount for t in month_transactions if t.transaction_type == 'expense')
        total_income = sum(t.amount for t in month_transactions if t.transaction_type == 'income')
        
        total_spending_30 = sum(t.amount for t in last_30_transactions if t.transaction_type == 'expense')
        total_income_30 = sum(t.amount for t in last_30_transactions if t.transaction_type == 'income')
        
        # Category breakdown
        category_spending = {}
        for t in last_30_transactions:
            if t.transaction_type == 'expense':
                if t.category not in category_spending:
                    category_spending[t.category] = 0
                category_spending[t.category] += t.amount
        
        # Daily spending for chart
        daily_spending = {}
        for i in range(30):
            date = (today - timedelta(days=i)).date()
            daily_spending[date.strftime('%Y-%m-%d')] = 0
        
        for t in last_30_transactions:
            if t.transaction_type == 'expense':
                date_str = t.date.strftime('%Y-%m-%d')
                if date_str in daily_spending:
                    daily_spending[date_str] += t.amount
        
        # Get recent transactions
        recent = Transaction.query.filter_by(user_id=current_user.id)\
                                 .order_by(Transaction.date.desc())\
                                 .limit(15).all()
        
        # Get budgets
        budgets = Budget.query.filter_by(
            user_id=current_user.id,
            month=today.strftime('%Y-%m')
        ).all()
        
        # Budget comparison
        budget_comparison = []
        for budget in budgets:
            spent = sum(t.amount for t in month_transactions 
                       if t.transaction_type == 'expense' and t.category == budget.category)
            budget_comparison.append({
                'category': budget.category,
                'budget': budget.amount,
                'spent': spent,
                'percentage': min((spent / budget.amount * 100) if budget.amount > 0 else 0, 100)
            })
        
        return render_template('dashboard.html',
                             total_spending=float(total_spending),
                             total_income=float(total_income),
                             total_spending_30=float(total_spending_30),
                             total_income_30=float(total_income_30),
                             balance=float(total_income - total_spending),
                             category_spending=category_spending,
                             daily_spending=daily_spending,
                             recent_transactions=recent,
                             budgets=budgets,
                             budget_comparison=budget_comparison,
                             current_month=today.strftime('%B %Y'))
                             
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'danger')
        
        return render_template('dashboard.html',
                             total_spending=0.0,
                             total_income=0.0,
                             total_spending_30=0.0,
                             total_income_30=0.0,
                             balance=0.0,
                             category_spending={},
                             daily_spending={},
                             recent_transactions=[],
                             budgets=[],
                             budget_comparison=[],
                             current_month=datetime.now().strftime('%B %Y'))

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """Add transaction manually"""
    if request.method == 'POST':
        try:
            # Get form data
            date_str = request.form.get('date')
            description = request.form.get('description', '').strip()
            amount = float(request.form.get('amount', 0))
            category = request.form.get('category', 'Others')
            trans_type = request.form.get('type', 'expense')
            
            if not date_str or not description or amount <= 0:
                flash('Please fill all fields correctly', 'danger')
                return redirect(url_for('add_transaction'))
            
            # Create transaction
            transaction = Transaction(
                user_id=current_user.id,
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                description=description,
                amount=amount,
                category=category,
                transaction_type=trans_type
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding transaction: {str(e)}', 'danger')
            print(f"Add transaction error: {e}")
    
    # Categories for dropdown
    categories = [
        'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
        'Utilities', 'Healthcare', 'Groceries', 'Education', 
        'Investment', 'Transfer', 'Others'
    ]
    
    return render_template('add_transaction.html', 
                         categories=categories,
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/transactions')
@login_required
def transactions():
    """View all transactions with filtering, statistics, and category breakdown"""

    page = request.args.get('page', 1, type=int)
    per_page = 20

    # --- Filter Parameters ---
    category = request.args.get('category', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = Transaction.query.filter(Transaction.user_id == current_user.id)

    if category:
        query = query.filter(Transaction.category == category)

    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= to_date)
        except ValueError:
            pass

    # --- All filtered results for calculations ---
    all_filtered_transactions = query.all()

    # --- Totals ---
    total_spending = sum(t.amount for t in all_filtered_transactions if t.transaction_type == 'expense')
    total_income = sum(t.amount for t in all_filtered_transactions if t.transaction_type == 'income')
    total_count = len(all_filtered_transactions)

    # --- Date Range & Average ---
    days_range = 0
    avg_per_day = 0
    
    if all_filtered_transactions:
        # Convert dates to date objects if they're datetime
        dates = []
        for t in all_filtered_transactions:
            if hasattr(t.date, 'date'):  # If it's a datetime object
                dates.append(t.date.date())
            else:  # If it's already a date object
                dates.append(t.date)
        
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            days_range = (max_date - min_date).days + 1  # +1 to include both start and end dates
            
            # Calculate average per day only if we have expenses
            if days_range > 0 and total_spending > 0:
                avg_per_day = total_spending / days_range
            else:
                avg_per_day = 0
            
            # Debug prints (remove in production)
            print(f"Min date: {min_date}, Max date: {max_date}")
            print(f"Days range: {days_range}, Total spending: {total_spending}")
            print(f"Average per day: {avg_per_day}")

    # --- Counts by type ---
    expense_count = sum(1 for t in all_filtered_transactions if t.transaction_type == 'expense')
    income_count = sum(1 for t in all_filtered_transactions if t.transaction_type == 'income')

    # --- Pagination (only for display list) ---
    pagination = query.order_by(Transaction.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # --- All user categories (for dropdown filter, not filtered set) ---
    all_user_categories = db.session.query(Transaction.category).filter_by(
        user_id=current_user.id
    ).distinct().all()
    categories = sorted([c[0] for c in all_user_categories if c[0]])

    # --- Category Breakdown (only expenses) ---
    category_breakdown = {}
    for t in all_filtered_transactions:
        if t.transaction_type == 'expense':
            cat = t.category or 'Uncategorized'  # Handle None categories
            if cat not in category_breakdown:
                category_breakdown[cat] = {'amount': 0, 'count': 0}
            category_breakdown[cat]['amount'] += t.amount
            category_breakdown[cat]['count'] += 1

    # Sort category breakdown by amount (highest first)
    category_breakdown = dict(sorted(category_breakdown.items(), 
                                   key=lambda x: x[1]['amount'], 
                                   reverse=True))

    # --- Render ---
    return render_template(
        'transactions.html',
        transactions=pagination.items,
        pagination=pagination,
        total_spending=total_spending,
        total_income=total_income,
        avg_per_day=avg_per_day,
        expense_count=expense_count,
        income_count=income_count,
        days_range=days_range,
        total_count=total_count,
        categories=categories,
        category_breakdown=category_breakdown,
        selected_category=category,
        selected_date_from=date_from,
        selected_date_to=date_to,
    )

@app.route('/transaction/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    """Edit a transaction"""
    transaction = Transaction.query.get_or_404(id)
    
    if transaction.user_id != current_user.id:
        flash('You do not have permission to edit this transaction.', 'danger')
        return redirect(url_for('transactions'))
    
    if request.method == 'POST':
        try:
            transaction.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            transaction.description = request.form.get('description', '').strip()
            transaction.amount = float(request.form.get('amount', 0))
            transaction.category = request.form.get('category', 'Others')
            transaction.transaction_type = request.form.get('type', 'expense')
            
            db.session.commit()
            flash('Transaction updated successfully!', 'success')
            return redirect(url_for('transactions'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating transaction: {str(e)}', 'danger')
            print(f"Edit transaction error: {e}")
    
    categories = [
        'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
        'Utilities', 'Healthcare', 'Groceries', 'Education', 
        'Investment', 'Transfer', 'Others'
    ]
    
    return render_template('edit_transaction.html', 
                         transaction=transaction,
                         categories=categories)

@app.route('/delete_transaction/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    """Delete a transaction"""
    transaction = Transaction.query.get_or_404(id)
    
    if transaction.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('transactions'))
    
    try:
        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting transaction', 'danger')
        print(f"Delete error: {e}")
    
    return redirect(url_for('transactions'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload CSV file"""
    if request.method == 'POST':
        try:
            if not request.files:
                return jsonify({'success': False, 'error': 'No file provided'}), 400
            
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file uploaded'}), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            if not file.filename.lower().endswith('.csv'):
                return jsonify({'success': False, 'error': 'Please upload a CSV file'}), 400
            
            # Save file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{current_user.id}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            
            # Process CSV
            processor = DataProcessor()
            transactions = processor.process_csv(filepath)
            
            if not transactions:
                os.remove(filepath)
                return jsonify({
                    'success': False, 
                    'error': 'No valid transactions found. Please check your CSV format.'
                }), 400
            
            # Save transactions
            count = 0
            skipped = 0
            
            for trans_data in transactions:
                existing = Transaction.query.filter_by(
                    user_id=current_user.id,
                    date=trans_data['date'],
                    amount=trans_data['amount'],
                    description=trans_data['description']
                ).first()
                
                if not existing:
                    transaction = Transaction(
                        user_id=current_user.id,
                        date=trans_data['date'],
                        description=trans_data['description'],
                        amount=trans_data['amount'],
                        category=trans_data['category'],
                        transaction_type=trans_data.get('type', 'expense')
                    )
                    db.session.add(transaction)
                    count += 1
                else:
                    skipped += 1
            
            db.session.commit()
            os.remove(filepath)
            
            message = f'Successfully imported {count} transactions'
            if skipped > 0:
                message += f' ({skipped} duplicates skipped)'
            
            return jsonify({
                'success': True,
                'message': message,
                'count': count,
                'skipped': skipped,
                'total': len(transactions)
            }), 200
            
        except Exception as e:
            db.session.rollback()
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'success': False, 
                'error': f'Processing error: {str(e)}'
            }), 500
    
    return render_template('upload.html')

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        total_transactions = Transaction.query.filter_by(user_id=current_user.id).count()
        
        transactions = Transaction.query.filter_by(user_id=current_user.id).all()
        total_spending = sum(t.amount for t in transactions if t.transaction_type == 'expense')
        total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
        
        member_since = current_user.created_at.strftime('%B %Y') if current_user.created_at else 'N/A'
        
        return render_template('profile.html',
                             user=current_user,
                             total_transactions=total_transactions,
                             total_spending=total_spending,
                             total_income=total_income,
                             member_since=member_since)
    except Exception as e:
        print(f"Profile error: {e}")
        flash('Error loading profile', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    try:
        return render_template('settings.html',
                             currency=session.get('currency_display', 'INR'),
                             date_format=session.get('date_format', 'DD/MM/YYYY'))
    except Exception as e:
        print(f"Settings error: {e}")
        flash('Error loading settings', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    """Manage budgets"""
    if request.method == 'POST':
        try:
            category = request.form.get('category')
            amount = float(request.form.get('amount', 0))
            month = request.form.get('month', datetime.now().strftime('%Y-%m'))
            
            if amount <= 0:
                flash('Please enter a valid amount', 'danger')
                return redirect(url_for('budgets'))
            
            budget = Budget.query.filter_by(
                user_id=current_user.id,
                category=category,
                month=month
            ).first()
            
            if budget:
                budget.amount = amount
                flash('Budget updated successfully', 'success')
            else:
                budget = Budget(
                    user_id=current_user.id,
                    category=category,
                    amount=amount,
                    month=month
                )
                db.session.add(budget)
                flash('Budget created successfully', 'success')
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            flash('Error saving budget', 'danger')
            print(f"Budget error: {e}")
        
        return redirect(url_for('budgets'))
    
    # GET request
    current_month = datetime.now().strftime('%Y-%m')
    user_budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=current_month
    ).all()
    
    budget_status = []
    month_start = datetime.now().replace(day=1)
    
    for budget in user_budgets:
        spending = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category == budget.category,
            Transaction.date >= month_start.date(),
            Transaction.transaction_type == 'expense'
        ).scalar() or 0
        
        budget_status.append({
            'id': budget.id,
            'category': budget.category,
            'budget': budget.amount,
            'spent': spending,
            'remaining': budget.amount - spending,
            'percentage': min((spending / budget.amount * 100) if budget.amount > 0 else 0, 100)
        })
    
    categories = [
        'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
        'Utilities', 'Healthcare', 'Groceries', 'Education', 'Others'
    ]
    
    return render_template('budgets.html',
                         budgets=budget_status,
                         categories=categories,
                         current_month=current_month)

@app.route('/budget/delete/<int:id>', methods=['POST'])
@login_required
def delete_budget(id):
    """Delete a budget"""
    budget = Budget.query.get_or_404(id)
    
    if budget.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('budgets'))
    
    try:
        db.session.delete(budget)
        db.session.commit()
        flash('Budget deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting budget', 'danger')
        print(f"Delete budget error: {e}")
    
    return redirect(url_for('budgets'))

@app.route('/budget/edit/<int:id>', methods=['POST'])
@login_required
def edit_budget(id):
    """Edit a budget"""
    budget = Budget.query.get_or_404(id)
    
    if budget.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('budgets'))
    
    try:
        budget.amount = float(request.form.get('amount', 0))
        db.session.commit()
        flash('Budget updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating budget', 'danger')
        print(f"Edit budget error: {e}")
    
    return redirect(url_for('budgets'))

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    """Generate spending predictions using LSTM if available"""
    try:
        # Get transactions from last 90 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        
        transactions = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).order_by(Transaction.date.asc()).all()

        print(f"🔍 Found {len(transactions)} expense transactions for prediction")

        if len(transactions) < 3:
            return jsonify({
                'success': False,
                'error': 'Need at least 3 days of transaction history for predictions'
            }), 400

        # Convert transactions to DataFrame for predictor
        df = pd.DataFrame([{
            'date': t.date,
            'amount': float(t.amount)  # Ensure float conversion
        } for t in transactions])

        print(f"📊 DataFrame created with {len(df)} records")
        print(f"📅 Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"💰 Total amount: ₹{df['amount'].sum():,.2f}")

        # Initialize predictor
        predictor = LSTMPredictor(model_path='models/lstm_model.h5')

        # Get predictions
        result = predictor.predict_spending(df, days=30)

        if not result:
            return jsonify({
                'success': False,
                'error': 'Prediction failed - no result returned'
            }), 500

        # Validate and clean the result
        daily_avg = float(result.get('daily_average', 0))
        total_pred = float(result.get('total_predicted', daily_avg * 30))
        confidence = float(result.get('confidence', 50.0))
        
        # Ensure total is calculated correctly
        if total_pred <= 0 and daily_avg > 0:
            total_pred = daily_avg * 30
        
        # Clean result
        clean_result = {
            'daily_average': daily_avg,
            'total_predicted': total_pred,
            'confidence': confidence,
            'confidence_level': result.get('confidence_level', 'medium'),
            'method': result.get('method', 'statistical'),
            'predictions': result.get('predictions', [daily_avg] * 30),
            'data_points_used': len(transactions),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
        
        # Enhanced message
        if clean_result['method'] == 'lstm':
            clean_result['message'] = "Predictions powered by LSTM neural network"
        elif clean_result['method'] == 'statistical':
            clean_result['message'] = "Predictions using statistical analysis with trend recognition"
        else:
            clean_result['message'] = "Predictions using historical average"

        print(f"✅ Sending clean result: Daily=₹{daily_avg:.2f}, Total=₹{total_pred:.2f}, Confidence={confidence:.1f}%")

        return jsonify({
            'success': True,
            'predictions': clean_result
        })
    
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/reports')
@login_required
def reports():
    """Reports page"""
    return render_template('reports.html', 
                         current_month=datetime.now().strftime('%Y-%m'),
                         current_year=datetime.now().year)

@app.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    """Generate PDF report"""
    if not HAS_REPORTLAB:
        flash('PDF generation is not available. Please install reportlab.', 'warning')
        return redirect(url_for('reports'))
    
    try:
        # Register a Unicode font that definitely supports ₹
        font_registered = False
        unicode_font_name = 'UnicodeFont'

        # Prefer project-bundled fonts; avoid Arial (no ₹) and flaky Windows font access
        possible_font_paths = [
            os.path.join(r'C:\Users\tirth\OneDrive\Desktop\ZORO\BudgetWiseAI\static', 'fonts', 'NotoSans-Regular.ttf'),
            os.path.join(app.root_path, 'static', 'fonts', 'NotoSans-Regular.ttf'),
            # Common Linux/Mac installs
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/Library/Fonts/DejaVuSans.ttf',
            # Windows (Segoe UI includes ₹)
            r'C:\Windows\Fonts\segoeui.ttf',
            # If you've actually placed this file in Windows Fonts
            r'C:\Windows\Fonts\NotoSans-Regular.ttf',
        ]

        chosen_font_path = None
        for font_path in possible_font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(unicode_font_name, font_path))
                    font_registered = True
                    chosen_font_path = font_path
                    print(f"[PDF] Registered Unicode font: {font_path}")
                    break
                except Exception as e:
                    print(f"[PDF] Failed to register font {font_path}: {e}")

        # If no Unicode font found, use Rs. instead of ₹ to avoid tofu boxes
        currency_symbol = '₹' if font_registered else 'Rs.'

        report_type = request.form.get('report_type', 'monthly')
        month = request.form.get('month', datetime.now().strftime('%Y-%m'))

        if report_type == 'monthly':
            year, month_num = map(int, month.split('-'))
            start_date = datetime(year, month_num, 1).date()
            if month_num == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month_num + 1, 1).date() - timedelta(days=1)
        elif report_type == 'yearly':
            year = int(request.form.get('year', datetime.now().year))
            start_date = datetime(year, 1, 1).date()
            end_date = datetime(year, 12, 31).date()
        else:
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()

        transactions = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).order_by(Transaction.date.desc()).all()

        if not transactions:
            flash('No transactions found for the selected period', 'warning')
            return redirect(url_for('reports'))

        # Calculate statistics
        total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
        total_expense = sum(t.amount for t in transactions if t.transaction_type == 'expense')
        net_savings = total_income - total_expense

        # Category breakdown
        category_expenses = {}
        for t in transactions:
            if t.transaction_type == 'expense':
                category_expenses[t.category] = category_expenses.get(t.category, 0) + t.amount

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Force Unicode font on all styles if registered
        if font_registered:
            for style_name, style in styles.byName.items():
                style.fontName = unicode_font_name

        # Title style (no conditional fallback here; we avoid mixing fonts)
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=unicode_font_name if font_registered else 'Helvetica-Bold'
        )

        # Build PDF content
        story.append(Paragraph(f"Financial Report - {current_user.username}", title_style))
        story.append(Spacer(1, 20))

        period_text = f"Report Period: {start_date.strftime('%d %B %Y')} to {end_date.strftime('%d %B %Y')}"
        story.append(Paragraph(period_text, styles['Normal']))
        story.append(Spacer(1, 20))

        # Summary table with proper currency formatting
        summary_data = [
            ['Summary', f'Amount ({currency_symbol})'],
            ['Total Income', f'{currency_symbol}{total_income:,.2f}'],
            ['Total Expenses', f'{currency_symbol}{total_expense:,.2f}'],
            ['Net Savings', f'{currency_symbol}{net_savings:,.2f}'],
            ['Number of Transactions', str(len(transactions))]
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])

        # Summary table style (fresh style object)
        summary_table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, -1), unicode_font_name if font_registered else 'Helvetica'),
        ])
        summary_table.setStyle(summary_table_style)
        story.append(summary_table)

        # Add category breakdown if expenses exist
        if category_expenses:
            story.append(Spacer(1, 30))
            # Ensure Heading2 uses the right font
            heading2_style = ParagraphStyle(
                'Heading2Unicode',
                parent=styles['Heading2'],
                fontName=unicode_font_name if font_registered else styles['Heading2'].fontName
            )
            story.append(Paragraph("Expense Breakdown by Category", heading2_style))
            story.append(Spacer(1, 10))

            category_data = [['Category', f'Amount ({currency_symbol})', 'Percentage']]
            for category, amount in sorted(category_expenses.items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                category_data.append([
                    category.title(),
                    f'{currency_symbol}{amount:,.2f}',
                    f'{percentage:.1f}%'
                ])

            category_table = Table(category_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])

            # Category table style (separate style object)
            category_table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('FONTNAME', (0, 0), (-1, -1), unicode_font_name if font_registered else 'Helvetica'),
            ])
            category_table.setStyle(category_table_style)
            story.append(category_table)

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        filename = f"Financial_Report_{current_user.username}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        if chosen_font_path:
            print(f"[PDF] Using font: {chosen_font_path}")
        else:
            print("[PDF] No Unicode font found. Falling back to Rs. and Helvetica to avoid tofu boxes.")

        return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

    except Exception as e:
        print(f"Report generation error: {e}")
        import traceback
        traceback.print_exc()
        flash('Error generating report. Please try again.', 'danger')
        return redirect(url_for('reports'))
        
# ============= API ENDPOINTS =============

@app.route('/api/dashboard_data')
@login_required
def api_dashboard_data():
    """API endpoint for dashboard data"""
    try:
        days = request.args.get('days', 30, type=int)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        transactions = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        daily_data = {}
        for t in transactions:
            if t.transaction_type == 'expense':
                date_str = t.date.strftime('%Y-%m-%d')
                if date_str not in daily_data:
                    daily_data[date_str] = 0
                daily_data[date_str] += t.amount
        
        categories = {}
        for t in transactions:
            if t.transaction_type == 'expense':
                if t.category not in categories:
                    categories[t.category] = 0
                categories[t.category] += t.amount
        
        return jsonify({
            'success': True,
            'daily_spending': daily_data,
            'categories': categories,
            'total_spending': sum(categories.values()),
            'transaction_count': len(transactions)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/add_transaction', methods=['POST'])
@login_required
def api_add_transaction():
    """API endpoint for adding transaction"""
    try:
        data = request.get_json()
        
        transaction = Transaction(
            user_id=current_user.id,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            description=data['description'],
            amount=float(data['amount']),
            category=data.get('category', 'Others'),
            transaction_type=data.get('type', 'expense')
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Transaction added successfully',
            'transaction': transaction.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_transactions')
@login_required
def export_transactions():
    """Export transactions as CSV"""
    try:
        transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                      .order_by(Transaction.date.desc()).all()
        
        data = []
        for t in transactions:
            data.append({
                'Date': t.date.strftime('%Y-%m-%d'),
                'Description': t.description,
                'Amount': t.amount,
                'Category': t.category,
                'Type': t.transaction_type
            })
        
        df = pd.DataFrame(data)
        
        filename = f'transactions_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        df.to_csv(filepath, index=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        flash('Error exporting transactions', 'danger')
        print(f"Export error: {e}")
        return redirect(url_for('transactions'))

@app.route('/api/save_settings', methods=['POST'])
@login_required
def api_save_settings():
    """Save user settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        session['currency_display'] = data.get('currency', 'INR')
        session['date_format'] = data.get('date_format', 'DD/MM/YYYY')
        
        return jsonify({
            'success': True,
            'message': 'Settings saved successfully',
            'settings': {
                'currency': session.get('currency_display', 'INR'),
                'date_format': session.get('date_format', 'DD/MM/YYYY')
            }
        })
        
    except Exception as e:
        print(f"Settings error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_settings', methods=['GET'])
@login_required
def api_get_settings():
    """Get user settings"""
    try:
        settings = {
            'currency': session.get('currency_display', 'INR'),
            'date_format': session.get('date_format', 'DD/MM/YYYY'),
            'theme': session.get('theme', 'light')
        }
        
        return jsonify({
            'success': True,
            'settings': settings
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

# ============= MAIN EXECUTION =============

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 BudgetWise AI - Starting Application")
    print("=" * 50)
    
    # Initialize database
    init_database()
    
    print("\n✨ Application ready!")
    print("📍 URL: http://localhost:5000")
    print("📍 Press Ctrl+C to stop")
    print("-" * 50)
    
    # Run application
    app.run(debug=True, port=5000, use_reloader=False)
