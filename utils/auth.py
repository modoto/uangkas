import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import session, redirect, url_for, abort, g, current_app, request
from flask_mail import Message
from extensions import db, mail


# ─── Token helpers ───────────────────────────────────────────────────────────

def generate_token():
    """Buat token acak. Return (plaintext, hashed)."""
    plain  = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(plain.encode()).hexdigest()
    return plain, hashed


def hash_token(plain):
    return hashlib.sha256(plain.encode()).hexdigest()


# ─── Session helpers ─────────────────────────────────────────────────────────

def get_current_user():
    """Ambil user dari session token. Return User atau None."""
    from models import User, UserSession
    token = session.get('session_token')
    if not token:
        return None
    sess = UserSession.query.filter_by(session_token=token, is_active=True).first()
    if not sess:
        return None
    user = User.query.filter_by(id=sess.user_id, is_active=True).first()
    return user


def create_user_session(user):
    """Buat session baru dan simpan token ke Flask session cookie."""
    from models import UserSession
    plain_token = secrets.token_urlsafe(64)
    us = UserSession(
        user_id       = user.id,
        session_token = plain_token,
        device_info   = request.headers.get('User-Agent', '')[:255],
        ip_address    = request.remote_addr,
    )
    db.session.add(us)
    db.session.commit()
    session.permanent = True
    session['session_token'] = plain_token
    return us


# ─── Decorators ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        if user.role != 'owner':
            abort(403)
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def driver_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        if user.role != 'driver':
            abort(403)
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


# ─── Magic link helpers ──────────────────────────────────────────────────────

def create_magic_token(user, purpose='login'):
    """Buat dan simpan magic token. Return plaintext token."""
    from models import MagicToken

    cfg = current_app.config
    if purpose == 'login':
        expires_at = datetime.utcnow() + timedelta(minutes=cfg['MAGIC_LINK_LOGIN_MINUTES'])
    else:
        expires_at = datetime.utcnow() + timedelta(hours=cfg['MAGIC_LINK_ONBOARD_HOURS'])

    plain, hashed = generate_token()
    mt = MagicToken(user_id=user.id, token=hashed, purpose=purpose, expires_at=expires_at)
    db.session.add(mt)
    db.session.commit()
    return plain


def is_rate_limited(user):
    """Cek apakah user sudah melebihi batas request magic link dalam 5 menit."""
    from models import MagicToken
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    count = MagicToken.query.filter(
        MagicToken.user_id   == user.id,
        MagicToken.created_at >= five_min_ago,
    ).count()
    return count >= current_app.config['MAGIC_LINK_RATE_LIMIT']


def send_magic_link_email(user, plain_token, purpose='login'):
    """
    Kirim email magic link ke user.

    Jika pengiriman SMTP gagal (mis. credentials belum diisi), magic link
    tetap dicetak ke console/log agar development tidak terhambat.
    Return True jika email terkirim, False jika gagal (tapi link tetap di-log).
    """
    base_url   = current_app.config['APP_BASE_URL']
    verify_url = f"{base_url}/auth/verify/{plain_token}"

    if purpose == 'login':
        subject   = 'Masuk ke Uang Kas — Link Login Anda'
        body_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:24px">
          <h2 style="color:#1E3A5F">Uang Kas</h2>
          <p>Halo <strong>{user.name}</strong>,</p>
          <p>Klik tombol di bawah untuk masuk ke aplikasi Uang Kas:</p>
          <a href="{verify_url}"
             style="display:inline-block;background:#2D5FA8;color:#fff;padding:12px 28px;
                    border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0">
            Masuk ke Uang Kas
          </a>
          <p style="color:#666;font-size:13px">
            Link ini hanya berlaku <strong>15 menit</strong> dan hanya dapat digunakan sekali.<br>
            Jika Anda tidak merasa meminta link ini, abaikan email ini.
          </p>
          <hr style="border:none;border-top:1px solid #eee">
          <p style="color:#999;font-size:12px">Uang Kas — Sistem Monitoring Kas Driver</p>
        </div>
        """
    else:
        subject   = 'Selamat Datang di Uang Kas — Aktifkan Akun Anda'
        body_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:24px">
          <h2 style="color:#1E3A5F">Uang Kas</h2>
          <p>Halo <strong>{user.name}</strong>,</p>
          <p>Anda telah didaftarkan sebagai driver di aplikasi <strong>Uang Kas</strong>.</p>
          <p>Klik tombol di bawah untuk mengaktifkan akun Anda:</p>
          <a href="{verify_url}"
             style="display:inline-block;background:#1A7A5A;color:#fff;padding:12px 28px;
                    border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0">
            Aktifkan Akun Saya
          </a>
          <p style="color:#666;font-size:13px">
            Link ini hanya berlaku <strong>24 jam</strong>.<br>
            Setelah aktif, gunakan email ini untuk login kapan saja.
          </p>
          <hr style="border:none;border-top:1px solid #eee">
          <p style="color:#999;font-size:12px">Uang Kas — Sistem Monitoring Kas Driver</p>
        </div>
        """

    # Validasi awal: jika username/password belum diisi, skip SMTP dan log saja
    mail_user = current_app.config.get('MAIL_USERNAME')
    mail_pass = current_app.config.get('MAIL_PASSWORD')
    smtp_not_configured = (
        not mail_user
        or not mail_pass
        or mail_pass == 'ISI_APP_PASSWORD_GMAIL_DISINI'
        or mail_pass == 'ISI_APP_PASSWORD_YAHOO_DISINI'
    )

    if smtp_not_configured:
        _log_magic_link_to_console(user, verify_url, purpose)
        return False

    msg = Message(subject=subject, recipients=[user.email], html=body_html)
    try:
        mail.send(msg)
        current_app.logger.info(f'Magic link email terkirim ke {user.email}')
        return True
    except Exception as e:
        current_app.logger.error(f'[EMAIL ERROR] Gagal kirim ke {user.email}: {e}')
        # Fallback: tetap tampilkan link di console supaya development tidak terhambat
        _log_magic_link_to_console(user, verify_url, purpose)
        return False


def _log_magic_link_to_console(user, verify_url, purpose):
    """Tampilkan magic link di console (fallback saat email tidak terkirim)."""
    border = '=' * 60
    label  = 'LOGIN' if purpose == 'login' else 'ONBOARDING'
    # Gunakan print biasa agar selalu tampil di terminal
    print(f'\n{border}')
    print(f'  [DEV] MAGIC LINK — {label}')
    print(f'  User   : {user.name} <{user.email}>')
    print(f'  URL    : {verify_url}')
    print(f'{border}\n')
