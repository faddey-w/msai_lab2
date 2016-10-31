import os
import sys
from distutils.core import setup
import py2exe


tcl_location = os.path.join(os.path.dirname(sys.executable), 'tcl', 'tcl8.6')
tk_location = os.path.join(os.path.dirname(sys.executable), 'tcl', 'tk8.6')
os.environ['TCL_LIBRARY'] = tcl_location
os.environ['TK_LIBRARY'] = tk_location

setup(
    options={'py2exe': {'bundle_files': 1, 'compressed': True}},
    zipfile=None,
    windows=['TkReversi.py']
)

