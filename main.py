"""
Entry point untuk Gunicorn.

Jalankan:
    gunicorn serve:app --bind 0.0.0.0:85

Atau (lebih baik):
    gunicorn serve:app --bind unix:/tmp/myapp.sock
"""

from app import create_app

# Gunicorn akan membaca variable ini
app = create_app('production')