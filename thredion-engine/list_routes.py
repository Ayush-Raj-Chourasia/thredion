import sys
import os
sys.path.insert(0, os.getcwd())

from main import app

print("FastAPI routes registered:")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"  {route.path}")
