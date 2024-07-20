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
    role = db.Column(db.String(50), nullable=False)  # 'volunteer', 'receiver', 'donor'

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.String(100), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Send email notification
def send_email_notification(item, name):
    msg = MIMEText(f"Volunteer {name} signed up to rescue {item.name}!")
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
    items = Item.query.all()
    return render_template('index.html', items=items)

@app.route('/volunteer', methods=['POST'])
@login_required
def volunteer():
    name = request.form['name']
    item_id = request.form['item_id']
    volunteer = Volunteer(name=name, item_id=item_id)
    db.session.add(volunteer)
    db.session.commit()
    flash('Volunteer signed up successfully!', 'success')

    item = Item.query.get(item_id)
    send_email_notification(item, name)

    return redirect(url_for('index'))

@app.route('/track/<int:item_id>')
@login_required
def track(item_id):
    item = Item.query.get(item_id)
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
        role = request.form['role']
        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/donate', methods=['GET', 'POST'])
@login_required
def donate():
    if request.method == 'POST':
        item_name = request.form['item_name']
        quantity = request.form['quantity']
        expiry_date = request.form['expiry_date']
        item = Item(name=item_name, quantity=quantity, expiry_date=expiry_date, donor_id=current_user.id)
        db.session.add(item)
        db.session.commit()
        flash('Item donated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('donate.html')

if __name__ == '__main__':
    app.run(debug=True)


