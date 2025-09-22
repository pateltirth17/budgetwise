import os

def fix_model_files():
    """Remove problematic LSTM model files"""
    model_files = [
        'models/lstm_model.h5',
        'models/lstm_model_scaler.pkl'
    ]
    
    for file_path in model_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Removed {file_path}")
            except Exception as e:
                print(f"❌ Could not remove {file_path}: {e}")
        else:
            print(f"ℹ️ {file_path} does not exist")
    
    print("\n🔄 Now the predictor will use only statistical methods")
    print("📊 This should give more realistic predictions")

if __name__ == '__main__':
    fix_model_files()