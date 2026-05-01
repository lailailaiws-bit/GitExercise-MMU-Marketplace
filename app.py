from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import uuid
import os
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///item.db'

UPLOAD_FOLDER = 'static/css/photos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.String(300), nullable=True)
    profile_pic = db.Column(db.String(), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Products(db.Model):
    __bind_key__ = "item"
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(150), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    item_pic = db.Column(db.String(), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

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

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if user_id := request.form.get('user_id'):
             print(f"User ID: {user_id}")
        
        pass
        return redirect(url_for('profile'))
    
    else:
        return render_template('profile.html', user=current_user)


@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

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

@app.route('/profile_edit/', methods=['GET', 'POST'])
@login_required
def profile_edit():
    if request.method == 'POST':
        current_user.contact_number = request.form.get('contact_number')
        current_user.bio = request.form.get('bio')
        
        if 'profile_pic' in request.files:
            profile_pic = request.files.get('profile_pic')

            if profile_pic and profile_pic.filename != '':
                pic_filename = secure_filename(profile_pic.filename)
                pic_name = str(uuid.uuid1()) + '_' + pic_filename
                profile_pic.save(os.path.join(app.config["UPLOAD_FOLDER"], pic_name))
                current_user.profile_pic = pic_name

        try:
            db.session.commit()
            flash("Update successful")
            return redirect(url_for("profile_edit"))
        except:
            flash("Error")
            return redirect(url_for("profile_edit"))
    else:
        return render_template('profile_edit.html', user=current_user)
    
@app.route('/delete')
@login_required
def delete():
    try:
        db.session.delete(current_user)
        db.session.commit()
        flash('Account Deleted!')
        return redirect (url_for('index'))

    except:
        flash('Error...Process Unsuccessful!')
        return redirect (url_for('index'))
    
@app.route('/item_post', methods=['GET', 'POST'])
@login_required
def item_post():
    if request.method == 'POST': 
        item_name = request.form.get('item_name')
        price = request.form.get('price')
        description = request.form.get('description')
        date_created = request.form.get('date_created')

        product = Products(
            item_name = request.form.get('item_name'),
            price = request.form.get('price'),
            description = request.form.get('description'),
            date_created = request.form.get('date_created'),
        )

        if not item_name or not price or not description:
            flash('Please fill out the item detail.')
            return redirect(url_for('item_post'))

        try:
            db.session.add(product)
            db.session.commit()
            return redirect (url_for('item_post'))
        except:
            return redirect (url_for('item_post'))
    else:
        return render_template('item_post.html', user=current_user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)