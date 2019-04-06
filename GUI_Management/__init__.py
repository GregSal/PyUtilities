'''
Manage Structure Templates
@author: Greg Salomons
'''
from pathlib import Path
import sys

def add_path(relative_path: str):
    new_path = Path.cwd() / relative_path
    new_path_str = str(new_path.resolve())
    sys.path.append(new_path_str)

# Set the path to the Utilities Package.
utilities_path = '..'
variable_path = r'..\CustomVariableSet'
templates_path = r'..\..\EclipseRelated\EclipseTemplates\ManageStructuresTemplates'

add_path(utilities_path)
add_path(variable_path)
add_path(templates_path)

