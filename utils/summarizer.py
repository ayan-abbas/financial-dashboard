# utils/summarizer.py
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
from newspaper import Article
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')  # This was missing in your previous error

class ArticleSummarizer:  # Make sure this class name matches your import
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
    
    def fetch_article_content(self, url):
        """Extract article content and image from URL with enhanced image detection"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            image_url = article.top_image
            
            # If Newspaper3k couldn't find an image, try additional methods
            if not image_url:
                try:
                    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple image sources in order of preference
                    # 1. Open Graph image (often used for social sharing)
                    og_image = soup.find('meta', property='og:image')
                    if og_image and og_image.get('content'):
                        image_url = og_image.get('content')
                    
                    # 2. Twitter card image
                    elif soup.find('meta', {'name': 'twitter:image'}):
                        image_url = soup.find('meta', {'name': 'twitter:image'}).get('content')
                    
                    # 3. First large image in the article
                    elif soup.find('img'):
                        images = soup.find_all('img')
                        for img in images:
                            # Skip small images, icons, etc.
                            if img.get('width') and int(img.get('width')) > 300:
                                image_url = img.get('src')
                                if image_url and not image_url.startswith('http'):
                                    # Handle relative URLs
                                    parsed_url = urlparse(url)
                                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                    image_url = urljoin(base_url, image_url)
                                break
                except:
                    pass
            
            return article.text, image_url
        except Exception as e:
            print(f"Error extracting content: {e}")
            return "", ""

    
    def summarize(self, text, max_sentences=1):
        """Generate a summary of the given text"""
        if not text or len(text) < 100:
            return text
        
        # Tokenize sentences and words
        sentences = sent_tokenize(text)
        words = word_tokenize(text.lower())
        
        # Remove stopwords
        filtered_words = [word for word in words if word.isalnum() and word not in self.stop_words]
        
        # Calculate word frequencies
        word_frequencies = FreqDist(filtered_words)
        
        # Calculate sentence scores based on word frequencies
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_words = word_tokenize(sentence.lower())
            score = sum(word_frequencies[word] for word in sentence_words 
                      if word in word_frequencies)
            sentence_scores[i] = score
        
        # Get top sentences
        top_sentence_indices = sorted(sentence_scores.items(), 
                                    key=lambda x: x[1], reverse=True)[:max_sentences]
        top_sentence_indices = sorted([idx for idx, _ in top_sentence_indices])
        
        # Create summary
        summary = ' '.join([sentences[i] for i in top_sentence_indices])
        return summary
