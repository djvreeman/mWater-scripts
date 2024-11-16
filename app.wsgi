import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, "/var/www/sensor-dashboard")

# Activate the virtual environment
venv_path = "/var/www/sensor-dashboard/venv"
os.environ['VIRTUAL_ENV'] = venv_path
os.environ['PATH'] = os.path.join(venv_path, 'bin') + os.pathsep + os.environ['PATH']

# Add the virtual environment's site-packages to the Python path
site_packages = os.path.join(venv_path, 'lib', 'python3.12', 'site-packages')
sys.path.insert(0, site_packages)

# Import the Dash app (exposing Flask server via `server`)
from run_sensor_dashboard_for_web import app
application = app.server