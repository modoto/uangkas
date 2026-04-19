from datetime import datetime, date
from flask import Blueprint, render_template, request, g
from models import User, Wallet, Transaction, TransactionType
from utils.auth import owner_required
from extensions import db

owner_reports_bp = Blueprint('owner_reports', __name__, url_prefix='/owner/reports')


def _parse_filters():
    """Parse filter tanggal dan driver dari query string."""
    today = date.today()
    first_of_month = today.replace(day=1)

    driver_id = request.args.get('driver_id', 'all')
    date_from = request.args.get('date_from', first_of_month.strftime('%Y-%m-%d'))
    date_to   = request.args.get('date_to',   today.strftime('%Y-%m-%d'))
    txn_type  = request.args.get('txn_type',  'all')

    try:
        dt_from = datetime.strptime(date_from, '%Y-%m-%d')
        dt_to   = datetime.strptime(date_to,   '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        dt_from = datetime(today.year, today.month, 1)
        dt_to   = datetime.combine(today, datetime.max.time())

    return driver_id, dt_from, dt_to, txn_type, date_from, date_to


@owner_reports_bp.route('/jenius')
@owner_required
def jenius():
    drivers    = User.query.filter_by(role='driver').order_by(User.name).all()
    txn_types  = (TransactionType.query
                  .filter_by(wallet_type='jenius', is_active=True)
                  .order_by(TransactionType.label).all())

    driver_id, dt_from, dt_to, txn_type_filter, date_from, date_to = _parse_filters()

    query = (db.session.query(Transaction, Wallet, User)
             .join(Wallet, Transaction.wallet_id == Wallet.id)
             .join(User,   Transaction.created_by == User.id)
             .filter(Wallet.wallet_type == 'jenius',
                     Transaction.txn_date >= dt_from,
                     Transaction.txn_date <= dt_to))

    if driver_id != 'all':
        query = query.filter(Wallet.driver_id == driver_id)
    if txn_type_filter != 'all':
        query = query.filter(Transaction.txn_type_id == txn_type_filter)

    rows = query.order_by(Transaction.txn_date.desc()).all()

    return render_template('owner/reports/jenius.html',
                           rows=rows, drivers=drivers,
                           txn_types=txn_types,
                           sel_driver=driver_id,
                           sel_txntype=txn_type_filter,
                           date_from=date_from, date_to=date_to)


@owner_reports_bp.route('/cash')
@owner_required
def cash():
    drivers = User.query.filter_by(role='driver').order_by(User.name).all()
    driver_id, dt_from, dt_to, _, date_from, date_to = _parse_filters()

    # Ambil semua driver jika filter 'all'
    target_drivers = ([User.query.get(driver_id)] if driver_id != 'all'
                      else drivers)

    report_data = []
    for d in target_drivers:
        if not d:
            continue
        cash_wallet = Wallet.query.filter_by(driver_id=d.id, wallet_type='cash').first()
        if not cash_wallet:
            continue

        # Saldo awal: balance_after dari transaksi terakhir sebelum dt_from
        prev_txn = (Transaction.query
                    .filter_by(wallet_id=cash_wallet.id)
                    .filter(Transaction.txn_date < dt_from)
                    .order_by(Transaction.txn_date.desc())
                    .first())
        opening_balance = prev_txn.balance_after if prev_txn else 0

        # Transaksi dalam periode
        txns = (Transaction.query
                .filter_by(wallet_id=cash_wallet.id)
                .filter(Transaction.txn_date >= dt_from,
                        Transaction.txn_date <= dt_to)
                .order_by(Transaction.txn_date.asc())
                .all())

        total_in  = sum(t.amount for t in txns if t.direction == 'credit')
        total_out = sum(t.amount for t in txns if t.direction == 'debit')

        report_data.append({
            'driver':          d,
            'wallet':          cash_wallet,
            'opening_balance': opening_balance,
            'txns':            txns,
            'total_in':        total_in,
            'total_out':       total_out,
            'closing_balance': opening_balance + total_in - total_out,
        })

    return render_template('owner/reports/cash.html',
                           report_data=report_data,
                           drivers=drivers,
                           sel_driver=driver_id,
                           date_from=date_from, date_to=date_to)


@owner_reports_bp.route('/emoney')
@owner_required
def emoney():
    drivers = User.query.filter_by(role='driver').order_by(User.name).all()
    driver_id, dt_from, dt_to, _, date_from, date_to = _parse_filters()

    query = (db.session.query(Transaction, Wallet, User)
             .join(Wallet, Transaction.wallet_id == Wallet.id)
             .join(User,   Transaction.created_by == User.id)
             .filter(Wallet.wallet_type == 'emoney',
                     Transaction.txn_date >= dt_from,
                     Transaction.txn_date <= dt_to))

    if driver_id != 'all':
        query = query.filter(Wallet.driver_id == driver_id)

    rows = query.order_by(Transaction.txn_date.desc()).all()

    return render_template('owner/reports/emoney.html',
                           rows=rows, drivers=drivers,
                           sel_driver=driver_id,
                           date_from=date_from, date_to=date_to)
