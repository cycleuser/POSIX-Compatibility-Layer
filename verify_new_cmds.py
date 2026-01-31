import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from posix_compat import core
    compat = core.CompatLayer()
    
    print("Testing lscpu...")
    print(compat.execute("lscpu", []))
    print("-" * 20)
    
    print("Testing hostname...")
    print(compat.execute("hostname", []))
    print("-" * 20)
    
    print("Testing df...")
    print(compat.execute("df", []))
    print("-" * 20)
    
    print("Testing free (might be simulated)...")
    print(compat.execute("free", []))
    print("-" * 20)
    
    # lspci/lsusb rely on wmic on windows, might fail in some envs but code should handle exception
    print("Testing lspci...")
    print(compat.execute("lspci", [])[:200] + "...") # Truncate
    print("-" * 20)
    
except Exception as e:
    print(f"Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
