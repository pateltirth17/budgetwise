from app import app
import requests
import json

def test_dashboard_predictions():
    with app.test_client() as client:
        # You'll need to login first - replace with your actual credentials
        login_data = {
            'email': 'your_email@example.com',  # Replace with your email
            'password': 'your_password'  # Replace with your password
        }
        
        # Login
        response = client.post('/login', data=login_data, follow_redirects=True)
        
        if b'Welcome' in response.data or response.status_code == 200:
            print("✅ Login successful")
            
            # Test prediction endpoint
            response = client.post('/predict')
            
            if response.status_code == 200:
                data = json.loads(response.data)
                print("✅ Prediction endpoint working")
                print(f"📊 Response: {json.dumps(data, indent=2)}")
            else:
                print(f"❌ Prediction failed: {response.status_code}")
                print(f"Response: {response.data.decode()}")
        else:
            print("❌ Login failed")
            print("Please update the login credentials in the script")

if __name__ == '__main__':
    test_dashboard_predictions()