"""
Windows console binding for SasView
"""
import atexit
import os
import sys


def attach_windows_console():
    """
    Attach a console to a windows program that does not normally have one.

    Note: Uses a lazy import for win32console so you will to add pywin32
    to requirements.txt and tell the installer to include win32.win32console
    """
    # Lazy import so we don't have to check for OS.
    from win32 import win32console
    if win32console.GetConsoleWindow() == 0: # No console attached
        # The following kinda works but has flaky interaction with the existing prompt
        #win32console.AttachConsole(-1) # Attach to parent console
        # Instead create a new console for I/O and call it the sasview console
        win32console.AllocConsole()
        win32console.SetConsoleTitle('SasView console')

class Singleton(type):
    """
    Metaclass indicating that all object instantiations should return the same instance.

    Usage:

        class Stateful(metaclass=Singleton): ...

    The init will only be triggered for the first instance, so you probably shouldn't
    parameterize it, or only parameterize it during setup before any other instances
    are created.
    """
    # Adam Forsyth (2011)
    # https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python/6798042#6798042
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class WindowsConsole(metaclass=Singleton):
    """
    Windows console object.

    This only creates the console when you read to it or write from it. This reduces
    flashing windows when using the app in a pipeline.

    This presents as an incomplete standard rw file interface.

    Unfortunately it does not regiister as a windows console stdio object so the
    cpython myreadline code does not call PyOS_InputHook during read. The practical
    consequence is that pyplot.ion() does not create an interactive plot, and you
    instead need to call pyplot.pause(0.1) to draw the figure. You can try tracing
    through myreadline.c to see what we need to do to get sys.stdin recognized as
    stdin here: https://github.com/python/cpython/blob/main/Parser/myreadline.c
    """
    def __init__(self):
        self._attached = False
        self._conin = None
        self._conout = None
    def close_wait(self):
        """
        Registered with atexit to give users a chance to see the output.
        """
        if self._conout is not None:
            # An output console was opened for writing, so pause
            self.write("Press enter to exit...")
            self.flush()
            self.readline()
    def _attach_console(self):
        if not self._attached:
            attach_windows_console()
            self._attached = True
    @property
    def _read_fd(self):
        if self._conin is None:
            self._attach_console()
            self._conin = open("CONIN$")
        return self._conin
    @property
    def _write_fd(self):
        if self._conout is None:
            self._attach_console()
            self._conout = open("CONOUT$", "w")
            #self._conout.write("registering atexit...\n")
            atexit.register(self.close_wait)
        return self._conout
    def readline(self, *args, **kwargs):
        return self._read_fd.readline(*args, **kwargs)
    def write(self, *args, **kwargs):
        return self._write_fd.write(*args, **kwargs)
    def flush(self):
        return self._write_fd.flush()
    # Unused
    def read(self, *args, **kwargs):
        return self._read_fd.read(*args, **kwargs)
    def isatty(self):
        return True
    def readable(self):
        return True
    def writeable(self):
        return True
    def seekable(self):
        return False
    def name(self):
        return "<CONIO>"
    # Not implemented:
    #    buffer, close, closed, detach, encoding, errors, fileno, line_buffering, mode,
    #    newlines, readlines, reconfigure, seek, tell, truncate, write_through, write_lines
    #    __enter__, __exit__, __iter__, __next__

def setup_console(stderr_as="console"):
    """
    Lazy redirect of stdio to windows console.

    Handling of stderr is defined by the caller:

    * console: create a console for stderr even if stdin/stdout are redirected.
    * stdout: redirect stderr to whereever stdout is going
    * null: redirect stderr to the NUL device (untested!!)
    * none: don't redirect stderr; instead windows displays an error box with stderr contents
    """
    if os.name == 'nt': # Make sure we are attached to a console
        if sys.__stdin__ is None:
            sys.__stdin__ = sys.stdin = WindowsConsole()
        if sys.__stdout__ is None:
            sys.__stdout__ = sys.stdout = WindowsConsole()
        if sys.__stderr__ is None:
            if stderr_as == "console":
                stderr = WindowsConsole()
            elif stderr_as == "stdout":
                stderr = sys.__stdout__
            elif stderr_as == "null":
                # TODO: Untested !!
                stderr = open("NUL:", "w")
            elif stderr_as == "none":
                stderr = None
            sys.__stderr__ = sys.stderr = stderr

def setup_console_simple(stderr_to_stdout=True):
    """
    Simple version of stdio redirection: always open a console, and don't pause before closing.
    """
    if os.name == 'nt':
        def console_open(mode):
            attach_windows_console()
            return open("CON:") if mode == "r" else open("CON:", "w")
        if sys.__stdin__ is None:
            sys.__stdin__ = sys.stdin = console_open("r")
        if sys.__stdout__ is None:
            sys.__stdout__ = sys.stdout = console_open("w")
        if sys.__stderr__ is None:
            sys.__stderr__ = sys.stderr = sys.__stdout__ if stderr_to_stdout else console_open("w")
            sys.__stderr__ = sys.stderr = console_open("w")


def demo():
    setup_console()
    print("demo ready")
    import code
    code.interact(local={'exit': sys.exit})
    print('demo done')
    #import time; time.sleep(2)

if __name__ == "__main__":
    demo()
