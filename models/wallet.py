import uuid
from datetime import datetime
from extensions import db

WALLET_TYPES = ['jenius', 'emoney', 'cash']

WALLET_LABELS = {
    'jenius': 'Jenius',
    'emoney': 'eMoney',
    'cash':   'Uang Cash',
}


class Wallet(db.Model):
    __tablename__ = 'wallets'

    id              = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id       = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    wallet_type     = db.Column(db.String(20), nullable=False)     # 'jenius' | 'emoney' | 'cash'
    label           = db.Column(db.String(100), nullable=False)
    current_balance = db.Column(db.BigInteger, nullable=False, default=0)
    is_active       = db.Column(db.Boolean, nullable=False, default=True)
    created_at      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('driver_id', 'wallet_type', name='uq_wallet_driver_type'),
    )

    transactions = db.relationship('Transaction', backref='wallet', lazy='dynamic')

    def __repr__(self):
        return f'<Wallet {self.label} Rp {self.current_balance}>'

    def credit(self, amount):
        """Tambah saldo."""
        self.current_balance += amount

    def debit(self, amount):
        """Kurangi saldo. Raise ValueError jika tidak cukup."""
        if self.current_balance < amount:
            raise ValueError(
                f'Saldo tidak mencukupi. Tersedia: Rp {self.current_balance:,.0f}'.replace(',', '.')
            )
        self.current_balance -= amount
