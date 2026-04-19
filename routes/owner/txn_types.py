import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from extensions import db
from models import TransactionType
from utils.auth import owner_required

owner_txntypes_bp = Blueprint('owner_txntypes', __name__, url_prefix='/owner/txn-types')

WALLET_CHOICES    = [('jenius','Jenius'),('emoney','eMoney'),('cash','Uang Cash'),('all','Semua')]
DIRECTION_CHOICES = [('credit','Kredit (masuk)'),('debit','Debit (keluar)'),('both','Keduanya')]


def _label_to_code(label):
    code = label.lower().strip()
    code = re.sub(r'[^a-z0-9\s]', '', code)
    code = re.sub(r'\s+', '_', code)
    return code[:50]


def _unique_code(base_code):
    code = base_code
    i = 2
    while TransactionType.query.filter_by(code=code).first():
        code = f'{base_code}_{i}'
        i += 1
    return code


@owner_txntypes_bp.route('/')
@owner_required
def index():
    types = TransactionType.query.order_by(
        TransactionType.wallet_type, TransactionType.sort_order, TransactionType.label
    ).all()
    return render_template('owner/txn_types/list.html', types=types,
                           wallet_choices=WALLET_CHOICES)


@owner_txntypes_bp.route('/add', methods=['GET', 'POST'])
@owner_required
def add():
    if request.method == 'POST':
        label      = request.form.get('label', '').strip()
        wtype      = request.form.get('wallet_type', '')
        direction  = request.form.get('direction', '')
        sort_order = request.form.get('sort_order', '99').strip()

        errors = []
        if len(label) < 3:
            errors.append('Label minimal 3 karakter.')
        if wtype not in [w[0] for w in WALLET_CHOICES]:
            errors.append('Wallet tidak valid.')
        if direction not in [d[0] for d in DIRECTION_CHOICES]:
            errors.append('Arah transaksi tidak valid.')

        try:
            sort_order = int(sort_order)
        except ValueError:
            sort_order = 99

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('owner/txn_types/form.html', action='add',
                                   data=request.form,
                                   wallet_choices=WALLET_CHOICES,
                                   direction_choices=DIRECTION_CHOICES)

        code = _unique_code(_label_to_code(label))
        tt = TransactionType(code=code, label=label, wallet_type=wtype,
                             direction=direction, sort_order=sort_order,
                             created_by=g.current_user.id)
        db.session.add(tt)
        db.session.commit()
        flash(f'Jenis transaksi "{label}" berhasil ditambahkan.', 'success')
        return redirect(url_for('owner_txntypes.index'))

    return render_template('owner/txn_types/form.html', action='add', data={},
                           wallet_choices=WALLET_CHOICES,
                           direction_choices=DIRECTION_CHOICES)


@owner_txntypes_bp.route('/<tt_id>/edit', methods=['GET', 'POST'])
@owner_required
def edit(tt_id):
    tt = TransactionType.query.get_or_404(tt_id)

    if request.method == 'POST':
        label      = request.form.get('label', '').strip()
        sort_order = request.form.get('sort_order', '99').strip()
        is_active  = request.form.get('is_active') == '1'

        errors = []
        if len(label) < 3:
            errors.append('Label minimal 3 karakter.')
        try:
            sort_order = int(sort_order)
        except ValueError:
            sort_order = 99

        # Non-system: boleh edit wallet_type dan direction
        if not tt.is_system:
            wtype     = request.form.get('wallet_type', tt.wallet_type)
            direction = request.form.get('direction', tt.direction)
            if wtype not in [w[0] for w in WALLET_CHOICES]:
                errors.append('Wallet tidak valid.')
            if direction not in [d[0] for d in DIRECTION_CHOICES]:
                errors.append('Arah tidak valid.')
            tt.wallet_type = wtype
            tt.direction   = direction

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('owner/txn_types/form.html', action='edit', tt=tt,
                                   data=request.form,
                                   wallet_choices=WALLET_CHOICES,
                                   direction_choices=DIRECTION_CHOICES)

        tt.label      = label
        tt.sort_order = sort_order
        tt.is_active  = is_active
        db.session.commit()
        flash(f'Jenis transaksi "{label}" berhasil diperbarui.', 'success')
        return redirect(url_for('owner_txntypes.index'))

    return render_template('owner/txn_types/form.html', action='edit', tt=tt,
                           data=tt.__dict__,
                           wallet_choices=WALLET_CHOICES,
                           direction_choices=DIRECTION_CHOICES)


@owner_txntypes_bp.route('/<tt_id>/delete', methods=['POST'])
@owner_required
def delete(tt_id):
    tt = TransactionType.query.get_or_404(tt_id)

    if tt.is_system:
        flash('Jenis transaksi sistem tidak dapat dihapus.', 'error')
        return redirect(url_for('owner_txntypes.index'))

    count = tt.transactions.count()
    if count > 0:
        flash(f'Tidak dapat menghapus — sudah digunakan di {count} transaksi.', 'error')
        return redirect(url_for('owner_txntypes.index'))

    db.session.delete(tt)
    db.session.commit()
    flash(f'Jenis transaksi "{tt.label}" berhasil dihapus.', 'success')
    return redirect(url_for('owner_txntypes.index'))
