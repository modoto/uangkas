from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from extensions import db
from models import User, Wallet, UserSession, Transaction
from utils.auth import owner_required, create_magic_token, send_magic_link_email

owner_drivers_bp = Blueprint('owner_drivers', __name__, url_prefix='/owner/drivers')


@owner_drivers_bp.route('/')
@owner_required
def index():
    drivers = (User.query.filter_by(role='driver')
               .order_by(User.name).all())
    driver_data = []
    for d in drivers:
        wallets  = Wallet.query.filter_by(driver_id=d.id, is_active=True).all()
        wallet_map = {w.wallet_type: w for w in wallets}
        sessions = (UserSession.query
                    .filter_by(user_id=d.id, is_active=True)
                    .order_by(UserSession.created_at.desc())
                    .all())
        driver_data.append({'driver': d, 'wallets': wallet_map, 'sessions': sessions})
    return render_template('owner/drivers/list.html', driver_data=driver_data)


@owner_drivers_bp.route('/add', methods=['GET', 'POST'])
@owner_required
def add():
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()

        errors = []
        if len(name) < 2:
            errors.append('Nama minimal 2 karakter.')
        if not email or '@' not in email:
            errors.append('Format email tidak valid.')
        if User.query.filter_by(email=email).first():
            errors.append('Email sudah terdaftar.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('owner/drivers/add.html',
                                   name=name, email=email)

        driver = User(name=name, email=email, role='driver')
        db.session.add(driver)
        db.session.flush()   # dapatkan driver.id

        # Buat 3 wallet otomatis
        for wtype, label_prefix in [('jenius', 'Jenius'), ('emoney', 'eMoney'), ('cash', 'Uang Cash')]:
            w = Wallet(driver_id=driver.id,
                       wallet_type=wtype,
                       label=f'{label_prefix} — {name}')
            db.session.add(w)

        db.session.commit()

        # Kirim magic link onboarding
        plain = create_magic_token(driver, purpose='onboarding')
        sent  = send_magic_link_email(driver, plain, purpose='onboarding')

        msg = f'Driver {name} berhasil ditambahkan.'
        msg += ' Email aktivasi telah dikirim.' if sent else ' (Gagal kirim email, kirim ulang manual.)'
        flash(msg, 'success')
        return redirect(url_for('owner_drivers.index'))

    return render_template('owner/drivers/add.html', name='', email='')


@owner_drivers_bp.route('/<driver_id>/edit', methods=['GET', 'POST'])
@owner_required
def edit(driver_id):
    driver = User.query.filter_by(id=driver_id, role='driver').first_or_404()

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        is_active = request.form.get('is_active') == '1'

        if len(name) < 2:
            flash('Nama minimal 2 karakter.', 'error')
            return render_template('owner/drivers/edit.html', driver=driver)

        was_active = driver.is_active
        driver.name      = name
        driver.is_active = is_active
        driver.updated_at = datetime.utcnow()

        # Jika dinonaktifkan, terminate semua session aktif
        if was_active and not is_active:
            UserSession.query.filter_by(
                user_id=driver.id, is_active=True
            ).update({
                'is_active':     False,
                'terminated_at': datetime.utcnow(),
                'terminated_by': g.current_user.id,
            })

        db.session.commit()
        flash(f'Data driver {name} berhasil diperbarui.', 'success')
        return redirect(url_for('owner_drivers.index'))

    return render_template('owner/drivers/edit.html', driver=driver)


@owner_drivers_bp.route('/sessions/<session_id>/terminate', methods=['POST'])
@owner_required
def terminate_session(session_id):
    """Terminate session driver langsung dari halaman daftar driver."""
    us = UserSession.query.filter_by(id=session_id, is_active=True).first_or_404()
    if us.user_id == g.current_user.id:
        flash('Tidak dapat menterminasi session sendiri.', 'error')
        return redirect(url_for('owner_drivers.index'))
    us.is_active     = False
    us.terminated_at = datetime.utcnow()
    us.terminated_by = g.current_user.id
    db.session.commit()
    driver = User.query.get(us.user_id)
    flash(f'Session {driver.name} berhasil diterminasi.', 'success')
    return redirect(url_for('owner_drivers.index'))


@owner_drivers_bp.route('/<driver_id>/resend', methods=['POST'])
@owner_required
def resend(driver_id):
    from models import MagicToken
    driver = User.query.filter_by(id=driver_id, role='driver', is_active=True).first_or_404()

    # Invalidasi token onboarding lama
    MagicToken.query.filter_by(
        user_id=driver.id, purpose='onboarding', used_at=None
    ).update({'used_at': datetime.utcnow()})
    db.session.commit()

    plain = create_magic_token(driver, purpose='onboarding')
    sent  = send_magic_link_email(driver, plain, purpose='onboarding')

    if sent:
        flash(f'Magic link onboarding dikirim ulang ke {driver.email}.', 'success')
    else:
        flash('Gagal mengirim email. Periksa konfigurasi SMTP.', 'error')

    return redirect(url_for('owner_drivers.index'))


@owner_drivers_bp.route('/<driver_id>/delete', methods=['POST'])
@owner_required
def delete(driver_id):
    from models import MagicToken
    driver = User.query.filter_by(id=driver_id, role='driver').first_or_404()

    # Blokir jika ada riwayat transaksi
    txn_count = (Transaction.query
                 .join(Wallet, Transaction.wallet_id == Wallet.id)
                 .filter(Wallet.driver_id == driver.id)
                 .count())
    if txn_count > 0:
        flash(
            f'Driver {driver.name} tidak dapat dihapus karena sudah memiliki '
            f'{txn_count} riwayat transaksi. Nonaktifkan driver jika tidak lagi digunakan.',
            'error'
        )
        return redirect(url_for('owner_drivers.edit', driver_id=driver.id))

    name = driver.name

    # Hapus session, token, wallet, lalu user
    UserSession.query.filter_by(user_id=driver.id).delete()
    MagicToken.query.filter_by(user_id=driver.id).delete()
    Wallet.query.filter_by(driver_id=driver.id).delete()
    db.session.delete(driver)
    db.session.commit()

    flash(f'Driver {name} berhasil dihapus.', 'success')
    return redirect(url_for('owner_drivers.index'))
