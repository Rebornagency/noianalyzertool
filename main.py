import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main app
from app import main

# Run the app if this file is executed directly
if __name__ == "__main__":
    main()
