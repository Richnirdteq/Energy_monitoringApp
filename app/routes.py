import os
import secrets
import csv
import datetime as dt
from datetime import date, datetime, timedelta
from collections import defaultdict
from io import StringIO
from PIL import Image
from datetime import datetime
from calendar import monthrange
from flask_mail import Message
from .extension import db, mail
from flask import Blueprint, render_template, redirect, url_for, flash, request
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from .forms import ForgotPasswordForm, ResetPasswordForm
from .models import User
from .extension import db
from werkzeug.security import generate_password_hash
from flask_mail import Message

from flask import (
    Blueprint, render_template, redirect, url_for, flash, 
    request, session, make_response, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from .forms import (
    LoginForm, RegisterForm, ForgotPasswordForm, 
    GoalForm, ApplianceUsageForm, ProfileUpdateForm
)
from .models import User, EnergyInput, Goal, ApplianceUsage
from .extension import db

main = Blueprint('main', __name__)


# Helper Functions


from collections import defaultdict
from flask_login import current_user
from .models import EnergyInput

def calculate_daily_usage():
    all_inputs = EnergyInput.query.filter_by(user_id=current_user.id).all()
    daily_usage = defaultdict(float)

    for entry in all_inputs:
        day = entry.date.strftime('%Y-%m-%d')
        daily_usage[day] += entry.kwh  # use kwh instead of usage

    daily_labels = sorted(daily_usage.keys())
    daily_data = [daily_usage[day] for day in daily_labels]

    return daily_labels, daily_data

def calculate_monthly_usage():
    all_inputs = EnergyInput.query.filter_by(user_id=current_user.id).all()
    monthly_usage = defaultdict(float)

    for entry in all_inputs:
        month = entry.date.strftime('%Y-%m')
        monthly_usage[month] += entry.kwh  # use kwh

    monthly_labels = sorted(monthly_usage.keys())
    monthly_data = [monthly_usage[month] for month in monthly_labels]

    return monthly_labels, monthly_data

def calculate_breakdown_usage():
    all_inputs = EnergyInput.query.filter_by(user_id=current_user.id).all()
    breakdown_usage = defaultdict(float)

    for entry in all_inputs:
        breakdown_usage[entry.appliance] += entry.kwh  # use kwh

    breakdown_labels = list(breakdown_usage.keys())
    breakdown_data = list(breakdown_usage.values())

    return breakdown_labels, breakdown_data



def save_profile_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    upload_folder = current_app.config['UPLOAD_FOLDER']  # should be 'app/static/uploads'
    picture_path = os.path.join(current_app.root_path, upload_folder, picture_fn)
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    output_size = (125, 125)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)
    return picture_fn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def send_goal_alert_email(user, progress_percent, usage_kwh, goal_kwh, forecast_kwh):
    """Send a single alert email when user is about to exceed goal."""
    if not current_app.config.get('MAIL_SERVER'):
        current_app.logger.warning("MAIL not configured; skipping email send.")
        return False

    try:
        msg = Message(
            subject=f"Energy goal alert: {progress_percent:.0f}% of monthly goal used",
            recipients=[user.email]
        )
        msg.body = (
            f"Hi {user.username},\n\n"
            f"You've used {usage_kwh:.2f} kWh out of your {goal_kwh:.2f} kWh goal "
            f"this month ({progress_percent:.0f}%).\n"
            f"Current forecast: ~{forecast_kwh:.2f} kWh by month end.\n\n"
            f"Tip: Unplug idle devices and shift heavy usage to off-peak where possible.\n\n"
            f"— Your Energy Tracker"
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Email send failed: {e}")
        return False

# Routes
@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.app_context_processor
def inject_current_year():
    return {'current_year': datetime.utcnow().year}

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash("❌ Invalid username or password.", "error")
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already exists. Please log in or use a different email.', 'danger')
            return redirect(url_for('main.register'))

        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

# Forgot password route
@main.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            token = s.dumps(user.email, salt=current_app.config["SECURITY_PASSWORD_SALT"])
            reset_url = url_for("main.reset_password", token=token, _external=True)

            msg = Message("Password Reset Request", recipients=[user.email])
            msg.body = f"Click the link to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour."
            mail.send(msg)

            flash("Password reset link has been sent to your email.", "success")
            return redirect(url_for("main.login"))
        else:
            flash("No account found with that email.", "error")
    return render_template("forgot_password.html", form=form)


# Reset password route
@main.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(token, salt=current_app.config["SECURITY_PASSWORD_SALT"], max_age=3600)
    except SignatureExpired:
        flash("The reset link has expired. Please request a new one.", "error")
        return redirect(url_for("main.forgot_password"))
    except BadSignature:
        flash("Invalid reset link. Please request a new one.", "error")
        return redirect(url_for("main.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("main.forgot_password"))

        # Use your model helper
        user.set_password(form.password.data)
        db.session.commit()

        flash("Your password has been updated! You can now log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("reset_password.html", form=form)

@main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session.pop('guest', None)
    return redirect(url_for('main.login'))

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileUpdateForm()
    
    if form.validate_on_submit():
        if form.picture.data:
            try:
                # Delete old profile pic if not default
                if current_user.profile_image != 'default.png':
                    old_pic_path = os.path.join(
                        current_app.root_path, 
                        'app', 'static', 'uploads', 
                        current_user.profile_image
                    )
                    if os.path.exists(old_pic_path):
                        os.remove(old_pic_path)
                
                # Save new picture
                picture_file = save_profile_picture(form.picture.data)
                current_user.profile_image = picture_file
                db.session.commit()
                flash('Your profile picture has been updated!', 'success')
            except Exception as e:
                flash('Error updating profile picture.', 'danger')
                current_app.logger.error(f"Profile pic update error: {str(e)}")
            
            return redirect(url_for('main.profile'))

    image_file = url_for('static', filename='uploads/' + current_user.profile_image)
    return render_template('profile.html', 
                         form=form, 
                         image_file=image_file, 
                         user=current_user)

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = ApplianceUsageForm()
    profile_form = ProfileUpdateForm()
    goal_form = GoalForm()
    now = datetime.now()
    today = now.date()
    current_month_str = today.strftime('%Y-%m')
    days_in_month = monthrange(today.year, today.month)[1]
    days_elapsed = today.day

    # Fetch all inputs for user - optimized query
    all_inputs = db.session.query(EnergyInput).filter(
        EnergyInput.user_id == current_user.id
    ).order_by(EnergyInput.date).all()

    # Daily Usage + Forecasting with improved calculation
    daily_usage = defaultdict(float)
    current_month_inputs = [
        entry for entry in all_inputs 
        if entry.date.strftime('%Y-%m') == current_month_str
    ]
    
    for entry in current_month_inputs:
        day = entry.date.strftime('%Y-%m-%d')
        daily_usage[day] += entry.kwh

    # Fill missing days with 0 for complete dataset
    first_day = today.replace(day=1)
    complete_daily_usage = {}
    for i in range(days_in_month):
        day = first_day + timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        complete_daily_usage[day_str] = daily_usage.get(day_str, 0)

    # Sort by date
    daily_usage = dict(sorted(complete_daily_usage.items()))
    total_kwh_so_far = sum(daily_usage.values())

    # Enhanced forecasting calculation
    if days_elapsed > 0:
        daily_avg = total_kwh_so_far / days_elapsed
        forecast_kwh = round(daily_avg * days_in_month, 2)
        forecast_variance = round((forecast_kwh - total_kwh_so_far) / days_elapsed, 2)
    else:
        daily_avg = 0
        forecast_kwh = 0
        forecast_variance = 0

    # Get current goal or use default
    current_goal = Goal.query.filter_by(
        user_id=current_user.id,
        month=current_month_str
    ).first()
    
    goal_value = current_goal.target_kwh if current_goal else 100  # fallback to 100 kWh
    forecast_status = "✅ On Track" if forecast_kwh <= goal_value else "❌ Likely to Exceed Goal"

    # Historical comparison (prev month usage)
    prev_month_str = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    prev_month_usage = sum(
        e.kwh for e in all_inputs if e.date.strftime('%Y-%m') == prev_month_str
    )

    # Monthly usage totals (current vs previous) - optimized
    monthly_usage = {
        "current": sum(e.kwh for e in current_month_inputs),
        "previous": prev_month_usage
    }

    # Appliance choices - unchanged from your working version
    grouped = [
        ("Household", [
            ("Fan", "Fan"), ("Refrigerator", "Refrigerator"),
            ("TV", "TV"), ("Washing Machine", "Washing Machine")
        ]),
        ("Business", [
            ("Printer", "Printer"), ("Server Computer", "Server Computer"),
            ("Office Lighting", "Office Lighting")
        ]),
        ("Other", [("Other", "Other")])
    ]
    form.appliance.choices = [(val, label) for _, items in grouped for val, label in items]

    # Handle Goal Form - with improved validation
    if goal_form.validate_on_submit():
        if current_goal:
            current_goal.target_kwh = goal_form.target_kwh.data
        else:
            new_goal = Goal(
                user_id=current_user.id,
                month=current_month_str,
                target_kwh=goal_form.target_kwh.data
            )
            db.session.add(new_goal)
        db.session.commit()
        flash('✅ Monthly goal updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    # Initialize variables
    filtered_inputs = []
    appliance_data = []
    notifications = []
    tips = []
    usage_today = 0
    monthly_usage_kwh = monthly_usage["current"]
    progress_percent = min(round((monthly_usage_kwh / goal_value * 100), 2) if goal_value else 0, 100)

    # Main Processing with better error handling
    try:
        # Calculate today's usage
        usage_today = sum(
            u.kwh for u in all_inputs 
            if u.date.strftime('%Y-%m-%d') == today.strftime('%Y-%m-%d')
        )

        # Apply filters if present
        filter_month = request.args.get('month')
        selected_appliance = request.args.get('appliance')
        custom_appliance = request.args.get('other_filter_appliance')

        appliance_filter = (
            custom_appliance.strip()
            if selected_appliance == "Other" and custom_appliance
            else selected_appliance
        )

        filtered_query = EnergyInput.query.filter_by(user_id=current_user.id)

        if filter_month:
            try:
                year, mon = map(int, filter_month.split('-'))
                start = date(year, mon, 1)
                end = date(year + (mon == 12), (mon % 12) + 1, 1)
                filtered_query = filtered_query.filter(
                    EnergyInput.date >= start, 
                    EnergyInput.date < end
                )
            except ValueError:
                flash("Invalid month format", "error")

        if appliance_filter:
            filtered_query = filtered_query.filter(
                EnergyInput.appliance.ilike(f"%{appliance_filter}%")
            )

        filtered_inputs = filtered_query.order_by(EnergyInput.date).all()

        # Appliance breakdown - optimized calculation
        appliance_usage_summary = defaultdict(float)
        inputs_for_summary = (
            filtered_inputs if filter_month else current_month_inputs
        )
        
        for entry in inputs_for_summary:
            appliance_usage_summary[entry.appliance] += entry.kwh

        appliance_labels = list(appliance_usage_summary.keys())
        appliance_kwh = [round(val, 2) for val in appliance_usage_summary.values()]
        cost_per_kwh = 0.5  # Default cost - could be configurable per user
        appliance_costs = [round(kwh * cost_per_kwh, 2) for kwh in appliance_kwh]
        appliance_data = list(zip(appliance_labels, appliance_kwh, appliance_costs))

        # Goal Alerts (Email + Banner) with improved session management
        threshold_pct = 90
        alert_session_key = f'goal_alert_sent_{current_month_str}'

        if goal_value and progress_percent >= threshold_pct:
            if not session.get(alert_session_key):
                notifications.append(
                    f"🚨 Alert: You've used {progress_percent:.0f}% of your {goal_value:.0f} kWh goal. "
                    f"Forecast: ~{forecast_kwh:.2f} kWh by month end."
                )
                
                # Only send email if we haven't sent one this month
                email_ok = send_goal_alert_email(
                    current_user,
                    progress_percent=progress_percent,
                    usage_kwh=monthly_usage_kwh,
                    goal_kwh=goal_value,
                    forecast_kwh=forecast_kwh
                )
                
                if email_ok:
                    session[alert_session_key] = True
                    session.modified = True
                else:
                    current_app.logger.warning("Goal alert email not sent; will try again later.")

        # Enhanced Notifications + Tips system
        if usage_today > 5:
            notifications.append(
                f"⚠️ You've used {usage_today:.2f} kWh today - consider reducing usage."
            )
            tips.append("💡 Consider using fans instead of air conditioners during the day.")

        if progress_percent >= 100:
            notifications.append("❌ You've exceeded your monthly goal!")
            tips.append("📉 Review your usage patterns and consider adjusting appliances usage.")
        elif progress_percent >= 90:
            notifications.append(
                f"⚠️ You're at {progress_percent:.0f}% of your monthly goal."
            )

        # Appliance-specific tips
        today_appliances = {
            e.appliance.lower() 
            for e in all_inputs 
            if e.date.strftime('%Y-%m-%d') == today.strftime('%Y-%m-%d')
        }

        if any(a in today_appliances for a in ['refrigerator', 'freezer']):
            tips.append("🧊 Keep refrigerator doors closed to save energy.")

        if 'washing machine' in today_appliances:
            tips.append("🧺 Run washing machines only with full loads to save electricity.")

        if usage_today < 1:
            tips.append("✅ Great job! Your energy usage today is very efficient.")

    except Exception as e:
        current_app.logger.error(f"Error in dashboard route: {str(e)}", exc_info=True)
        flash("An error occurred while loading dashboard data", "error")

    return render_template(
        "dashboard.html",
        form=form,
        profile_form=profile_form,
        goal_form=goal_form,
        grouped=grouped,
        usage_today=round(usage_today, 2),
        usage_month=round(monthly_usage_kwh, 2),
        estimated_bill=round((monthly_usage_kwh * 0.5), 2),
        goal_value=goal_value,
        progress_percent=progress_percent,
        monthly_usage_kwh=monthly_usage_kwh,
        energy_inputs=filtered_inputs,
        appliance_data=appliance_data,
        notifications=notifications,
        tips=tips,
        now=now,
        datetime=datetime,
        current_date=now.strftime('%Y-%m-%d'),
        daily_usage=daily_usage,
        forecast_kwh=forecast_kwh,
        forecast_variance=forecast_variance,
        forecast_status=forecast_status,
        prev_month_usage=prev_month_usage,
        monthly_usage=monthly_usage
    )


@main.route('/guest_dashboard')
def guest_dashboard():
    # Demo / mock data for guest
    demo_data = {
        "username": "Guest User",
        "monthly_usage": 245,  # kWh
        "estimated_cost": 36.75,  # in $
        "savings_percent": 18,
        "appliance_breakdown": {
            "Air Conditioner": 40,
            "Refrigerator": 25,
            "Lighting": 20,
            "Others": 15
        },
        "daily_usage": [5, 7, 6, 8, 10, 9, 7, 6, 8, 12, 11, 10, 9, 8, 7],
        "goal_progress": 65
    }

    return render_template("guest_dashboard.html", data=demo_data)


@main.route('/add_appliance_usage', methods=['POST'])
@login_required
def add_appliance_usage():
    form = ApplianceUsageForm()
    
    # Repopulate grouped choices
    grouped = [
        ("Household", [("Fan","Fan"),("Refrigerator","Refrigerator"),("TV","TV"),("Washing Machine","Washing Machine")]),
        ("Business", [("Printer","Printer"),("Server Computer","Server Computer"),("Office Lighting","Office Lighting")]),
        ("Other", [("Other","Other")])
    ]
    form.appliance.choices = [(val, label) for _, items in grouped for val, label in items]

    if form.validate_on_submit():
        # Validate date is not in future
        if form.date.data > datetime.now().date():
            flash("❌ Future dates are not allowed.", "error")
            return redirect(url_for('main.dashboard'))
            
        appliance = form.other_appliance.data.strip() if form.appliance.data == "Other" else form.appliance.data
        watts = form.watts.data
        hours = form.hours.data
        usage_date = form.date.data

        # Calculate kWh
        kwh = round((watts * hours) / 1000, 2)

        # Create new record
        new_input = EnergyInput(
            user_id=current_user.id,
            appliance=appliance,
            watts=watts,
            hours=hours,
            date=usage_date,
            kwh=kwh
        )
        db.session.add(new_input)
        db.session.commit()

        flash(f"✅ Usage added for {appliance} on {usage_date.strftime('%Y-%m-%d')}.", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"❌ {form[field].label.text}: {error}", "error")

    return redirect(url_for('main.dashboard'))

@main.route('/export-csv')
@login_required
def export_csv():
    query = EnergyInput.query.filter_by(user_id=current_user.id)

    # Apply filters
    month = request.args.get('month')
    appliance = request.args.get('appliance')
    other_appliance = request.args.get('other_filter_appliance')

    if month:
        try:
            year, mon = map(int, month.split('-'))
            start = date(year, mon, 1)
            end = date(year + (mon == 12), (mon % 12) + 1, 1)
            query = query.filter(EnergyInput.date >= start, EnergyInput.date < end)
        except ValueError:
            pass

    if appliance == "Other" and other_appliance:
        query = query.filter(EnergyInput.appliance.ilike(f"%{other_appliance.strip()}%"))
    elif appliance:
        query = query.filter(EnergyInput.appliance.ilike(f"%{appliance}%"))

    data = query.order_by(EnergyInput.date).all()

    # Generate CSV
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Date', 'Appliance', 'Watts', 'Hours', 'kWh'])
    for entry in data:
        writer.writerow([
            entry.date.strftime('%Y-%m-%d'),
            entry.appliance,
            entry.watts,
            entry.hours,
            round(entry.kwh, 2)
        ])

    response = make_response(si.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=energy_usage.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@main.route('/energy-input', methods=['GET', 'POST'])
@login_required
def energy_input():
    form = ApplianceUsageForm()

    if form.validate_on_submit():
        # Example of saving logic
        appliance = form.appliance.data
        if appliance == "Other":
            appliance = form.other_appliance.data
        watts = form.watts.data
        hours = form.hours.data
        date = form.date.data

        # Save to DB (you must have an ApplianceUsage model)
        usage = ApplianceUsage(
            user_id=current_user.id,
            appliance=appliance,
            watts=watts,
            hours=hours,
            date=date
        )
        db.session.add(usage)
        db.session.commit()
        flash("Usage logged successfully!", "success")
        return redirect(url_for("main.energy_input"))

    return render_template("energy_input.html", form=form, current_date=date.today())

@main.route('/set_goal', methods=['GET', 'POST'])
@login_required
def set_goal():
    form = GoalForm()

    # Get current month in YYYY-MM format
    current_month_str = datetime.now().strftime('%Y-%m')

    if form.validate_on_submit():
        # Check if goal already exists for this user and month
        user_goal = Goal.query.filter_by(user_id=current_user.id, month=current_month_str).first()
        if user_goal:
            user_goal.value = form.monthly_goal.data
        else:
            new_goal = Goal(
                user_id=current_user.id,
                month=current_month_str,
                value=form.monthly_goal.data
            )
            db.session.add(new_goal)
        db.session.commit()
        flash('✅ Monthly goal updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    # Pre-fill existing goal if available
    user_goal = Goal.query.filter_by(user_id=current_user.id, month=current_month_str).first()
    if request.method == 'GET' and user_goal:
        form.monthly_goal.data = user_goal.value

    return render_template('set_goal.html', form=form)

@main.route("/send-test-email")
def send_test_email():
    try:
        msg = Message(
            subject="Energy Tracker Test Email",
            recipients=["yourpersonalemail@example.com"],  # change this
            body="Hello! This is a test email from your Energy Monitoring App 🚀"
        )
        mail.send(msg)
        return "✅ Test email sent successfully!"
    except Exception as e:
        return f"❌ Error: {str(e)}"

@main.route('/charts/daily')
@login_required
def daily_chart():
    # Example: get daily usage data
    daily_labels, daily_data = calculate_daily_usage()  # your function
    return render_template("charts/daily.html",
                           daily_labels=daily_labels,
                           daily_data=daily_data)

@main.route('/charts/monthly')
@login_required
def monthly_chart():
    # Example: get monthly usage data
    monthly_labels, monthly_data = calculate_monthly_usage()  # your function
    return render_template("charts/monthly.html",
                           monthly_labels=monthly_labels,
                           monthly_data=monthly_data)

@main.route('/charts/breakdown')
@login_required
def breakdown_chart():
    # Example: get breakdown data by appliance
    breakdown_labels, breakdown_data = calculate_breakdown_usage()  # your function
    return render_template("charts/breakdown.html",
                           breakdown_labels=breakdown_labels,
                           breakdown_data=breakdown_data)

@main.route('/announcements')
def announcements():
    announcements_data = [
        {
            "title": "New Energy Tariff Adjustments",
            "description": "The Energy Commission has announced new tariffs effective from September 2025.",
            "source": "https://www.energycom.gov.gh",
            "date": "2025-08-15"
        },
        {
            "title": "National Grid Maintenance",
            "description": "Power outage scheduled for some regions due to routine maintenance.",
            "source": "https://gridcogh.com",
            "date": "2025-08-10"
        },
        {
            "title": "Solar Energy Policy Update",
            "description": "New government incentives announced to encourage solar adoption.",
            "source": "https://energycom.gov.gh",
            "date": "2025-08-05"
        }
    ]
    return {"announcements": announcements_data}