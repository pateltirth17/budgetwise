"""
Run script for BudgetWise AI
Simple script to start the application
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    print("🔍 Checking requirements...")
    
    try:
        import flask
        import tensorflow
        import pandas
        import numpy
        print("✅ All core packages installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("\n📦 Please install requirements:")
        print("   pip install -r requirements.txt")
        return False

def check_model():
    """Check if LSTM model exists"""
    model_path = Path("models/lstm_model.h5")
    
    if not model_path.exists():
        print("\n⚠️  LSTM model not found!")
        print("🤖 Training initial model...")
        print("   This is a one-time process (takes 2-3 minutes)")
        
        os.system("python train_model.py")
        
        if model_path.exists():
            print("✅ Model trained successfully!")
            return True
        else:
            print("❌ Model training failed")
            return False
    
    print("✅ LSTM model found")
    return True

def check_database():
    """Check if database exists"""
    try:
        from app import app, db
        
        with app.app_context():
            db.create_all()
            print("✅ Database ready")
            return True
    except AttributeError as e:
        # Handle Flask 2.3+ compatibility
        if "before_first_request" in str(e):
            print("⚠️  Fixing Flask 2.3+ compatibility...")
            # Database will be created when app runs
            return True
        else:
            print(f"❌ Database error: {e}")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main function to run the application"""
    print("=" * 50)
    print("🚀 BudgetWise AI - Starting Application")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check model
    if not check_model():
        print("\n💡 Tip: You can train the model manually:")
        print("   python train_model.py")
        sys.exit(1)
    
    # Check database
    if not check_database():
        sys.exit(1)
    
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("static/images", exist_ok=True)
    
    print("\n" + "=" * 50)
    print("✨ All checks passed! Starting server...")
    print("=" * 50)
    
    # Run the application
    from app import app
    
    print("\n🌐 Opening BudgetWise AI...")
    print("📍 URL: http://localhost:5000")
    print("📍 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Open browser automatically
    import webbrowser
    import threading
    import time
    
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:5000')
    
    threading.Thread(target=open_browser).start()
    
    # Run Flask app
    app.run(debug=True, port=5000, use_reloader=False)

if __name__ == "__main__":
    main()