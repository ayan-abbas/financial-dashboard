# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

# Firebase Configuration
FIREBASE_CONFIG = {
    'apiKey': FIREBASE_API_KEY,
    'authDomain': 'your-project-id.firebaseapp.com',
    'projectId': 'your-project-id',
    'storageBucket': 'your-project-id.appspot.com',
    'messagingSenderId': 'your-messaging-sender-id',
    'appId': 'your-app-id',
    'databaseURL': 'https://your-project-id-default-rtdb.firebaseio.com'
}
