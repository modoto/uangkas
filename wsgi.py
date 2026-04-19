import sys
import os

# Tambahkan path project ke sys.path
path = '/home/YOUR_USERNAME/flask_uangkas'
if path not in sys.path:
    sys.path.insert(0, path)

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

from app import create_app
application = create_app('production')
