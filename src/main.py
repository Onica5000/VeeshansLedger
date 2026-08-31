"""Entry point for the EQL Plane of Sky Tracker."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eqlsky.app import main

if __name__ == "__main__":
    main()
