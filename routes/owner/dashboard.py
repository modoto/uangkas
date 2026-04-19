from datetime import datetime, timedelta, date
from collections import defaultdict
from flask import Blueprint, render_template, g
from sqlalchemy import func
from extensions import db
from utils.auth import owner_required
from models import User, Transaction, Wallet, TransactionType

owner_dashboard_bp = Blueprint('owner_dashboard', __name__, url_prefix='/owner')


def _chart_data(all_wallets):
    if not all_wallets:
        empty30 = [0] * 30
        return dict(
            balance_labels=[], balance_jenius=empty30,
            balance_emoney=empty30, balance_cash=empty30,
            cat_labels=[], cat_data=[],
        )

    wallet_ids = [w.id for w in all_wallets]

    # ── Grafik saldo harian (30 hari terakhir) ──────────────────
    today     = date.today()
    start     = today - timedelta(days=29)
    date_range = [start + timedelta(days=i) for i in range(30)]

    # Ambil semua transaksi (tanpa batas tanggal agar baseline benar)
    all_txns = (Transaction.query
                .filter(Transaction.wallet_id.in_(wallet_ids))
                .order_by(Transaction.txn_date)
                .all())

    txns_by_wallet = defaultdict(list)
    for t in all_txns:
        txns_by_wallet[t.wallet_id].append(t)

    wallets_by_type = defaultdict(list)
    for w in all_wallets:
        wallets_by_type[w.wallet_type].append(w)

    type_daily = {}
    for wtype, wallets in wallets_by_type.items():
        daily = []
        for d in date_range:
            day_end = datetime(d.year, d.month, d.day, 23, 59, 59)
            total = 0
            for w in wallets:
                balance = 0
                for t in txns_by_wallet[w.id]:
                    if t.txn_date <= day_end:
                        balance = t.balance_after
                    else:
                        break
                total += balance
            daily.append(total)
        type_daily[wtype] = daily

    # ── Grafik kategori pengeluaran (semua waktu, debit non-cancelled) ──
    cat_rows = (db.session.query(
                    TransactionType.label,
                    func.sum(Transaction.amount).label('total')
                )
                .join(TransactionType, Transaction.txn_type_id == TransactionType.id)
                .filter(
                    Transaction.wallet_id.in_(wallet_ids),
                    Transaction.direction == 'debit',
                    Transaction.is_cancelled == False,
                )
                .group_by(TransactionType.id, TransactionType.label)
                .order_by(func.sum(Transaction.amount).desc())
                .all())

    return dict(
        balance_labels =[d.strftime('%d/%m') for d in date_range],
        balance_jenius  = type_daily.get('jenius', [0] * 30),
        balance_emoney  = type_daily.get('emoney', [0] * 30),
        balance_cash    = type_daily.get('cash',   [0] * 30),
        cat_labels      = [r.label for r in cat_rows],
        cat_data        = [int(r.total) for r in cat_rows],
    )


@owner_dashboard_bp.route('/')
@owner_required
def index():
    drivers = User.query.filter_by(role='driver').order_by(User.name).all()

    driver_data = []
    all_wallets = []
    for d in drivers:
        wallets = Wallet.query.filter_by(driver_id=d.id, is_active=True).all()
        wallet_map = {w.wallet_type: w for w in wallets}
        driver_data.append({'driver': d, 'wallets': wallet_map})
        all_wallets.extend(wallets)

    recent_txns = (Transaction.query
                   .join(Wallet, Transaction.wallet_id == Wallet.id)
                   .join(User,   Transaction.created_by == User.id)
                   .order_by(Transaction.txn_date.desc())
                   .limit(10).all())

    charts = _chart_data(all_wallets)

    return render_template('owner/dashboard.html',
                           driver_data=driver_data,
                           recent_txns=recent_txns,
                           charts=charts)
