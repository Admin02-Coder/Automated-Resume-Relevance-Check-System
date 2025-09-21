import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///resume_relevance.db')
    CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', './data/embeddings')
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 10485760))
    
    # Scoring weights
    HARD_MATCH_WEIGHT = 0.4
    SEMANTIC_MATCH_WEIGHT = 0.4
    EXPERIENCE_WEIGHT = 0.2
    
    # Thresholds
    HIGH_RELEVANCE_THRESHOLD = 75
    MEDIUM_RELEVANCE_THRESHOLD = 50