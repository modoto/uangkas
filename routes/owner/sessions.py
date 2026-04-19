from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, g, abort, session
from extensions import db
from models import UserSession, User
from utils.auth import owner_required

owner_sessions_bp = Blueprint('owner_sessions', __name__, url_prefix='/owner/sessions')


@owner_sessions_bp.route('/')
@owner_required
def index():
    active = (UserSession.query
              .join(User, UserSession.user_id == User.id)
              .filter(UserSession.is_active == True)
              .order_by(UserSession.created_at.desc())
              .all())

    # Cari ID session owner yang sedang dipakai sekarang
    current_token = session.get('session_token')
    current_sess  = UserSession.query.filter_by(session_token=current_token).first()
    current_id    = current_sess.id if current_sess else None

    owner_sessions  = [s for s in active if s.user.role == 'owner']
    driver_sessions = [s for s in active if s.user.role == 'driver']

    return render_template('owner/sessions.html',
                           owner_sessions=owner_sessions,
                           driver_sessions=driver_sessions,
                           current_id=current_id)


@owner_sessions_bp.route('/terminate-others', methods=['POST'])
@owner_required
def terminate_others():
    current_token = session.get('session_token')
    current_sess  = UserSession.query.filter_by(session_token=current_token).first()
    if not current_sess:
        abort(403)

    count = (UserSession.query
             .filter(UserSession.user_id == g.current_user.id,
                     UserSession.is_active == True,
                     UserSession.id != current_sess.id)
             .update({
                 'is_active':     False,
                 'terminated_at': datetime.utcnow(),
                 'terminated_by': g.current_user.id,
             }))
    db.session.commit()

    if count:
        flash(f'{count} session owner lainnya berhasil ditutup.', 'success')
    else:
        flash('Tidak ada session lain yang perlu ditutup.', 'info')
    return redirect(url_for('owner_sessions.index'))


@owner_sessions_bp.route('/<session_id>/terminate', methods=['POST'])
@owner_required
def terminate(session_id):
    us = UserSession.query.filter_by(id=session_id, is_active=True).first_or_404()

    if us.user_id == g.current_user.id:
        abort(403)

    us.is_active     = False
    us.terminated_at = datetime.utcnow()
    us.terminated_by = g.current_user.id
    db.session.commit()

    user = User.query.get(us.user_id)
    flash(f'Session {user.name} berhasil diterminasi.', 'success')
    return redirect(url_for('owner_sessions.index'))
