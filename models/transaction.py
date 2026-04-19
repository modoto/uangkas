import uuid
from datetime import datetime
from extensions import db


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id             = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_id      = db.Column(db.String(36), db.ForeignKey('wallets.id',           ondelete='RESTRICT'), nullable=False)
    txn_type_id    = db.Column(db.String(36), db.ForeignKey('transaction_types.id', ondelete='RESTRICT'), nullable=False)
    created_by     = db.Column(db.String(36), db.ForeignKey('users.id',             ondelete='RESTRICT'), nullable=False)
    direction      = db.Column(db.String(10), nullable=False)    # 'credit' | 'debit'
    amount         = db.Column(db.BigInteger, nullable=False)
    balance_before = db.Column(db.BigInteger, nullable=False)
    balance_after  = db.Column(db.BigInteger, nullable=False)
    notes          = db.Column(db.Text,       nullable=True)
    txn_date       = db.Column(db.DateTime,   nullable=False)
    linked_txn_id  = db.Column(db.String(36), db.ForeignKey('transactions.id'), nullable=True)
    is_cancelled   = db.Column(db.Boolean,    nullable=False, default=False)
    created_at     = db.Column(db.DateTime,   nullable=False, default=datetime.utcnow)

    linked_txn = db.relationship('Transaction', remote_side='Transaction.id',
                                  foreign_keys=[linked_txn_id], backref='linked_from')

    def __repr__(self):
        return f'<Transaction {self.direction} Rp {self.amount} wallet={self.wallet_id}>'

    @property
    def is_credit(self):
        return self.direction == 'credit'

    @property
    def signed_amount(self):
        """Positif untuk kredit, negatif untuk debit."""
        return self.amount if self.is_credit else -self.amount
