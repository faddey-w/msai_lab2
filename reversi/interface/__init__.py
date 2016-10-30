import tkinter as tk
from .app import ReversiApp


__all__ = ['main', 'ReversiApp']


def main():
    root = tk.Tk()

    _platform_specific_init()

    ReversiApp(root)
    root.mainloop()


def _platform_specific_init():
    from os import system, getenv
    from platform import system as platform
    if platform() == 'Darwin':
        if getenv('REVERSI_DEVEL', ''):
            # focus on Tk window, development only
            # in production we'll build the application with py2app
            system('''/usr/bin/osascript -e '''
                   ''' 'tell app "Finder" to set frontmost '''
                   '''  of process "Python" to true' ''')
