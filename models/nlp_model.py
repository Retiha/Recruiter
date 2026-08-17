"""NLP Model loader, entity recognition engine, and text processing utilities."""
import logging
import re
from typing import List, Tuple, Set, Optional, Dict, Any

logger = logging.getLogger("ai_recruiter.nlp")

# Common English stop words for fast filtering when spaCy isn't loaded
DEFAULT_STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
    "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves",
    "etc", "eg", "ie", "also", "including", "using", "work", "experience", "resume", "cv", "page"
}

# Pre-compiled Regex Patterns for High Precision
EMAIL_REGEX = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

PHONE_REGEX = re.compile(
    r'(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?|\+?\d{1,4}[-.\s]?(?:\(?\d{1,4}\)?[-.\s]?)?\d{2,5}[-.\s]?\d{3,5}',
    re.IGNORECASE
)

URL_REGEX = re.compile(
    r'https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)',
    re.IGNORECASE
)

LINKEDIN_REGEX = re.compile(
    r'(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_-]+)',
    re.IGNORECASE
)

GITHUB_REGEX = re.compile(
    r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)',
    re.IGNORECASE
)


class NLPEngine:
    """Singleton NLP Engine with spaCy support and resilient fallbacks."""
    _instance = None
    _nlp = None
    _is_spacy_loaded = False
    _spacy_model_name = "en_core_web_sm"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NLPEngine, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Attempts to load spaCy model, with safe fallbacks."""
        try:
            import spacy
            try:
                self._nlp = spacy.load(self._spacy_model_name)
                self._is_spacy_loaded = True
                logger.info(f"Loaded spaCy model: {self._spacy_model_name}")
            except Exception:
                try:
                    # Attempt blank English model
                    self._nlp = spacy.blank("en")
                    if "sentencizer" not in self._nlp.pipe_names:
                        self._nlp.add_pipe("sentencizer")
                    self._is_spacy_loaded = True
                    logger.info("Loaded spaCy blank 'en' model with sentencizer.")
                except Exception as e:
                    self._nlp = None
                    self._is_spacy_loaded = False
                    logger.warning(f"spaCy load failed: {e}. Using native NLP fallback.")
        except ImportError:
            self._nlp = None
            self._is_spacy_loaded = False
            logger.info("spaCy not installed. Using native regex & scikit-learn NLP engine.")

    @property
    def is_spacy_available(self) -> bool:
        return self._is_spacy_loaded and self._nlp is not None

    def get_spacy_nlp(self):
        return self._nlp

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase alphanumeric tokens, filtering stop words."""
        if not text:
            return []
        if self.is_spacy_available:
            doc = self._nlp(text)
            return [
                token.text.lower()
                for token in doc
                if not token.is_stop and not token.is_punct and not token.is_space and len(token.text.strip()) > 1
            ]
        # Native fallback
        tokens = re.findall(r'\b[A-Za-z0-9_+#.-]+\b', text.lower())
        return [t for t in tokens if t not in DEFAULT_STOP_WORDS and len(t) > 1]

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if not text:
            return []
        if self.is_spacy_available:
            doc = self._nlp(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        # Native regex sentence boundary
        raw_sents = re.split(r'(?<=[.!?])\s+|\n+', text)
        return [s.strip() for s in raw_sents if len(s.strip()) > 5]

    def extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extract entities (text, label) using spaCy NER if available."""
        if not text or not self.is_spacy_available:
            return []
        try:
            doc = self._nlp(text)
            return [(ent.text.strip(), ent.label_) for ent in doc.ents]
        except Exception:
            return []

    def extract_keywords(self, text: str, top_n: int = 15) -> List[str]:
        """Extract dominant meaningful keywords from text using frequency & TF-IDF."""
        if not text or not text.strip():
            return []
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            # Clean text
            cleaned = re.sub(r'[^a-zA-Z0-9\s+#.-]', ' ', text.lower())
            
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=50
            )
            tfidf_matrix = vectorizer.fit_transform([cleaned])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Sort keywords by score
            scored_keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
            return [kw for kw, score in scored_keywords[:top_n] if len(kw) > 2]
        except Exception:
            # Fallback simple frequency count
            tokens = self.tokenize(text)
            freq: Dict[str, int] = {}
            for t in tokens:
                freq[t] = freq.get(t, 0) + 1
            sorted_tokens = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            return [t for t, count in sorted_tokens[:top_n]]


# Helper function to get global engine
def get_nlp_engine() -> NLPEngine:
    return NLPEngine()
