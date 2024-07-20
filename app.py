from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bootstrap import Bootstrap
from smtplib import SMTP
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_rescue.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
Bootstrap(app)

# Email configuration
SMTP_SERVER = 'smtp.example.com'
SMTP_PORT = 587
SMTP_USERNAME = 'your_email@example.com'
SMTP_PASSWORD = 'your_email_password'
EMAIL_FROM = 'your_email@example.com'
EMAIL_TO = 'recipient@example.com'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_volunteer = db.Column(db.Boolean, default=False)
    is_recipient = db.Column(db.Boolean, default=False)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # Restaurant, Grocery Shop, Supermarket

class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    time_collected = db.Column(db.String(100), nullable=False)
    proof_of_delivery = db.Column(db.String(100), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Send email notification
def send_email_notification(item, name):
    msg = MIMEText(f"Volunteer {name} signed up to rescue {item.item}!")
    msg['Subject'] = 'Food Rescue Alert'
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    with SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

# Routes
@app.route('/')
@login_required
def index():
    inventory = Inventory.query.all()
    return render_template('index.html', inventory=inventory)

@app.route('/volunteer', methods=['POST'])
@login_required
def volunteer():
    name = request.form['name']
    item_id = request.form['item_id']
    time_collected = request.form['time_collected']
    volunteer = Volunteer(user_id=current_user.id, item_id=item_id, time_collected=time_collected)
    db.session.add(volunteer)
    db.session.commit()
    flash('Volunteer signed up successfully!', 'success')

    # Send email notification
    item = Inventory.query.get(item_id)
    send_email_notification(item, name)

    return redirect(url_for('index'))

@app.route('/track/<int:item_id>')
@login_required
def track(item_id):
    item = Inventory.query.get(item_id)
    volunteers = Volunteer.query.filter_by(item_id=item_id).all()
    return render_template('track.html', item=item, volunteers=volunteers)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_volunteer = 'is_volunteer' in request.form
        is_recipient = 'is_recipient' in request.form
        user = User(username=username, password=password, is_volunteer=is_volunteer, is_recipient=is_recipient)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        item = request.form['item']
        quantity = request.form['quantity']
        expiry_date = request.form['expiry_date']
        location = request.form['location']
        category = request.form['category']
        new_item = Inventory(item=item, quantity=quantity, expiry_date=expiry_date, location=location, category=category)
        db.session.add(new_item)
        db.session.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_item.html')

@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    if request.method == 'POST':
        item_id = request.form['item_id']
        time_collected = request.form['time_collected']
        proof_of_delivery = request.form['proof_of_delivery']
        volunteer = Volunteer.query.filter_by(user_id=current_user.id, item_id=item_id).first()
        volunteer.proof_of_delivery = proof_of_delivery
        db.session.commit()
        flash('Delivery proof submitted successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('cart.html')

if __name__ == '__main__':
    app.run(debug=True)
