"""
Utils package for BudgetWise AI
"""

# Try to import modules, but don't fail if they don't exist
try:
    from .data_processor import DataProcessor
except ImportError:
    DataProcessor = None

try:
    from .predictor import LSTMPredictor
except ImportError:
    LSTMPredictor = None

try:
    from .model_trainer import ModelTrainer
except ImportError:
    ModelTrainer = None

try:
    from .database import DatabaseManager
except ImportError:
    DatabaseManager = None

__all__ = ['DataProcessor', 'LSTMPredictor', 'ModelTrainer', 'DatabaseManager']
