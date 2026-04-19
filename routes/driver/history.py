from flask import Blueprint, render_template, request, g
from models import Wallet, Transaction
from utils.auth import driver_required

driver_history_bp = Blueprint('driver_history', __name__, url_prefix='/driver/history')

PER_PAGE = 20


@driver_history_bp.route('/jenius')
@driver_required
def jenius():
    wallet = Wallet.query.filter_by(
        driver_id=g.current_user.id, wallet_type='jenius', is_active=True
    ).first_or_404()

    page = request.args.get('page', 1, type=int)
    txns = (Transaction.query
            .filter_by(wallet_id=wallet.id)
            .order_by(Transaction.txn_date.desc())
            .paginate(page=page, per_page=PER_PAGE, error_out=False))

    return render_template('driver/history.html',
                           wallet=wallet, txns=txns,
                           wallet_type='jenius',
                           title='Riwayat Transaksi Jenius')


@driver_history_bp.route('/cash')
@driver_required
def cash():
    wallet = Wallet.query.filter_by(
        driver_id=g.current_user.id, wallet_type='cash', is_active=True
    ).first_or_404()

    page = request.args.get('page', 1, type=int)
    txns = (Transaction.query
            .filter_by(wallet_id=wallet.id)
            .order_by(Transaction.txn_date.desc())
            .paginate(page=page, per_page=PER_PAGE, error_out=False))

    # Hitung ringkasan
    all_txns = Transaction.query.filter_by(wallet_id=wallet.id).all()
    total_in  = sum(t.amount for t in all_txns if t.direction == 'credit')
    total_out = sum(t.amount for t in all_txns if t.direction == 'debit')

    return render_template('driver/history.html',
                           wallet=wallet, txns=txns,
                           wallet_type='cash',
                           title='Riwayat Uang Cash',
                           total_in=total_in, total_out=total_out)
