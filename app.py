import os
from flask import Flask, render_template
from config import config
from extensions import db, csrf, mail


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Extensions
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Jinja2 filters
    from utils.filters import format_rupiah, format_datetime, format_date
    app.jinja_env.filters['rupiah']   = format_rupiah
    app.jinja_env.filters['dtformat'] = format_datetime
    app.jinja_env.filters['dformat']  = format_date

    # Register blueprints
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from routes.owner.dashboard  import owner_dashboard_bp
    from routes.owner.drivers    import owner_drivers_bp
    from routes.owner.wallets    import owner_wallets_bp
    from routes.owner.txn_types  import owner_txntypes_bp
    from routes.owner.reports    import owner_reports_bp
    from routes.owner.sessions   import owner_sessions_bp

    app.register_blueprint(owner_dashboard_bp)
    app.register_blueprint(owner_drivers_bp)
    app.register_blueprint(owner_wallets_bp)
    app.register_blueprint(owner_txntypes_bp)
    app.register_blueprint(owner_reports_bp)
    app.register_blueprint(owner_sessions_bp)

    from routes.driver.dashboard     import driver_dashboard_bp
    from routes.driver.jenius        import driver_jenius_bp
    from routes.driver.cash          import driver_cash_bp
    from routes.driver.history       import driver_history_bp
    from routes.driver.transactions  import driver_transactions_bp

    app.register_blueprint(driver_dashboard_bp)
    app.register_blueprint(driver_jenius_bp)
    app.register_blueprint(driver_cash_bp)
    app.register_blueprint(driver_history_bp)
    app.register_blueprint(driver_transactions_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # Index redirect
    @app.route('/')
    def index():
        from flask import redirect, url_for, session, g
        if session.get('session_token'):
            from utils.auth import get_current_user
            user = get_current_user()
            if user:
                if user.role == 'owner':
                    return redirect(url_for('owner_dashboard.index'))
                return redirect(url_for('driver_dashboard.index'))
        return redirect(url_for('auth.login'))

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
