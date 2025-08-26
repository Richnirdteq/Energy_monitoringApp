from datetime import date, timedelta
from run import app, db   # <-- Import from your actual app entry point
from app.models import EnergyInput   # <-- Adjust path if your models are elsewhere

with app.app_context():
    today = date.today()
    current_month = today.strftime('%Y-%m')
    prev_month_date = today.replace(day=1) - timedelta(days=1)
    prev_month = prev_month_date.strftime('%Y-%m')

    # Query current month
    current_entries = EnergyInput.query.filter(
        db.extract('year', EnergyInput.date) == today.year,
        db.extract('month', EnergyInput.date) == today.month
    ).all()

    # Query previous month
    prev_entries = EnergyInput.query.filter(
        db.extract('year', EnergyInput.date) == prev_month_date.year,
        db.extract('month', EnergyInput.date) == prev_month_date.month
    ).all()

    print(f"📅 Current month ({current_month}): {len(current_entries)} records")
    for e in current_entries:
        print(f" - {e.date} | {e.appliance} | {e.kwh} kWh")

    print(f"\n📅 Previous month ({prev_month}): {len(prev_entries)} records")
    for e in prev_entries:
        print(f" - {e.date} | {e.appliance} | {e.kwh} kWh")