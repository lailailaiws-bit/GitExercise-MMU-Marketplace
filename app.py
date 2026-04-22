import json
import os
from datetime import datetime

from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


#chat system
CHAT_DIR = 'chat folder'
os.makedirs(CHAT_DIR, exist_ok=True)

def load_user_data(username):
    file_path = get_user_file(username)
    if not os.path.exists(file_path):
        return {} 
    
    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_user_data(username, data):
    file_path = get_user_file(username)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def load_all_chats():
    if not os.path.exists(chat_history):
        return {}
    with open(chat_history, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}
        
def save_user_data(username, data):
    file_path = get_user_file(username)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def load_messages(current_user, target_user):
    user_data = load_user_data(current_user)
    return user_data.get(target_user, [])

def save_message(sender, receiver, content):
    message_obj = {
        'sender': sender,
        'content': content, 
        'time': datetime.now().strftime("%H:%M")
    }

def save_message(sender, receiver, content):
    message_obj = {
        'sender': sender,
        'content': content, 
        'time': datetime.now().strftime("%H:%M")
    }

    # Save to sender's file
    sender_data = load_user_data(sender)
    if receiver not in sender_data:
        sender_data[receiver] = []
    sender_data[receiver].append(message_obj)
    save_user_data(sender, sender_data)

    # Save to receiver's file
    if sender != receiver:
        receiver_data = load_user_data(receiver)
        if sender not in receiver_data:
            receiver_data[sender] = []
        receiver_data[sender].append(message_obj)
        save_user_data(receiver, receiver_data)


        
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/acc')
def account():
    return render_template('account.html')

@app.route('/search')
def search():
    query = request.args.get('q')
    print(f"Search query: {query}")
    return redirect(url_for('index'))

app.route('/chat', methods=['GET'])
@login_required
def chat_list() :
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('chat_list.html', users=users)



@app.route('/chat/<user_username>', methods=['GET', 'POST'])
@login_required 
def chat():
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            save_message(current_user.username, content)
        return redirect(url_for('chat'))
    
    # Load private messages for this specific user
    user_messages = load_messages(current_user.username)
    return render_template('chat.html', messages=user_messages)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if user_id := request.form.get('user_id'):
             print(f"User ID: {user_id}")
        # Handle form submission
        pass
    return render_template('profile.html', user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exist.')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('This email has already been registered for an account')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    else:
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('profile'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)