from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from extensions import db
from models import Wallet, TransactionType
from utils.auth import driver_required
from utils.transactions import record_atm_withdrawal, record_transaction

driver_jenius_bp = Blueprint('driver_jenius', __name__, url_prefix='/driver/jenius')


@driver_jenius_bp.route('/record', methods=['GET', 'POST'])
@driver_required
def record():
    jenius_wallet = Wallet.query.filter_by(
        driver_id=g.current_user.id, wallet_type='jenius', is_active=True
    ).first_or_404()

    # Jenis transaksi custom dari owner (non-system, wallet jenius/all)
    custom_types = TransactionType.for_wallet('jenius')

    if request.method == 'POST':
        txn_choice   = request.form.get('txn_choice', '')   # 'atm'|'fuel'|'misc'|'other'
        nominal_str  = request.form.get('nominal', '').replace('.', '').strip()
        date_str     = request.form.get('txn_date', '').strip()
        time_str     = request.form.get('txn_time', '').strip()
        notes        = request.form.get('notes', '').strip() or None
        other_type   = request.form.get('other_type', '').strip()
        misc_dir     = request.form.get('misc_direction', 'debit')   # 'debit'|'credit'

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
            if txn_date > datetime.now():
                errors.append('Tanggal tidak boleh di masa depan.')
        except ValueError:
            errors.append('Tanggal atau jam tidak valid.')

        if txn_choice not in ('atm', 'fuel', 'misc', 'other'):
            errors.append('Pilih jenis transaksi.')

        if txn_choice == 'other' and not other_type:
            errors.append('Pilih jenis transaksi lainnya.')

        if txn_choice == 'misc' and misc_dir not in ('debit', 'credit'):
            errors.append('Pilih arah transaksi (keluar/masuk).')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('driver/jenius_record.html',
                                   wallet=jenius_wallet,
                                   custom_types=custom_types,
                                   form=request.form)

        try:
            if txn_choice == 'atm':
                cash_wallet = Wallet.query.filter_by(
                    driver_id=g.current_user.id, wallet_type='cash', is_active=True
                ).first_or_404()
                record_atm_withdrawal(jenius_wallet, cash_wallet, nominal,
                                      g.current_user.id, txn_date, notes)
                from utils.filters import format_rupiah
                flash(f'Tarik ATM {format_rupiah(nominal)} berhasil. '
                      f'Saldo Cash bertambah {format_rupiah(nominal)}.', 'success')

            elif txn_choice == 'fuel':
                record_transaction(jenius_wallet, 'fuel_payment', 'debit',
                                   nominal, g.current_user.id, txn_date, notes)
                db.session.commit()
                from utils.filters import format_rupiah
                flash(f'Pembayaran bensin {format_rupiah(nominal)} berhasil dicatat.', 'success')

            elif txn_choice == 'misc':
                record_transaction(jenius_wallet, 'jenius_misc', misc_dir,
                                   nominal, g.current_user.id, txn_date, notes)
                db.session.commit()
                from utils.filters import format_rupiah
                dir_label = 'masuk' if misc_dir == 'credit' else 'keluar'
                flash(f'Lain-lain {format_rupiah(nominal)} ({dir_label}) berhasil dicatat.', 'success')

            else:
                # Jenis custom (owner-added)
                tt = TransactionType.query.filter_by(id=other_type, is_active=True).first()
                if not tt:
                    flash('Jenis transaksi tidak valid.', 'error')
                    return render_template('driver/jenius_record.html',
                                           wallet=jenius_wallet,
                                           custom_types=custom_types,
                                           form=request.form)
                record_transaction(jenius_wallet, tt.code, tt.direction if tt.direction != 'both' else 'debit',
                                   nominal, g.current_user.id, txn_date, notes)
                db.session.commit()
                from utils.filters import format_rupiah
                flash(f'{tt.label} {format_rupiah(nominal)} berhasil dicatat.', 'success')

        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'error')
            return render_template('driver/jenius_record.html',
                                   wallet=jenius_wallet,
                                   custom_types=custom_types,
                                   form=request.form)

        return redirect(url_for('driver_dashboard.index'))

    now = datetime.now()
    return render_template('driver/jenius_record.html',
                           wallet=jenius_wallet,
                           custom_types=custom_types,
                           form={'txn_date': now.strftime('%Y-%m-%d'),
                                 'txn_time': now.strftime('%H:%M')})
