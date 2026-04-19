import uuid
from datetime import datetime
from extensions import db


class TransactionType(db.Model):
    __tablename__ = 'transaction_types'

    id          = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code        = db.Column(db.String(50),  unique=True, nullable=False)
    label       = db.Column(db.String(100), nullable=False)
    wallet_type = db.Column(db.String(20),  nullable=False)   # 'jenius'|'emoney'|'cash'|'all'
    direction   = db.Column(db.String(10),  nullable=False)   # 'credit'|'debit'|'both'
    is_system   = db.Column(db.Boolean, nullable=False, default=False)
    is_active   = db.Column(db.Boolean, nullable=False, default=True)
    sort_order  = db.Column(db.SmallInteger, nullable=False, default=99)
    created_by  = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    transactions = db.relationship('Transaction', backref='txn_type', lazy='dynamic')

    def __repr__(self):
        return f'<TransactionType {self.code}>'

    @property
    def is_deletable(self):
        return not self.is_system and self.transactions.count() == 0

    @classmethod
    def get_by_code(cls, code):
        return cls.query.filter_by(code=code).first()

    @classmethod
    def for_wallet(cls, wallet_type):
        """Ambil jenis transaksi aktif untuk wallet tertentu (untuk dropdown driver)."""
        return cls.query.filter(
            cls.is_active == True,
            db.or_(cls.wallet_type == wallet_type, cls.wallet_type == 'all'),
            cls.is_system == False
        ).order_by(cls.sort_order, cls.label).all()


# ─── Seed data ───────────────────────────────────────────────────────────────

SEED_TRANSACTION_TYPES = [
    {'code': 'owner_topup',         'label': 'Top Up Saldo',       'wallet_type': 'jenius', 'direction': 'credit', 'sort_order': 1},
    {'code': 'owner_topup_em',      'label': 'Top Up eMoney',      'wallet_type': 'emoney', 'direction': 'credit', 'sort_order': 2},
    {'code': 'owner_withdrawal',    'label': 'Penarikan Saldo',    'wallet_type': 'jenius', 'direction': 'debit',  'sort_order': 3},
    {'code': 'owner_withdrawal_em', 'label': 'Penarikan eMoney',   'wallet_type': 'emoney', 'direction': 'debit',  'sort_order': 4},
    {'code': 'atm_withdrawal',      'label': 'Tarik ATM',          'wallet_type': 'jenius', 'direction': 'debit',  'sort_order': 5},
    {'code': 'fuel_payment',        'label': 'Bayar Bensin',       'wallet_type': 'jenius', 'direction': 'debit',  'sort_order': 6},
    {'code': 'cash_in',             'label': 'Uang Cash Masuk',    'wallet_type': 'cash',   'direction': 'credit', 'sort_order': 7},
    {'code': 'cash_out',            'label': 'Pengeluaran Cash',   'wallet_type': 'cash',   'direction': 'debit',  'sort_order': 8},
    {'code': 'emoney_usage',        'label': 'Pemakaian eMoney',   'wallet_type': 'emoney', 'direction': 'debit',  'sort_order': 9},
    {'code': 'jenius_misc',         'label': 'Lain-lain Jenius',   'wallet_type': 'jenius', 'direction': 'both',   'sort_order': 10},
]
