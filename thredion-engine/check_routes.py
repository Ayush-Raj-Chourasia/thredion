#!/usr/bin/env python3
"""Check if routes are registered in the deployed app"""

try:
    from main import app
    auth_routes = [r.path for r in app.routes if hasattr(r, 'path') and '/auth' in r.path]
    all_route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
    
    print("=" * 70)
    print("ROUTE REGISTRATION CHECK")
    print("=" * 70)
    print(f"\nTotal routes: {len(all_route_paths)}")
    print(f"\nAuth routes found: {len(auth_routes)}")
    if auth_routes:
        for path in auth_routes:
            print(f"  ✓ {path}")
    else:
        print("  ✗ No auth routes found")
    
    print(f"\nAll routes:")
    for path in sorted(all_route_paths)[:20]:
        print(f"  - {path}")
    
    print("\n" + "=" * 70)
    print("DEPLOYMENT STATUS: Auth routes are", "REGISTERED ✓" if auth_routes else "NOT REGISTERED ✗")
    print("=" * 70)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
