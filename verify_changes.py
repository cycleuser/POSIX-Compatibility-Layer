import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from posix_compat import ollama_client
    print("ollama_client imported successfully")
    
    client = ollama_client.OllamaClient()
    print("OllamaClient initialized")
    
    from posix_compat import i18n
    print("i18n imported successfully")
    print(f"Key check: {i18n._('gui_lbl_model')}")
    
    # GUI import might fail if no display, but we can check syntax
    try:
        from posix_compat import gui
        print("gui imported successfully")
    except ImportError as e:
        # Tkinter might fail in headless
        if "tkinter" in str(e):
             print("gui import skipped (headless)")
        else:
             raise e
    except Exception as e:
        # _tkinter.TclError: no display name and no $DISPLAY environment variable
        print(f"gui import exception: {e}")
    
except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
