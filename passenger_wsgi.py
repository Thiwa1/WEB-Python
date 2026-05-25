"""
cPanel Passenger WSGI entry point for tiptopvacancies.com
---------------------------------------------------------
cPanel's "Setup Python App" tool will use this file to serve the Flask app.
The virtual environment Python path is injected automatically by cPanel via
the PassengerPython directive it writes to .htaccess — do NOT hardcode it here.
"""
import sys
import os

# Make sure the app directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

# Force production mode on the server
os.environ.setdefault('FLASK_ENV', 'production')

# Import and expose the Flask app as "application" (Passenger requirement)
from app import app as application
