import uuid
from datetime import datetime
from extensions import db


class MagicToken(db.Model):
    __tablename__ = 'magic_tokens'

    id         = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id    = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token      = db.Column(db.String(128), unique=True, nullable=False)   # SHA-256 hash
    purpose    = db.Column(db.String(20),  nullable=False)                # 'login' | 'onboarding'
    expires_at = db.Column(db.DateTime,   nullable=False)
    used_at    = db.Column(db.DateTime,   nullable=True)
    created_at = db.Column(db.DateTime,   nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<MagicToken user={self.user_id} purpose={self.purpose}>'

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > datetime.utcnow()

    def consume(self):
        self.used_at = datetime.utcnow()
        db.session.commit()
