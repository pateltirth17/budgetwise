# BudgetWise: AI-based Expense Forecasting Tool

A comprehensive web application for personal finance management with AI-powered spending predictions using LSTM neural networks.

## Features

- 📊 **Dashboard**: Real-time financial overview with interactive charts
- 💰 **Transaction Management**: Add, edit, and categorize transactions
- 📈 **AI Predictions**: LSTM-based spending predictions
- 💼 **Budget Planning**: Set and track budgets by category
- 📁 **CSV Import/Export**: Bulk transaction upload via CSV
- 🔐 **User Authentication**: Secure login and registration system
- 📧 **Email Notifications**: Password reset functionality
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Machine Learning**: TensorFlow/Keras (LSTM)
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Chart.js
- **Authentication**: Flask-Login
- **Email**: Flask-Mail

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/budgetwise.git
cd budgetwise
```

2. **Create a virtual environment**
```bash
python -m venv venv
```

3. **Activate the virtual environment**
- Windows:
```bash
venv\Scripts\activate
```
- Mac/Linux:
```bash
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Set up environment variables**
Create a `.env` file in the root directory:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/budgetwise.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

6. **Initialize the database**
```bash
python fix_database.py
python check_and_populate_db.py
```

7. **Train the ML model (optional)**
```bash
python train_model.py
```

8. **Run the application**
```bash
python run.py
```

The application will be available at `http://localhost:5000`


## Usage

### 1. User Registration
- Navigate to `/signup`
- Create a new account with email and password

### 2. Adding Transactions
- Go to Dashboard → Add Transaction
- Enter transaction details (amount, category, date, description)
- Save transaction

### 3. Importing Transactions
- Prepare CSV file with columns: date, description, amount, category
- Go to Upload page
- Select and upload your CSV file

### 4. Viewing Reports
- Navigate to Reports section
- View spending trends and category breakdowns
- Export reports as needed

### 5. Budget Management
- Set monthly budgets for different categories
- Track spending against budgets
- Receive alerts when approaching limits

## API Endpoints

- `GET /` - Landing page
- `GET /dashboard` - User dashboard
- `GET /transactions` - View transactions
- `POST /add_transaction` - Add new transaction
- `GET /reports` - Financial reports
- `POST /upload` - Upload CSV file
- `GET /api/predictions` - Get spending predictions

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Or run specific test files:
```bash
python test_app.py
python test_transactions_route.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@budgetwise.com or create an issue in the GitHub repository.

## Acknowledgments

- Flask documentation
- TensorFlow/Keras community
- Chart.js for data visualization

