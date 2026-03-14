#!/usr/bin/env python3
"""
Quick Start Script - Verify all system components are ready
Run this to confirm system is ready for API testing and deployment
"""

import sys
import os
from pathlib import Path

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_files():
    """Verify all required files exist"""
    print("\n📂 CHECKING PROJECT STRUCTURE...")
    
    required_files = {
        "main.py": "FastAPI application",
        "requirements.txt": "Python dependencies",
        "db/models.py": "Database schema",
        "db/database.py": "Database connection",
        "services/transcriber.py": "Video transcription service",
        "services/extractor.py": "Content extraction service",
        "api/routes.py": "REST API endpoints",
        "core/config.py": "Configuration management",
    }
    
    all_good = True
    for file_path, description in required_files.items():
        full_path = Path(file_path)
        if full_path.exists():
            print(f"   ✅ {file_path:<40} ({description})")
        else:
            print(f"   ❌ {file_path:<40} (MISSING!)")
            all_good = False
    
    return all_good

def check_database():
    """Verify database is initialized"""
    print("\n💾 CHECKING DATABASE...")
    
    from db.database import init_db, SessionLocal, engine
    from db.models import Memory
    
    try:
        init_db()
        print("   ✅ Database initialized")
        
        db = SessionLocal()
        count = db.query(Memory).count()
        print(f"   ✅ Memory table accessible ({count} records)")
        db.close()
        
        return True
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def check_imports():
    """Verify all critical imports work"""
    print("\n📦 CHECKING IMPORTS...")
    
    imports_to_check = [
        ("fastapi", "FastAPI"),
        ("sqlalchemy.orm", "SQLAlchemy ORM"),
        ("services.transcriber", "Transcriber service"),
        ("services.extractor", "Extractor service"),
        ("services.classifier", "Classifier service"),
    ]
    
    all_good = True
    for module, description in imports_to_check:
        try:
            __import__(module)
            print(f"   ✅ {module:<40} ({description})")
        except ImportError as e:
            print(f"   ❌ {module:<40} (Error: {e})")
            all_good = False
    
    return all_good

def check_configuration():
    """Verify configuration is loaded"""
    print("\n⚙️  CHECKING CONFIGURATION...")
    
    try:
        from core.config import settings
        
        print(f"   ✅ DATABASE_URL: {settings.DATABASE_URL[:30]}...")
        groq_api = getattr(settings, 'GROQ_API_KEY', 'Not configured')
        print(f"   ✅ GROQ_API_KEY: {'Set' if groq_api != 'Not configured' else 'Not set'}")
        print(f"   ✅ Settings loaded successfully")
        
        return True
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 THREDION ENGINE - SYSTEM READINESS CHECK".center(70))
    print("="*70)
    
    results = {
        "Files": check_files(),
        "Database": check_database(),
        "Imports": check_imports(),
        "Configuration": check_configuration(),
    }
    
    print("\n" + "="*70)
    print("📊 SUMMARY".center(70))
    print("="*70)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check:<30} {status}")
    
    if all(results.values()):
        print("\n✅ ALL SYSTEMS GO! Ready to start server.\n")
        print("Start the API server with:")
        print("   python main.py\n")
        print("Then visit:")
        print("   http://localhost:8000/docs\n")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed. Fix issues before starting.\n")
        sys.exit(1)
