import uuid
from datetime import datetime
from extensions import db


class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id             = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id        = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_token  = db.Column(db.String(255), unique=True, nullable=False)
    device_info    = db.Column(db.String(255), nullable=True)
    ip_address     = db.Column(db.String(45),  nullable=True)
    is_active      = db.Column(db.Boolean, nullable=False, default=True)
    created_at     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    terminated_at  = db.Column(db.DateTime, nullable=True)
    terminated_by  = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    terminator = db.relationship('User', foreign_keys=[terminated_by], backref='terminated_sessions')

    def __repr__(self):
        return f'<UserSession user={self.user_id} active={self.is_active}>'

    def terminate(self, by_user_id):
        self.is_active     = False
        self.terminated_at = datetime.utcnow()
        self.terminated_by = by_user_id
        db.session.commit()
