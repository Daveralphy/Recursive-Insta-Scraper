import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- Form imports for WTForms ---
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange


# --- RQ & Redis Setup ---
from rq import Queue
from redis import Redis

redis_connection = Redis(host='localhost', port=6379, db=0)
q = Queue(connection=redis_connection) # Default queue

# --- Flask App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_strong_random_secret_key_here' # IMPORTANT: Change this to a strong, random key!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# --- Database Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    settings = db.relationship('UserSettings', backref='user', lazy=True, uselist=False)
    scrape_jobs = db.relationship('ScrapeJob', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    seed_usernames = db.Column(db.Text, default='')
    keywords = db.Column(db.Text, default='')
    scrape_limit = db.Column(db.Integer, default=500)
    recursion_depth = db.Column(db.Integer, default=1)
    export_format = db.Column(db.String(10), default='csv')
    visible_browser = db.Column(db.Boolean, default=False)
    scrape_duration_hours = db.Column(db.Integer, default=3)

class ScrapeJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    submitted_time = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    results_file_path = db.Column(db.String(255), nullable=True)
    profiles = db.relationship('ScrapedProfile', backref='job', lazy=True)

class ScrapedProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('scrape_job.id'), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=True)
    whatsapp_number = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(50), nullable=True)

# --- WTForms for Dashboard Settings ---
class UserSettingsForm(FlaskForm):
    seed_usernames = StringField('Seed Usernames (comma-separated)')
    keywords = StringField('Keywords (comma-separated)')
    scrape_limit = IntegerField('Scrape Limit (e.g., 500 profiles)', default=500, validators=[DataRequired(), NumberRange(min=1)])
    recursion_depth = IntegerField('Recursion Depth (e.g., 1)', default=1, validators=[DataRequired(), NumberRange(min=0)])
    visible_browser = BooleanField('Show Browser Window during Scrape (for testing)')
    export_format = StringField('Export Format (e.g., csv, json)', default='csv')
    scrape_duration_hours = IntegerField('Scrape Duration (hours, 1-24)', default=3, validators=[DataRequired(), NumberRange(min=1, max=24)])
    submit = SubmitField('Start New Scrape')


# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Initialization Command ---
@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    with app.app_context():
        db.create_all()
        print('Initialized the database.')


# --- Routes ---

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different one or log in.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        
        default_settings = UserSettings(user=new_user)
        db.session.add(default_settings)
        
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserSettingsForm()
    user_settings = current_user.settings
    user_jobs = ScrapeJob.query.filter_by(user_id=current_user.id).order_by(ScrapeJob.submitted_time.desc()).all()

    # --- NEW DEBUG PRINT STATEMENT BLOCK (CRITICAL FOR DIAGNOSIS) ---
    if request.method == 'POST':
        print(f"DEBUG: Request method is POST.")
        # Call validate_on_submit() once here to get the result and populate form.errors
        form_is_valid = form.validate_on_submit()
        print(f"DEBUG: form.validate_on_submit() result: {form_is_valid}")
        print(f"DEBUG: Form data received: {request.form}") # Print raw form data
        print(f"DEBUG: Form errors: {form.errors}") # Print validation errors

        # If validation fails, flash messages based on errors
        if not form_is_valid:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", 'danger')
            flash("Form submission failed validation. Please check your inputs.", 'danger')
    # --- END NEW DEBUG PRINT STATEMENT BLOCK ---


    # This 'if' block will now only be entered if form_is_valid was True
    if form.validate_on_submit(): # This call will return the same result as the one above
        action = request.form.get('action')

        # --- EXISTING DEBUG PRINT ---
        print(f"DEBUG: Form submitted, action: {action}")
        # --- END EXISTING DEBUG PRINT ---

        if action == 'start_scrape':
            if not user_settings:
                user_settings = UserSettings(user_id=current_user.id)
                db.session.add(user_settings)
            
            # Update settings based on form data BEFORE enqueueing
            user_settings.seed_usernames = form.seed_usernames.data
            user_settings.keywords = form.keywords.data
            user_settings.scrape_limit = form.scrape_limit.data
            user_settings.recursion_depth = form.recursion_depth.data
            user_settings.export_format = form.export_format.data
            user_settings.visible_browser = form.visible_browser.data
            user_settings.scrape_duration_hours = form.scrape_duration_hours.data

            new_job = ScrapeJob(user_id=current_user.id, status='pending')
            db.session.add(new_job)
            
            try:
                db.session.commit()

                user_settings_dict = {
                    'seed_usernames': user_settings.seed_usernames,
                    'keywords': user_settings.keywords,
                    'scrape_limit': user_settings.scrape_limit,
                    'recursion_depth': user_settings.recursion_depth,
                    'visible_browser': user_settings.visible_browser,
                    'export_format': user_settings.export_format,
                    'scrape_duration_hours': user_settings.scrape_duration_hours
                }
                
                # --- EXISTING DEBUGGING LINES (Redis connection & queue status) ---
                print(f"DEBUG: Redis connection alive: {q.connection.ping()}") 
                print(f"DEBUG: Current queue length before enqueue: {q.count}")
                # --- END EXISTING DEBUGGING LINES ---

                # --- This is the primary scrape job enqueue ---
                from tasks import run_instagram_scraper
                q.enqueue(run_instagram_scraper, current_user.id, new_job.id, user_settings_dict)

                # --- TEMPORARY TEST JOB ENQUEUE ---
                # UNCOMMENT THE LINE BELOW TO TEST IF ANY JOB GETS PICKED UP BY THE WORKER
                # This tests the basic RQ setup independent of your scraper function.
                # from tasks import test_task
                # q.enqueue(test_task, f"Hello from Flask for Job {new_job.id}!")
                # --- END TEMPORARY TEST JOB ENQUEUE ---


                flash('Scrape job initiated! Check "Your Scrape Jobs" below for status.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error initiating scrape job: {e}', 'danger')
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid form action specified.", 'danger')
            print(f"DEBUG: Invalid form action: {action}")

    # For GET requests, or if form validation failed on POST,
    # re-populate the form with current settings or submitted data.
    if request.method == 'GET' and user_settings: # Only pre-fill on GET requests
        form.seed_usernames.data = user_settings.seed_usernames
        form.keywords.data = user_settings.keywords
        form.scrape_limit.data = user_settings.scrape_limit
        form.recursion_depth.data = user_settings.recursion_depth
        form.visible_browser.data = user_settings.visible_browser
        form.export_format.data = user_settings.export_format
        form.scrape_duration_hours.data = user_settings.scrape_duration_hours
    # If it was a POST and validation failed, form.data will already contain submitted values
    # so no need to explicitly set them here again for POST requests.


    return render_template('dashboard.html', form=form, user_jobs=user_jobs)

@app.route("/download_results/<int:job_id>")
@login_required
def download_results(job_id):
    job = ScrapeJob.query.get_or_404(job_id)
    if job.user_id != current_user.id:
        flash("You are not authorized to download these results.", "danger")
        return redirect(url_for('dashboard'))

    if job.status in ['completed', 'terminated'] and job.results_file_path and os.path.exists(job.results_file_path):
        _, file_extension = os.path.splitext(job.results_file_path)
        mimetype = 'application/json' if file_extension.lower() == '.json' else 'application/octet-stream'
        
        return send_file(job.results_file_path, as_attachment=True, mimetype=mimetype, download_name=os.path.basename(job.results_file_path))
    else:
        flash("Results not available or job not completed/terminated with a file.", "warning")
        return redirect(url_for('dashboard'))

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True)