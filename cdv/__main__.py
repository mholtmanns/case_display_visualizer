"""Lets the project be launched as `python cdv` from the project root.

Python treats a directory passed as the script argument as runnable if it
contains a __main__.py, the same mechanism `python -m <package>` uses
internally -- no extra entry-point script or console_scripts shim needed.
"""

from case_display_visualizer.app import run

if __name__ == "__main__":
    run()
