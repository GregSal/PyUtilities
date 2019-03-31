'''
Manage Structure Templates
@author: Greg Salomons
'''
from pathlib import Path
import sys

# Set the path to the Utilities Package.
utilities_path = Path.cwd() / '..\\..\\..\\Utilities'
utilities_path_str = str(utilities_path.resolve())
sys.path.append(utilities_path_str)