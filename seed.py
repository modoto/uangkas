"""
Seed database: buat tabel, isi transaction_types, dan buat akun owner.
Jalankan sekali saat pertama kali setup:

    python seed.py
"""

from app import create_app
from extensions import db
from models import User, Wallet, TransactionType
from models.transaction_type import SEED_TRANSACTION_TYPES


def seed():
    app = create_app('development')
    with app.app_context():
        # Buat semua tabel
        db.create_all()
        print('[OK] Tabel database berhasil dibuat.')

        # Seed transaction_types
        for data in SEED_TRANSACTION_TYPES:
            if not TransactionType.query.filter_by(code=data['code']).first():
                tt = TransactionType(
                    code       = data['code'],
                    label      = data['label'],
                    wallet_type= data['wallet_type'],
                    direction  = data['direction'],
                    is_system  = True,
                    is_active  = True,
                    sort_order = data['sort_order'],
                )
                db.session.add(tt)
                print(f'  + TransactionType: {data["code"]}')
        db.session.commit()
        print('[OK] Transaction types berhasil di-seed.')

        # Buat akun owner jika belum ada
        owner_email = app.config.get('OWNER_EMAIL', 'setyanaputra@yahoo.com')
        owner = User.query.filter_by(email=owner_email).first()
        if not owner:
            owner = User(name='Setyana Putra', email=owner_email, role='owner')
            db.session.add(owner)
            db.session.commit()
            print(f'[OK] Owner dibuat: {owner_email}')
        else:
            print(f'  Owner sudah ada: {owner_email}')

        print('\nSetup selesai! Jalankan aplikasi dengan:')
        print('  python app.py\n')
        print('Lalu buka http://localhost:5000 dan login dengan email:', owner_email)


if __name__ == '__main__':
    seed()
