try:
    import tkinter as tk
    from tkinter import simpledialog
except ImportError:
    import Tkinter as tk
    import tkSimpleDialog as simpledialog

import enum


__all__ = ['tk', 'simpledialog', 'enum']
