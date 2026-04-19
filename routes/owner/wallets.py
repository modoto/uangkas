from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from extensions import db
from models import User, Wallet
from utils.auth import owner_required
from utils.transactions import record_transaction

owner_wallets_bp = Blueprint('owner_wallets', __name__, url_prefix='/owner/wallets')


@owner_wallets_bp.route('/')
@owner_required
def index():
    drivers = User.query.filter_by(role='driver', is_active=True).order_by(User.name).all()
    driver_data = []
    for d in drivers:
        wallets = Wallet.query.filter_by(driver_id=d.id, is_active=True).all()
        wallet_map = {w.wallet_type: w for w in wallets}
        driver_data.append({'driver': d, 'wallets': wallet_map})
    return render_template('owner/wallets/list.html', driver_data=driver_data)


def _process_topup_withdraw(wallet, txn_type_code, direction, label):
    """Helper untuk proses topup/withdrawal dari form."""
    nominal_str = request.form.get('nominal', '').replace('.', '').replace(',', '').strip()
    notes       = request.form.get('notes', '').strip() or None
    date_str    = request.form.get('txn_date', '').strip()
    time_str    = request.form.get('txn_time', '').strip()

    errors = []
    nominal = None
    try:
        nominal = int(nominal_str)
        if nominal < 1000:
            errors.append('Nominal minimal Rp 1.000.')
    except (ValueError, TypeError):
        errors.append('Nominal tidak valid.')

    txn_date = None
    try:
        txn_date = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
        if txn_date > datetime.utcnow():
            errors.append('Tanggal tidak boleh di masa depan.')
    except ValueError:
        errors.append('Tanggal atau jam tidak valid.')

    if errors:
        return errors, None

    try:
        txn = record_transaction(
            wallet        = wallet,
            txn_type_code = txn_type_code,
            direction     = direction,
            amount        = nominal,
            created_by_id = g.current_user.id,
            txn_date      = txn_date,
            notes         = notes,
        )
        db.session.commit()
        return [], txn
    except ValueError as e:
        db.session.rollback()
        return [str(e)], None


@owner_wallets_bp.route('/<wallet_id>/topup', methods=['GET', 'POST'])
@owner_required
def topup(wallet_id):
    wallet = Wallet.query.filter_by(id=wallet_id, is_active=True).first_or_404()
    driver = User.query.get_or_404(wallet.driver_id)

    type_map = {'jenius': 'owner_topup', 'emoney': 'owner_topup_em', 'cash': None}
    txn_code = type_map.get(wallet.wallet_type)
    if not txn_code:
        flash('Top up tidak tersedia untuk wallet ini.', 'error')
        return redirect(url_for('owner_wallets.index'))

    if request.method == 'POST':
        errors, txn = _process_topup_withdraw(wallet, txn_code, 'credit', 'Top Up')
        if errors:
            for e in errors:
                flash(e, 'error')
        else:
            from utils.filters import format_rupiah
            flash(f'Top up {format_rupiah(txn.amount)} ke {wallet.label} berhasil.', 'success')
            return redirect(url_for('owner_wallets.index'))

    now = datetime.now()
    return render_template('owner/wallets/topup.html',
                           wallet=wallet, driver=driver, action='topup',
                           now_date=now.strftime('%Y-%m-%d'),
                           now_time=now.strftime('%H:%M'))


@owner_wallets_bp.route('/<wallet_id>/withdraw', methods=['GET', 'POST'])
@owner_required
def withdraw(wallet_id):
    wallet = Wallet.query.filter_by(id=wallet_id, is_active=True).first_or_404()
    driver = User.query.get_or_404(wallet.driver_id)

    type_map = {'jenius': 'owner_withdrawal', 'emoney': 'owner_withdrawal_em'}
    txn_code = type_map.get(wallet.wallet_type)
    if not txn_code:
        flash('Penarikan tidak tersedia untuk wallet ini.', 'error')
        return redirect(url_for('owner_wallets.index'))

    if request.method == 'POST':
        errors, txn = _process_topup_withdraw(wallet, txn_code, 'debit', 'Penarikan')
        if errors:
            for e in errors:
                flash(e, 'error')
        else:
            from utils.filters import format_rupiah
            flash(f'Penarikan {format_rupiah(txn.amount)} dari {wallet.label} berhasil.', 'success')
            return redirect(url_for('owner_wallets.index'))

    now = datetime.now()
    return render_template('owner/wallets/topup.html',
                           wallet=wallet, driver=driver, action='withdraw',
                           now_date=now.strftime('%Y-%m-%d'),
                           now_time=now.strftime('%H:%M'))
