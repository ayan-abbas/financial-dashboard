# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import firebase_admin
from firebase_admin import auth, firestore
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
import nltk 
from datetime import datetime

from utils.news_fetcher import FinnhubNewsFetcher
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.summarizer import ArticleSummarizer
from config import FINNHUB_API_KEY, FIREBASE_CONFIG

# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')

# Initialize services
news_fetcher = FinnhubNewsFetcher(api_key=FINNHUB_API_KEY)
sentiment_analyzer = SentimentAnalyzer()
summarizer = ArticleSummarizer()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize Firebase
try:
    firebase_admin.get_app()
except ValueError:
    cred = firebase_admin.credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Initialize services
sentiment_analyzer = SentimentAnalyzer()
summarizer = ArticleSummarizer()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Authenticate with Firebase
            user = auth.get_user_by_email(email)
            # In a real app, you would verify the password with Firebase Auth
            # This is simplified for demonstration
            
            session['user_id'] = user.uid
            session['user_email'] = email  # Store email for later use
            
            # Check if user preferences document exists, create if not
            user_doc_ref = db.collection('user_preferences').document(user.uid)
            doc = user_doc_ref.get()
            
            if not doc.exists:
                # Create user preferences document if it doesn't exist
                user_doc_ref.set({
                    'email': email,
                    'interests': []
                })
            
            flash('Logged in successfully', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'danger')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Create user in Firebase
            user = auth.create_user(
                email=email,
                password=password
            )
            
            # Create user preferences document
            db.collection('user_preferences').document(user.uid).set({
                'email': email,
                'interests': []
            })
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('login.html', register=True)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get page parameter for pagination, default to 1
    page = request.args.get('page', 1, type=int)
    
    # Get date range parameter (default to past week)
    days_back = request.args.get('days_back', 7, type=int)
    
    user_id = session['user_id']
    
    # Get user preferences
    try:
        # Ensure NLTK resources are downloaded
        try:
            nltk.download('punkt_tab')
        except:
            pass
            
        user_doc = db.collection('user_preferences').document(user_id).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            interests = user_data.get('interests', [])
            
            # If user has interests, fetch news
            if interests:
                # Set articles per page - showing 10 articles per page
                per_page = 10
                
                # Fetch news with pagination using Finnhub
                news_data = news_fetcher.fetch_news(
                    interests, 
                    limit=per_page,
                    page=page,
                    days_back=days_back
                )
                
                # Process each news article
                processed_news = []
                for article in news_data:
                    try:
                        # Extract article content
                        content, image_url = summarizer.fetch_article_content(article.get('url', ''))
                        
                        # Get sentiment from article content
                        content_sentiment = sentiment_analyzer.analyze(content)
                        
                        # Try to get symbol-specific sentiment if available
                        symbol = article.get('symbol', '')
                        if symbol:
                            symbol_sentiment = news_fetcher.fetch_sentiment(symbol)
                            if symbol_sentiment and 'sentiment' in symbol_sentiment:
                                # Use Finnhub's sentiment score if available
                                sentiment_score = symbol_sentiment.get('sentiment', {}).get('bullishPercent', 0.5)
                                if sentiment_score > 0.6:
                                    sentiment_label = "Positive"
                                elif sentiment_score < 0.4:
                                    sentiment_label = "Negative"
                                else:
                                    sentiment_label = "Neutral"
                                    
                                sentiment = {
                                    "score": sentiment_score,
                                    "label": sentiment_label
                                }
                            else:
                                sentiment = content_sentiment
                        else:
                            sentiment = content_sentiment
                        
                        # Generate summary
                        try:
                            summary = summarizer.summarize(content)
                        except Exception as e:
                            # Fallback summary
                            summary = article.get('summary', '')
                            if not summary and content:
                                if len(content) > 200:
                                    summary = content[:197] + "..."
                                else:
                                    summary = content
                        
                        # Get publisher name
                        publisher = article.get('source', {})
                        if isinstance(publisher, dict):
                            publisher = publisher.get('name', 'Unknown')
                        
                        # Format datetime properly
                        try:
                            dt = datetime.fromtimestamp(article.get('datetime', 0))
                            published_at = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            published_at = article.get('published_at', '')
                        
                        processed_article = {
                            'title': article.get('title', 'No Title'),
                            'url': article.get('url', '#'),
                            'image_url': image_url or article.get('image_url', '') or article.get('image', ''),
                            'publisher': publisher,
                            'sentiment': sentiment,
                            'summary': summary,
                            'published_at': published_at
                        }
                        
                        processed_news.append(processed_article)
                    except Exception as e:
                        print(f"Error processing article: {e}")
                        continue
                
                # Determine if there are more articles to load
                # Since Finnhub might not have perfect pagination, we'll say there are more if we got at least per_page articles
                has_more = len(news_data) >= per_page
                
                return render_template(
                    'dashboard.html', 
                    news=processed_news, 
                    interests=interests,
                    page=page,
                    days_back=days_back,
                    has_more=has_more
                )
            else:
                # No interests set
                flash('Please set your financial interests to see personalized news.', 'info')
                return render_template('preferences.html')
        else:
            # User preferences not found, create them
            db.collection('user_preferences').document(user_id).set({
                'email': session.get('user_email', ''),
                'interests': []
            })
            flash('Please set your financial interests to see personalized news.', 'info')
            return render_template('preferences.html')
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Dashboard error: {error_details}")
        flash(f"Error loading dashboard: {str(e)}", 'danger')
        return render_template('dashboard.html', news=[], interests=[])






@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        # Get interests from form
        interests = request.form.get('interests', '').split(',')
        interests = [interest.strip().upper() for interest in interests if interest.strip()]
        
        # Check if document exists first
        user_doc_ref = db.collection('user_preferences').document(user_id)
        doc = user_doc_ref.get()
        
        if doc.exists:
            # Update existing document
            user_doc_ref.update({
                'interests': interests
            })
        else:
            # Create new document if it doesn't exist
            user_doc_ref.set({
                'email': session.get('user_email', ''),
                'interests': interests
            })
        
        flash('Preferences updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get current preferences
    user_doc = db.collection('user_preferences').document(user_id).get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        interests = user_data.get('interests', [])
        return render_template('preferences.html', interests=interests)
    else:
        return render_template('preferences.html', interests=[])


if __name__ == '__main__':
    app.run(debug=True)
