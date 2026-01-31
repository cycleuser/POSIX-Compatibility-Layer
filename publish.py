import os
import sys
import shutil
import subprocess
import glob

def print_step(step):
    print(f"\n{'='*40}")
    print(f"STEP: {step}")
    print(f"{'='*40}")

def check_dependencies():
    print_step("Checking Dependencies")
    required = ["build", "twine"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            # Try checking via pip freeze or just assume it might be installed as a tool
            # A better check is subprocess call
            try:
                subprocess.check_call([sys.executable, "-m", pkg, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                missing.append(pkg)
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("Dependencies installed successfully.")
        except subprocess.CalledProcessError:
            print("Error installing dependencies. Please install 'build' and 'twine' manually.")
            sys.exit(1)
    else:
        print("All dependencies (build, twine) are installed.")

def clean_dist():
    print_step("Cleaning 'dist' directory")
    dist_dir = os.path.join(os.getcwd(), "dist")
    if os.path.exists(dist_dir):
        try:
            shutil.rmtree(dist_dir)
            print(f"Removed {dist_dir}")
        except Exception as e:
            print(f"Error cleaning dist directory: {e}")
            sys.exit(1)
    else:
        print("No 'dist' directory found. Nothing to clean.")

def build_package():
    print_step("Building Package")
    try:
        subprocess.check_call([sys.executable, "-m", "build"])
        print("Build completed successfully.")
    except subprocess.CalledProcessError:
        print("Error during build process.")
        sys.exit(1)

def upload_package():
    print_step("Uploading to PyPI")
    
    # Check if dist has files
    files = glob.glob("dist/*")
    if not files:
        print("No files found in dist/ to upload.")
        sys.exit(1)
        
    print(f"Found {len(files)} files to upload:")
    for f in files:
        print(f" - {f}")
        
    confirm = input("\nDo you want to upload these files to PyPI? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Upload cancelled.")
        return

    try:
        cmd = [sys.executable, "-m", "twine", "upload"] + files
        subprocess.check_call(cmd)
        print("\nUpload completed successfully!")
    except subprocess.CalledProcessError:
        print("\nError during upload.")
        sys.exit(1)

def main():
    print("Starting automated build and publish process...")
    
    check_dependencies()
    clean_dist()
    build_package()
    upload_package()
    
    print("\nAll done.")

if __name__ == "__main__":
    main()
