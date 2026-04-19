"""Helper untuk membuat transaksi keuangan dengan atomic guarantee."""
from datetime import datetime
from extensions import db
from models import Transaction, TransactionType


def record_transaction(wallet, txn_type_code, direction, amount, created_by_id,
                        txn_date=None, notes=None):
    """
    Buat satu transaksi dan update saldo wallet.
    Return Transaction object (belum di-commit).
    """
    txn_type = TransactionType.get_by_code(txn_type_code)
    if not txn_type:
        raise ValueError(f'Transaction type "{txn_type_code}" tidak ditemukan.')

    if txn_date is None:
        txn_date = datetime.utcnow()

    balance_before = wallet.current_balance

    if direction == 'credit':
        wallet.credit(amount)
    else:
        wallet.debit(amount)   # raises ValueError jika saldo kurang

    balance_after = wallet.current_balance

    txn = Transaction(
        wallet_id      = wallet.id,
        txn_type_id    = txn_type.id,
        created_by     = created_by_id,
        direction      = direction,
        amount         = amount,
        balance_before = balance_before,
        balance_after  = balance_after,
        notes          = notes,
        txn_date       = txn_date,
    )
    db.session.add(txn)
    return txn


def record_atm_withdrawal(jenius_wallet, cash_wallet, amount, created_by_id,
                           txn_date=None, notes=None):
    """
    Linked transaction: debit Jenius + credit Cash (atomic).
    Raise ValueError jika saldo Jenius tidak cukup.
    """
    if txn_date is None:
        txn_date = datetime.utcnow()

    try:
        # Debit Jenius
        jenius_txn = record_transaction(
            wallet         = jenius_wallet,
            txn_type_code  = 'atm_withdrawal',
            direction      = 'debit',
            amount         = amount,
            created_by_id  = created_by_id,
            txn_date       = txn_date,
            notes          = notes,
        )
        db.session.flush()   # dapatkan jenius_txn.id

        # Credit Cash
        cash_txn = record_transaction(
            wallet         = cash_wallet,
            txn_type_code  = 'cash_in',
            direction      = 'credit',
            amount         = amount,
            created_by_id  = created_by_id,
            txn_date       = txn_date,
            notes          = f'Dari Tarik ATM{(" — " + notes) if notes else ""}',
        )
        db.session.flush()

        # Link keduanya
        jenius_txn.linked_txn_id = cash_txn.id
        cash_txn.linked_txn_id   = jenius_txn.id

        db.session.commit()
        return jenius_txn, cash_txn

    except Exception:
        db.session.rollback()
        raise
