from datetime import datetime


def format_rupiah(value):
    """Format integer ke Rupiah: 1500000 → Rp 1.500.000"""
    if value is None:
        return 'Rp 0'
    try:
        formatted = f'{int(value):,}'.replace(',', '.')
        return f'Rp {formatted}'
    except (ValueError, TypeError):
        return 'Rp 0'


def format_datetime(value, fmt='%d %b %Y, %H:%M'):
    """Format datetime object ke string."""
    if not value:
        return '-'
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(fmt)


def format_date(value, fmt='%d %b %Y'):
    """Format datetime ke tanggal saja."""
    return format_datetime(value, fmt)
