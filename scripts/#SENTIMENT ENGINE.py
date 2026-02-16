#SENTIMENT ENGINE
from textblob import TextBlob

def sentiment_score(text):
    score = TextBlob(text).sentiment.polarity
    if score > 0.5:
        strength = "strong"
    elif score > 0.1:
        strength = "moderate"
    else:
        strength = "weak"
    return score, strength