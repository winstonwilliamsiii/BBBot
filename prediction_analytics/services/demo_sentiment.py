"""Simplified sentiment engine using TextBlob for Demo_Bots testing."""
from textblob import TextBlob

def sentiment_score(text):
    """Calculate sentiment score and strength from text using TextBlob."""
    score = TextBlob(text).sentiment.polarity
    
    if score > 0.5:
        strength = "strong"
    elif score > 0.1:
        strength = "moderate"
    else:
        strength = "weak"
    
    return score, strength
