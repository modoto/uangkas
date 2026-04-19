from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, g)
from extensions import db
from models import User, MagicToken
from utils.auth import (hash_token, create_magic_token, is_rate_limited,
                         send_magic_link_email, create_user_session, get_current_user)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Sudah login → redirect ke dashboard
    user = get_current_user()
    if user:
        return redirect(url_for('owner_dashboard.index') if user.is_owner
                        else url_for('driver_dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email or '@' not in email:
            flash('Masukkan alamat email yang valid.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        # Respon generik — tidak membocorkan apakah email terdaftar
        if not user or not user.is_active:
            flash('Jika email terdaftar, link login akan dikirimkan ke inbox Anda.', 'info')
            return render_template('auth/login.html')

        if is_rate_limited(user):
            flash('Terlalu banyak permintaan. Coba lagi dalam beberapa menit.', 'warning')
            return render_template('auth/login.html')

        plain_token = create_magic_token(user, purpose='login')
        send_magic_link_email(user, plain_token, purpose='login')

        flash('Link login telah dikirimkan ke email Anda. Silakan cek inbox (dan folder Spam).', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@auth_bp.route('/verify/<token>')
def verify(token):
    hashed = hash_token(token)
    mt = MagicToken.query.filter_by(token=hashed).first()

    if not mt or not mt.is_valid:
        flash('Link tidak valid atau sudah kedaluwarsa. Silakan minta link baru.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(id=mt.user_id, is_active=True).first()
    if not user:
        flash('Akun tidak aktif. Hubungi administrator.', 'error')
        return redirect(url_for('auth.login'))

    mt.consume()
    create_user_session(user)

    flash(f'Selamat datang, {user.name}!', 'success')
    if user.is_owner:
        return redirect(url_for('owner_dashboard.index'))
    return redirect(url_for('driver_dashboard.index'))


@auth_bp.route('/logout', methods=['POST'])
def logout():
    from models import UserSession
    token = session.get('session_token')
    if token:
        us = UserSession.query.filter_by(session_token=token).first()
        if us:
            us.is_active    = False
            us.terminated_at = __import__('datetime').datetime.utcnow()
            db.session.commit()
    session.clear()
    flash('Anda telah berhasil keluar.', 'success')
    return redirect(url_for('auth.login'))
