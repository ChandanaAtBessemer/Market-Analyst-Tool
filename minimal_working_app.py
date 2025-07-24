# minimal_working_app.py - Self-contained version with database built-in

import streamlit as st
import sqlite3
import json
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# === BUILT-IN DATABASE CLASS ===
class SimpleMarketDB:
    def __init__(self, db_path: str = "simple_market.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS market_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_name TEXT NOT NULL,
                    query_type TEXT NOT NULL,
                    query_hash TEXT UNIQUE NOT NULL,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS pdf_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    total_pages INTEGER,
                    chunks_count INTEGER,
                    openai_file_ids TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'processed'
                );
                
                CREATE TABLE IF NOT EXISTS pdf_qa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_history_id INTEGER,
                    question TEXT NOT NULL,
                    answer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS ma_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_name TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    result_data TEXT,
                    deals_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS usage_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def generate_query_hash(self, market_name: str, query_type: str) -> str:
        """Generate a hash for caching purposes"""
        query_string = f"{market_name}:{query_type}"
        return hashlib.md5(query_string.encode()).hexdigest()
    
    def get_cached_result(self, market_name: str, query_type: str) -> Optional[Dict]:
        """Retrieve cached result"""
        query_hash = self.generate_query_hash(market_name, query_type)
        
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
                    'data': row['result_data'],  # Keep as string for simplicity
                    'cached_at': row['created_at'],
                    'expires_at': row['expires_at']
                }
        return None
    
    def cache_result(self, market_name: str, query_type: str, result_data: str, expire_hours: int = 24):
        """Cache a result"""
        query_hash = self.generate_query_hash(market_name, query_type)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO market_cache 
                (market_name, query_type, query_hash, result_data, expires_at)
                VALUES (?, ?, ?, ?, datetime('now', '+{} hours'))
            """.format(expire_hours), (market_name, query_type, query_hash, result_data))
    
    def get_market_analysis_history(self, limit: int = 20) -> List[Dict]:
        """Get market analysis history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT DISTINCT market_name, query_type, created_at
                FROM market_cache 
                WHERE expires_at > datetime('now') OR expires_at IS NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [{'market_name': row['market_name'], 
                    'query_type': row['query_type'], 
                    'created_at': row['created_at'],
                    'access_count': 1} for row in cursor.fetchall()]
    
    def get_pdf_sessions_summary(self, limit: int = 15) -> List[Dict]:
        """Get PDF sessions summary"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT p.id, p.file_name, p.total_pages, p.chunks_count, 
                       p.processed_at, p.openai_file_ids,
                       COUNT(q.id) as qa_count
                FROM pdf_history p
                LEFT JOIN pdf_qa q ON p.id = q.pdf_history_id
                WHERE p.status = 'processed'
                GROUP BY p.id
                ORDER BY p.processed_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
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
    
    def get_popular_markets(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """Get popular markets - simplified version"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT market_name, COUNT(*) as query_count, MAX(created_at) as last_queried
                FROM market_cache 
                WHERE created_at > datetime('now', '-{} days')
                GROUP BY market_name
                ORDER BY query_count DESC
                LIMIT ?
            """.format(days), (limit,))
            
            return [{'market_name': row[0], 'query_count': row[1], 'last_queried': row[2]} 
                   for row in cursor.fetchall()]
    
    def log_event(self, event_type: str, event_data: Dict = None, session_id: str = None):
        """Log an event"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO usage_analytics (event_type, event_data, session_id)
                VALUES (?, ?, ?)
            """, (event_type, json.dumps(event_data) if event_data else None, session_id))
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            tables = ['market_cache', 'pdf_history', 'pdf_qa', 'ma_searches', 'usage_analytics']
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            return stats
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM market_cache WHERE expires_at < datetime('now')")

# === STREAMLIT APP ===
st.set_page_config(page_title="Simple Market Explorer", layout="wide")

# Initialize database
@st.cache_resource
def init_simple_db():
    return SimpleMarketDB()

db = init_simple_db()

st.title("🧪 Simple Market Explorer - Database Test")

# Test the database methods
st.subheader("Database Method Test")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Test Market History"):
        try:
            result = db.get_market_analysis_history(5)
            st.success(f"✅ Market history works! Found {len(result)} items")
            if result:
                for item in result:
                    st.write(f"- {item['market_name']} ({item['query_type']})")
        except Exception as e:
            st.error(f"❌ Market history failed: {e}")

with col2:
    if st.button("Test PDF History"):
        try:
            result = db.get_pdf_sessions_summary(5)
            st.success(f"✅ PDF history works! Found {len(result)} items")
            if result:
                for item in result:
                    st.write(f"- {item['file_name']} ({item['qa_count']} Q&As)")
        except Exception as e:
            st.error(f"❌ PDF history failed: {e}")

with col3:
    if st.button("Test M&A History"):
        try:
            result = db.get_recent_ma_searches(5)
            st.success(f"✅ M&A history works! Found {len(result)} items")
            if result:
                for item in result:
                    st.write(f"- {item['market_name']} ({item['timeframe']})")
        except Exception as e:
            st.error(f"❌ M&A history failed: {e}")

# Add some test data
st.subheader("Add Test Data")

col1, col2 = st.columns(2)

with col1:
    if st.button("Add Test Market Data"):
        db.cache_result("AI Market", "global", "Test global AI market data")
        db.cache_result("AI Market", "vertical", "Test vertical AI market data")
        db.log_event("market_analysis", {"market_name": "AI Market"})
        st.success("✅ Added test market data")

with col2:
    if st.button("Add Test M&A Data"):
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("""
                INSERT INTO ma_searches (market_name, timeframe, result_data, deals_count)
                VALUES (?, ?, ?, ?)
            """, ("Tech Market", "Last 3 years", "Sample M&A data", 5))
        st.success("✅ Added test M&A data")

# Show database stats
st.subheader("Database Statistics")
stats = db.get_database_stats()
st.json(stats)

# Test popular markets
st.subheader("Popular Markets")
popular = db.get_popular_markets(30, 5)
if popular:
    for market in popular:
        st.write(f"📈 {market['market_name']}: {market['query_count']} queries")
else:
    st.info("No popular markets found. Add some test data first.")