# database.py
import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
import hashlib
import os
import streamlit as st
st.cache_data.clear()
st.cache_resource.clear()

# Replace the database initialization section with this:
# Initialize database connection - FORCE REFRESH
def init_database():
    """Initialize database connection (force refresh)"""
    return MarketResearchDB()

# Force create new database instance
if 'db_instance' not in st.session_state:
    st.session_state.db_instance = init_database()

db = st.session_state.db_instance

# Test if methods exist
try:
    # Test the problematic methods
    test_history = db.get_market_analysis_history(limit=1)
    test_pdf = db.get_pdf_sessions_summary(limit=1)
    st.success("✅ Database methods loaded successfully!")
except AttributeError as e:
    st.error(f"❌ Database method missing: {e}")
    st.info("🔄 Please restart the Streamlit app completely")
except Exception as e:
    st.info(f"📊 Database ready (empty): {e}")

class MarketResearchDB:
    def __init__(self, db_path: str = "market_research.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Market analysis cache
                CREATE TABLE IF NOT EXISTS market_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_name TEXT NOT NULL,
                    query_type TEXT NOT NULL, -- 'global', 'vertical', 'horizontal', 'metrics', 'companies'
                    query_hash TEXT UNIQUE NOT NULL,
                    result_data TEXT NOT NULL, -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    source TEXT -- 'openai', 'web_search', etc.
                );
                
                -- User sessions and queries
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    market_name TEXT,
                    query_type TEXT,
                    query_params TEXT, -- JSON string
                    result_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- PDF processing history
                CREATE TABLE IF NOT EXISTS pdf_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER,
                    total_pages INTEGER,
                    chunks_count INTEGER,
                    openai_file_ids TEXT, -- JSON array of file IDs
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'processed' -- 'processing', 'processed', 'error'
                );
                
                -- PDF Q&A history
                CREATE TABLE IF NOT EXISTS pdf_qa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_history_id INTEGER,
                    question TEXT NOT NULL,
                    answer TEXT,
                    query_tokens INTEGER,
                    response_tokens INTEGER,
                    cost_estimate REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pdf_history_id) REFERENCES pdf_history (id)
                );
                
                -- M&A search history
                CREATE TABLE IF NOT EXISTS ma_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_name TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    result_data TEXT, -- JSON string
                    deals_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- PDF comparison history
                CREATE TABLE IF NOT EXISTS pdf_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_names TEXT NOT NULL, -- JSON array
                    comparison_prompt TEXT NOT NULL,
                    result_data TEXT, -- JSON string
                    web_search_enabled BOOLEAN DEFAULT FALSE,
                    web_insights TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Usage analytics
                CREATE TABLE IF NOT EXISTS usage_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL, -- 'market_analysis', 'pdf_upload', 'pdf_query', 'comparison'
                    event_data TEXT, -- JSON string
                    user_agent TEXT,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_market_cache_hash ON market_cache(query_hash);
                CREATE INDEX IF NOT EXISTS idx_market_cache_name ON market_cache(market_name);
                CREATE INDEX IF NOT EXISTS idx_pdf_history_hash ON pdf_history(file_hash);
                CREATE INDEX IF NOT EXISTS idx_user_sessions_id ON user_sessions(session_id);
                CREATE INDEX IF NOT EXISTS idx_usage_analytics_type ON usage_analytics(event_type);
            """)
    
    def generate_query_hash(self, market_name: str, query_type: str, **kwargs) -> str:
        """Generate a hash for caching purposes"""
        query_string = f"{market_name}:{query_type}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(query_string.encode()).hexdigest()
    
    # === MARKET CACHE METHODS ===
    def get_cached_result(self, market_name: str, query_type: str, **kwargs) -> Optional[Dict]:
        """Retrieve cached market analysis result"""
        query_hash = self.generate_query_hash(market_name, query_type, **kwargs)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT result_data, created_at, expires_at 
                FROM market_cache 
                WHERE query_hash = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
            """, (query_hash,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'data': json.loads(row['result_data']),
                    'cached_at': row['created_at'],
                    'expires_at': row['expires_at']
                }
        return None
    
    def cache_result(self, market_name: str, query_type: str, result_data: Any, 
                    source: str = 'openai', expire_hours: int = 24, **kwargs):
        """Cache a market analysis result"""
        query_hash = self.generate_query_hash(market_name, query_type, **kwargs)
        expires_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if expire_hours else None
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO market_cache 
                (market_name, query_type, query_hash, result_data, source, expires_at)
                VALUES (?, ?, ?, ?, ?, datetime('now', '+{} hours'))
            """.format(expire_hours), (market_name, query_type, query_hash, 
                                     json.dumps(result_data), source))
    
    # === PDF METHODS ===
    def save_pdf_processing(self, file_name: str, file_content: bytes, 
                           total_pages: int, openai_file_ids: List[str]) -> int:
        """Save PDF processing information"""
        file_hash = hashlib.md5(file_content).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO pdf_history 
                (file_name, file_hash, file_size, total_pages, chunks_count, openai_file_ids)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_name, file_hash, len(file_content), total_pages, 
                  len(openai_file_ids), json.dumps(openai_file_ids)))
            
            return cursor.lastrowid
    
    def get_pdf_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Check if PDF was already processed"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM pdf_history WHERE file_hash = ? AND status = 'processed'
                ORDER BY processed_at DESC LIMIT 1
            """, (file_hash,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'file_name': row['file_name'],
                    'total_pages': row['total_pages'],
                    'chunks_count': row['chunks_count'],
                    'openai_file_ids': json.loads(row['openai_file_ids']),
                    'processed_at': row['processed_at']
                }
        return None
    
    def save_pdf_qa(self, pdf_history_id: int, question: str, answer: str, 
                   query_tokens: int = 0, response_tokens: int = 0) -> int:
        """Save PDF Q&A interaction"""
        # Rough cost estimation (adjust based on current OpenAI pricing)
        cost_estimate = (query_tokens * 0.01 + response_tokens * 0.03) / 1000
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO pdf_qa 
                (pdf_history_id, question, answer, query_tokens, response_tokens, cost_estimate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pdf_history_id, question, answer, query_tokens, response_tokens, cost_estimate))
            
            return cursor.lastrowid
    
    def get_pdf_qa_history(self, pdf_history_id: int) -> List[Dict]:
        """Get Q&A history for a specific PDF"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT question, answer, created_at, cost_estimate
                FROM pdf_qa 
                WHERE pdf_history_id = ?
                ORDER BY created_at DESC
            """, (pdf_history_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # === M&A METHODS ===
    def save_ma_search(self, market_name: str, timeframe: str, result_data: str, deals_count: int = 0):
        """Save M&A search result"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ma_searches (market_name, timeframe, result_data, deals_count)
                VALUES (?, ?, ?, ?)
            """, (market_name, timeframe, result_data, deals_count))
    
    def get_recent_ma_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent M&A searches"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT market_name, timeframe, deals_count, created_at, result_data
                FROM ma_searches 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # === ANALYTICS METHODS ===
    def log_event(self, event_type: str, event_data: Dict = None, session_id: str = None):
        """Log usage analytics event"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO usage_analytics (event_type, event_data, session_id)
                VALUES (?, ?, ?)
            """, (event_type, json.dumps(event_data) if event_data else None, session_id))
    
    def get_popular_markets(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """Get most popular markets in the last N days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    JSON_EXTRACT(event_data, '$.market_name') as market_name,
                    COUNT(*) as query_count,
                    MAX(created_at) as last_queried
                FROM usage_analytics 
                WHERE event_type = 'market_analysis' 
                    AND created_at > datetime('now', '-{} days')
                    AND JSON_EXTRACT(event_data, '$.market_name') IS NOT NULL
                GROUP BY JSON_EXTRACT(event_data, '$.market_name')
                ORDER BY query_count DESC
                LIMIT ?
            """.format(days), (limit,))
            
            return [{'market_name': row[0], 'query_count': row[1], 'last_queried': row[2]} 
                   for row in cursor.fetchall()]
    
    # === HISTORY BROWSING METHODS ===
    def get_market_analysis_history(self, limit: int = 20) -> List[Dict]:
        """Get history of market analyses for browsing"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT DISTINCT market_name, query_type, created_at,
                       COUNT(*) OVER (PARTITION BY market_name, query_type) as access_count
                FROM market_cache 
                WHERE expires_at > datetime('now') OR expires_at IS NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_complete_market_analysis(self, market_name: str) -> Dict:
        """Get all analysis types for a market (global, vertical, horizontal)"""
        results = {}
        for query_type in ['global', 'vertical', 'horizontal']:
            cached = self.get_cached_result(market_name, query_type)
            if cached:
                results[query_type] = cached['data']
        return results
    
    def get_pdf_sessions_summary(self, limit: int = 15) -> List[Dict]:
        """Get summary of PDF sessions for browsing"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT p.id, p.file_name, p.total_pages, p.chunks_count, 
                       p.processed_at, p.openai_file_ids,
                       COUNT(q.id) as qa_count,
                       MAX(q.created_at) as last_question
                FROM pdf_history p
                LEFT JOIN pdf_qa q ON p.id = q.pdf_history_id
                WHERE p.status = 'processed'
                GROUP BY p.id
                ORDER BY p.processed_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def restore_pdf_session(self, pdf_id: int) -> Dict:
        """Get all data needed to restore a PDF session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get PDF info
            pdf_cursor = conn.execute("""
                SELECT * FROM pdf_history WHERE id = ? AND status = 'processed'
            """, (pdf_id,))
            pdf_data = pdf_cursor.fetchone()
            
            if not pdf_data:
                return None
            
            # Get Q&A history
            qa_cursor = conn.execute("""
                SELECT question, answer, created_at, cost_estimate
                FROM pdf_qa 
                WHERE pdf_history_id = ?
                ORDER BY created_at ASC
            """, (pdf_id,))
            qa_history = [dict(row) for row in qa_cursor.fetchall()]
            
            return {
                'pdf_info': dict(pdf_data),
                'qa_history': qa_history
            }
    
    # === UTILITY METHODS ===
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM market_cache WHERE expires_at < datetime('now')")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Get table counts
            tables = ['market_cache', 'pdf_history', 'pdf_qa', 'ma_searches', 'usage_analytics']
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Get database size
            stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            
            return stats