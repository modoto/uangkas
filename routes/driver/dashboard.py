from flask import Blueprint, render_template, g
from models import Wallet, Transaction
from utils.auth import driver_required

driver_dashboard_bp = Blueprint('driver_dashboard', __name__, url_prefix='/driver')


@driver_dashboard_bp.route('/')
@driver_required
def index():
    wallets = Wallet.query.filter_by(driver_id=g.current_user.id, is_active=True).all()
    wallet_map = {w.wallet_type: w for w in wallets}

    wallet_ids = [w.id for w in wallets]
    recent_txns = (Transaction.query
                   .filter(Transaction.wallet_id.in_(wallet_ids))
                   .order_by(Transaction.txn_date.desc())
                   .limit(5).all())

    return render_template('driver/dashboard.html',
                           wallets=wallet_map,
                           recent_txns=recent_txns)
