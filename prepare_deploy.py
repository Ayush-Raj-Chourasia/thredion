#!/usr/bin/env python3
"""
Create proper deployment ZIP for Azure staging
Ensures requirements.txt is at root level for pip to find it
"""

import os
import shutil
import zipfile
from pathlib import Path

def main():
    # Create temp deploy directory
    deploy_dir = Path('deploy_temp')
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # Copy thredion-engine contents to root of deploy_dir
    engine_dir = Path('thredion-engine')
    print(f"Copying from {engine_dir}...")
    
    for item in engine_dir.iterdir():
        if item.is_dir():
            if item.name not in ['__pycache__', '.pytest_cache', '.git']:
                shutil.copytree(item, deploy_dir / item.name)
                print(f"  ✓ {item.name}/")
        else:
            shutil.copy2(item, deploy_dir / item.name)
            print(f"  ✓ {item.name}")
    
    print('\n✅ Copied engine files')
    
    # Verify key files exist
    print(f"\n📋 Verification:")
    print(f"  Requirements.txt exists: {(deploy_dir / 'requirements.txt').exists()}")
    print(f"  Main.py exists: {(deploy_dir / 'main.py').exists()}")
    
    # Create ZIP
    zip_path = Path('deploy_staging_fixed.zip')
    if zip_path.exists():
        zip_path.unlink()
    
    print(f"\n📦 Creating ZIP: {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(deploy_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache']]
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(deploy_dir)
                zf.write(file_path, arcname)
                
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f'✅ ZIP created: {zip_path} ({size_mb:.2f} MB)')
    print(f'\n🚀 Ready for deployment!')
    
    return True

if __name__ == "__main__":
    main()
