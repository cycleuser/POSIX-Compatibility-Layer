import sys
import os

def main():
    # Get the directory where this script is located (project root)
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Add 'src' directory to Python path
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        
    print(f"Starting POSIX Compatibility Layer GUI...")
    print(f"Added to path: {src_path}")
    
    try:
        from posix_compat.gui import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"\nError: Could not import application module.")
        print(f"Details: {e}")
        print("\nPlease ensure the 'src/posix_compat' directory exists and contains gui.py")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
