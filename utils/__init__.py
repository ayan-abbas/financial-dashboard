# utils/__init__.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json

# Initialize Firebase
cred = credentials.Certificate("firebase-key.json")
firebase_app = firebase_admin.initialize_app(cred)
db = firestore.client()

def get_db():
    return db
