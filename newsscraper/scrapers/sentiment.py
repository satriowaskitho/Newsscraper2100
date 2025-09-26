# sentiment_id.py
from deep_translator import GoogleTranslator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def _translate(text: str) -> str:
    """Translate Indonesian -> English (stable)."""
    return GoogleTranslator(source="id", target="en").translate(text)

def classify_sentiment_id(text_id: str) -> str:
    """
    Classify Indonesian text into: 'positif', 'negatif', or 'netral'
    using Deep Translator + VADER.
    """
    try:
        translated = _translate(text_id)
        scores = analyzer.polarity_scores(translated)
        compound = scores["compound"]

        if compound >= 0.05:
            return "positif"
        elif compound <= -0.05:
            return "negatif"
        else:
            return "netral"

    except Exception as e:
        return f"error: {e}"
