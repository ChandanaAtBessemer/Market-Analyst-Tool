# debug_database.py - Run this to diagnose the issue

import sys
import os

print("=== DATABASE DEBUGGING ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")  # Show first 3 paths

# Check if database.py exists
if os.path.exists('database.py'):
    print("✅ database.py file exists")
    
    # Check file size
    size = os.path.getsize('database.py')
    print(f"📊 database.py size: {size} bytes")
    
    if size < 1000:
        print("⚠️  File seems too small - might not have been updated properly")
    
    # Read first few lines to verify content
    with open('database.py', 'r') as f:
        first_lines = f.read(500)
        if 'get_market_analysis_history' in first_lines:
            print("✅ get_market_analysis_history found in file")
        else:
            print("❌ get_market_analysis_history NOT found in first 500 chars")
            
        if 'class MarketResearchDB' in first_lines:
            print("✅ MarketResearchDB class found")
        else:
            print("❌ MarketResearchDB class NOT found")
            
else:
    print("❌ database.py file NOT found")

print("\n=== IMPORT TEST ===")
try:
    # Test import
    from database import MarketResearchDB
    print("✅ Successfully imported MarketResearchDB")
    
    # Create instance
    db = MarketResearchDB()
    print("✅ Successfully created database instance")
    
    # Check methods
    methods = [method for method in dir(db) if not method.startswith('_')]
    print(f"📋 Available methods: {len(methods)}")
    
    required_methods = [
        'get_market_analysis_history',
        'get_pdf_sessions_summary', 
        'restore_pdf_session',
        'get_cached_result',
        'cache_result'
    ]
    
    print("\n=== METHOD CHECK ===")
    for method in required_methods:
        if hasattr(db, method):
            print(f"✅ {method} - EXISTS")
        else:
            print(f"❌ {method} - MISSING")
    
    print("\n=== TESTING METHODS ===")
    try:
        result = db.get_market_analysis_history(limit=1)
        print(f"✅ get_market_analysis_history works: {type(result)}")
    except Exception as e:
        print(f"❌ get_market_analysis_history failed: {e}")
        
    try:
        result = db.get_pdf_sessions_summary(limit=1)  
        print(f"✅ get_pdf_sessions_summary works: {type(result)}")
    except Exception as e:
        print(f"❌ get_pdf_sessions_summary failed: {e}")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n=== FILE CONTENT CHECK ===")
try:
    with open('database.py', 'r') as f:
        content = f.read()
        
    # Count key occurrences
    class_count = content.count('class MarketResearchDB')
    method1_count = content.count('def get_market_analysis_history')
    method2_count = content.count('def get_pdf_sessions_summary')
    
    print(f"MarketResearchDB class definitions: {class_count}")
    print(f"get_market_analysis_history definitions: {method1_count}")
    print(f"get_pdf_sessions_summary definitions: {method2_count}")
    
    if class_count != 1:
        print("⚠️  Should have exactly 1 class definition")
    if method1_count != 1:
        print("⚠️  Should have exactly 1 get_market_analysis_history definition")
    if method2_count != 1:
        print("⚠️  Should have exactly 1 get_pdf_sessions_summary definition")
        
    # Check for syntax errors
    try:
        compile(content, 'database.py', 'exec')
        print("✅ No syntax errors in database.py")
    except SyntaxError as e:
        print(f"❌ Syntax error in database.py: {e}")
        
except Exception as e:
    print(f"❌ Cannot read database.py: {e}")

print("\n=== RECOMMENDATIONS ===")
print("1. If methods are missing: Replace database.py with the complete version")
print("2. If import fails: Check for syntax errors")
print("3. If file is too small: Copy the complete database code again")
print("4. If all else fails: Restart Python completely")
print("=== END DEBUG ===")