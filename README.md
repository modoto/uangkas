# uangkas

🧩 1. Masuk ke VPS & install kebutuhan

SSH ke server:

ssh username@ip-server

Update & install:

sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git nginx -y

📥 2. Clone project dari GitHub

Masuk ke folder (misalnya /var/www):

cd /var/www
sudo git clone https://github.com/username/nama-repo.git
cd nama-repo

Kalau repo private, nanti pakai SSH key ya.

🐍 3. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate

Install dependency:

pip install -r requirements.txt

Kalau belum ada gunicorn, install:

pip install gunicorn

🚀 4. Test aplikasi dulu (penting!)

Misalnya kamu pakai Flask:

python app.py

Atau kalau Django:

python manage.py runserver 0.0.0.0:8000

Akses:

http://IP-VPS:8000

Kalau belum jalan di sini → jangan lanjut dulu.

⚙️ 5. Jalankan dengan Gunicorn

Contoh Flask:

gunicorn --bind 0.0.0.0:8000 app:app

Contoh Django:

gunicorn projectname.wsgi:application

🔁 6. Buat systemd service (biar auto running)
sudo nano /etc/systemd/system/myapp.service

Isi:

[Unit]
Description=Gunicorn instance for myapp
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/nama-repo
Environment="PATH=/var/www/nama-repo/venv/bin"
ExecStart=/var/www/nama-repo/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/nama-repo/myapp.sock \
          app:app

[Install]
WantedBy=multi-user.target

⚠️ Sesuaikan app:app dengan entry point kamu

Jalankan service:

sudo systemctl start myapp
sudo systemctl enable myapp
sudo systemctl status myapp

🌐 7. Setup NGINX (reverse proxy)

Edit config:

sudo nano /etc/nginx/sites-available/myapp

Isi:

server {
    listen 80;
    server_name IP-VPS atau domainkamu.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/nama-repo/myapp.sock;
    }
}

Aktifkan:

sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled

Test:

sudo nginx -t

Restart:

sudo systemctl restart nginx

🔓 8. Buka firewall (kalau pakai UFW)
sudo ufw allow 'Nginx Full'
✅ 9. Akses dari browser
http://IP-VPS

Kalau semua benar → web kamu sudah live 🎉

🔐 (Optional tapi sangat disarankan) SSL HTTPS

Install:

sudo apt install certbot python3-certbot-nginx -y

Jalankan:

sudo certbot --nginx -d domainkamu.com
💡 Tips penting (biar gak nyangkut)

Gunicorn error → cek:

journalctl -u myapp

NGINX error:

sudo tail -f /var/log/nginx/error.log

Permission error:

sudo chown -R www-data:www-data /var/www/nama-repo
🚀 Ringkas alurnya
Clone repo
Setup venv
Install dependency
Test app
Run pakai Gunicorn
Buat service
Hubungkan ke NGINX
(Opsional) SSL

gunicorn --bind 0.0.0.0:85 serve:app