# utils/news_fetcher.py
import finnhub
import os
from datetime import datetime, timedelta
import pandas as pd

class FinnhubNewsFetcher:
    def __init__(self, api_key):
        self.client = finnhub.Client(api_key=api_key)
    
    def fetch_news(self, symbols, limit=10, page=1, days_back=7):
        """
        Fetch company news for the given symbols
        
        Parameters:
        - symbols: List of stock symbols/keywords
        - limit: Number of articles to fetch per symbol
        - page: Page number for pagination
        - days_back: Number of days to look back for news
        
        Returns:
        - List of news articles with consistent format
        """
        all_news = []
        
        # Calculate date range (past week by default)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Skip items based on pagination
        skip = (page - 1) * limit
        
        # For each symbol, fetch news
        for symbol in symbols:
            try:
                # Clean up symbol if needed (remove spaces, etc.)
                clean_symbol = symbol.strip().upper()
                
                # Skip non-stock symbols or broad keywords
                if len(clean_symbol) > 5 or clean_symbol.lower() in ['cryptocurrency', 'bitcoin']:
                    continue
                
                # Get news for this symbol
                company_news = self.client.company_news(
                    clean_symbol, 
                    _from=start_date,
                    to=end_date
                )
                
                if company_news:
                    # Add symbol and source information to each news item
                    for news in company_news:
                        news['symbol'] = clean_symbol
                        
                        # Ensure consistent format
                        if 'image' not in news or not news['image']:
                            news['image'] = news.get('image_url', '')
                        
                        # Map Finnhub structure to expected structure
                        news['title'] = news.get('headline', 'No Title')
                        news['url'] = news.get('url', '#')
                        news['image_url'] = news.get('image', '')
                        news['source'] = {'name': news.get('source', 'Unknown')}
                        news['published_at'] = news.get('datetime', '')
                        
                    all_news.extend(company_news)
            except Exception as e:
                print(f"Error fetching news for {symbol}: {e}")
        
        # Sort by date (newest first)
        all_news = sorted(all_news, key=lambda x: x.get('datetime', 0), reverse=True)
        
        # Apply pagination
        paginated_news = all_news[skip:skip+limit]
        
        return paginated_news
    
    def fetch_sentiment(self, symbol):
        """
        Fetch sentiment analysis for a specific symbol
        
        Parameters:
        - symbol: Stock symbol to get sentiment for
        
        Returns:
        - Sentiment data dictionary
        """
        try:
            sentiment = self.client.news_sentiment(symbol)
            return sentiment
        except Exception as e:
            print(f"Error fetching sentiment for {symbol}: {e}")
            return None
