import sys
import os

INTERP = os.path.expanduser("/var/www/u3475599/data/flaskenv/bin/python")
if sys.executable != INTERP:
   os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

# Import the Flask application
from app import application
