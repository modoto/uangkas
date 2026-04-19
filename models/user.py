import uuid
from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email      = db.Column(db.String(255), unique=True, nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    role       = db.Column(db.String(10),  nullable=False)   # 'owner' | 'driver'
    is_active  = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    # Relationships
    wallets         = db.relationship('Wallet',          backref='driver',     lazy='dynamic',
                                      foreign_keys='Wallet.driver_id')
    magic_tokens    = db.relationship('MagicToken',      backref='user',       lazy='dynamic')
    sessions        = db.relationship('UserSession',     backref='user',       lazy='dynamic',
                                      foreign_keys='UserSession.user_id')
    transactions    = db.relationship('Transaction',     backref='creator',    lazy='dynamic',
                                      foreign_keys='Transaction.created_by')
    txn_types_made  = db.relationship('TransactionType', backref='creator',    lazy='dynamic',
                                      foreign_keys='TransactionType.created_by')

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

    @property
    def is_owner(self):
        return self.role == 'owner'

    @property
    def is_driver(self):
        return self.role == 'driver'

    def get_wallet(self, wallet_type):
        return self.wallets.filter_by(wallet_type=wallet_type, is_active=True).first()
