import sys
import pathlib

backend_dir = pathlib.Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
