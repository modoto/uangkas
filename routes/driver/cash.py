from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from extensions import db
from models import Wallet
from utils.auth import driver_required
from utils.transactions import record_transaction

driver_cash_bp = Blueprint('driver_cash', __name__, url_prefix='/driver/cash')


@driver_cash_bp.route('/record', methods=['GET', 'POST'])
@driver_required
def record():
    cash_wallet = Wallet.query.filter_by(
        driver_id=g.current_user.id, wallet_type='cash', is_active=True
    ).first_or_404()

    if request.method == 'POST':
        nominal_str = request.form.get('nominal', '').replace('.', '').strip()
        date_str    = request.form.get('txn_date', '').strip()
        time_str    = request.form.get('txn_time', '').strip()
        notes       = request.form.get('notes', '').strip()

        errors = []
        nominal = None
        try:
            nominal = int(nominal_str)
            if nominal < 500:
                errors.append('Nominal minimal Rp 500.')
        except (ValueError, TypeError):
            errors.append('Nominal tidak valid.')

        if len(notes) < 3:
            errors.append('Catatan wajib diisi (minimal 3 karakter) — tuliskan untuk apa uang digunakan.')

        txn_date = None
        try:
            txn_date = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
            if txn_date > datetime.now():
                errors.append('Tanggal tidak boleh di masa depan.')
        except ValueError:
            errors.append('Tanggal atau jam tidak valid.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('driver/cash_record.html',
                                   wallet=cash_wallet, form=request.form)

        try:
            record_transaction(cash_wallet, 'cash_out', 'debit',
                               nominal, g.current_user.id, txn_date, notes)
            db.session.commit()
            from utils.filters import format_rupiah
            flash(f'Pengeluaran cash {format_rupiah(nominal)} berhasil dicatat.', 'success')
            return redirect(url_for('driver_dashboard.index'))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'error')

    now = datetime.now()
    return render_template('driver/cash_record.html',
                           wallet=cash_wallet,
                           form={'txn_date': now.strftime('%Y-%m-%d'),
                                 'txn_time': now.strftime('%H:%M')})
