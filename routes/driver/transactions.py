from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from extensions import db
from models import Wallet, Transaction
from utils.auth import driver_required
from utils.transactions import record_transaction

driver_transactions_bp = Blueprint('driver_transactions', __name__,
                                   url_prefix='/driver/transactions')


def _get_own_txn(txn_id):
    """
    Ambil transaksi milik driver yang sedang login.
    404 jika tidak ada atau wallet bukan milik driver ini.
    """
    txn = Transaction.query.get_or_404(txn_id)
    wallet = Wallet.query.filter_by(
        id=txn.wallet_id, driver_id=g.current_user.id, is_active=True
    ).first_or_404()
    return txn, wallet


@driver_transactions_bp.route('/<txn_id>/edit', methods=['GET', 'POST'])
@driver_required
def edit(txn_id):
    txn, wallet = _get_own_txn(txn_id)

    # Hanya transaksi yang dibuat oleh driver ini yang boleh diedit
    if txn.created_by != g.current_user.id:
        flash('Anda hanya bisa mengedit transaksi yang Anda catat sendiri.', 'error')
        return redirect(request.referrer or url_for('driver_history.jenius'))

    if txn.is_cancelled:
        flash('Transaksi yang sudah dibatalkan tidak bisa diedit.', 'error')
        return redirect(request.referrer or url_for('driver_history.jenius'))

    if request.method == 'POST':
        notes    = request.form.get('notes', '').strip() or None
        date_str = request.form.get('txn_date', '').strip()
        time_str = request.form.get('txn_time', '').strip()

        errors = []
        txn_date = None
        try:
            txn_date = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
            if txn_date > datetime.utcnow():
                errors.append('Tanggal tidak boleh di masa depan.')
        except ValueError:
            errors.append('Tanggal atau jam tidak valid.')

        if errors:
            for e in errors:
                flash(e, 'error')
        else:
            txn.notes    = notes
            txn.txn_date = txn_date
            db.session.commit()
            flash('Catatan transaksi berhasil diperbarui.', 'success')
            return _redirect_to_history(wallet)

    local_dt = txn.txn_date  # stored as UTC, show as-is
    return render_template('driver/txn_edit.html',
                           txn=txn, wallet=wallet,
                           now_date=local_dt.strftime('%Y-%m-%d'),
                           now_time=local_dt.strftime('%H:%M'))


@driver_transactions_bp.route('/<txn_id>/reverse', methods=['POST'])
@driver_required
def reverse(txn_id):
    txn, wallet = _get_own_txn(txn_id)

    # Validasi: hanya transaksi yang dibuat driver sendiri
    if txn.created_by != g.current_user.id:
        flash('Anda hanya bisa membatalkan transaksi yang Anda catat sendiri.', 'error')
        return _redirect_to_history(wallet)

    if txn.is_cancelled:
        flash('Transaksi ini sudah dibatalkan sebelumnya.', 'error')
        return _redirect_to_history(wallet)

    # Jangan izinkan reversal transaksi ATM (linked ke transaksi lain dua arah)
    if txn.linked_txn_id is not None:
        linked = Transaction.query.get(txn.linked_txn_id)
        if linked and linked.linked_txn_id == txn.id:
            flash('Transaksi ATM tidak bisa dibatalkan langsung. Hubungi owner.', 'error')
            return _redirect_to_history(wallet)

    # Tentukan arah kebalikan
    reverse_direction = 'credit' if txn.direction == 'debit' else 'debit'
    reverse_notes = f'[BATAL] {txn.notes or txn.txn_type.label}'

    try:
        rev_txn = record_transaction(
            wallet        = wallet,
            txn_type_code = txn.txn_type.code,
            direction     = reverse_direction,
            amount        = txn.amount,
            created_by_id = g.current_user.id,
            txn_date      = datetime.utcnow(),
            notes         = reverse_notes,
        )
        db.session.flush()
        rev_txn.linked_txn_id = txn.id
        txn.is_cancelled = True
        db.session.commit()
        flash('Transaksi berhasil dibatalkan. Saldo telah disesuaikan.', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(str(e), 'error')

    return _redirect_to_history(wallet)


def _redirect_to_history(wallet):
    if wallet.wallet_type == 'cash':
        return redirect(url_for('driver_history.cash'))
    return redirect(url_for('driver_history.jenius'))
