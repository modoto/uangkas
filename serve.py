"""
Jalankan aplikasi dengan Waitress (production WSGI server).

    python serve.py

Pastikan FLASK_ENV=production sudah diset di .env sebelum menjalankan.
"""
import os
from waitress import serve
from app import create_app

app = create_app('production')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 85))
    print(f'Uang Kas — Production Server — port {port}')
    serve(app, host='0.0.0.0', port=port, threads=4)
