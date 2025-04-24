# utils/sentiment_analyzer.py
from textblob import TextBlob

class SentimentAnalyzer:
    def analyze(self, text):
        """
        Analyze the sentiment of the given text.
        Returns: dict with sentiment polarity (-1 to 1) and label
        """
        if not text:
            return {"score": 0, "label": "Neutral"}
        
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        # Determine sentiment label based on polarity
        if polarity > 0.1:
            label = "Positive"
        elif polarity < -0.1:
            label = "Negative"
        else:
            label = "Neutral"
            
        return {
            "score": polarity,
            "label": label
        }
