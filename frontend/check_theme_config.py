import os
import re

def check_tailwind_config():
    # Try js or cjs
    config_path = "tailwind.config.js"
    if not os.path.exists(config_path):
        config_path = "tailwind.config.cjs"
        if not os.path.exists(config_path):
            print("FAIL: tailwind.config.js/cjs not found!")
            return False
    
    with open(config_path, 'r') as f:
        content = f.read()
        
    if "darkMode: 'class'" in content or 'darkMode: "class"' in content:
        print("PASS: tailwind.config.js has darkMode: 'class'")
        return True
    else:
        print("FAIL: tailwind.config.js missing darkMode: 'class'")
        print("      Without this, adding 'dark' class to html won't trigger dark mode.")
        return False

def check_auth_context():
    # Check if applyTheme logic targets document.documentElement
    path = "src/context/AuthContext.tsx"
    if not os.path.exists(path):
        print(f"FAIL: {path} not found!")
        return False
        
    with open(path, 'r') as f:
        content = f.read()
        
    if "document.documentElement" in content and "classList.add" in content and "dark" in content:
        print("PASS: AuthContext.tsx seems to manipulate document classes for theme.")
        return True
    else:
        print("FAIL: AuthContext.tsx might be missing logic to add 'dark' class to html root.")
        return False

if __name__ == "__main__":
    print("=== Checking Frontend Theme Configuration ===")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    t = check_tailwind_config()
    a = check_auth_context()
    
    if t and a:
        print("\nConfiguration looks correct. If UI still doesn't change:")
        print("1. Check if index.css includes @tailwind base/components/utilities")
        print("2. Restart Vite server to reload tailwind config")
    else:
        print("\nFound configuration issues. Please fix them.")
