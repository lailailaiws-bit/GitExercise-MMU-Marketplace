import json
import os
import sqlite3
from datetime import datetime
from flask import Flask, flash, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import uuid
from datetime import datetime

app = Flask(__name__)


app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] =  os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/css/pictures'
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
    __tablename__ = "items"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    item_description = db.Column(db.String(150), nullable=False)
    item_category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    date_created = db.Column(db.DateTime, nullable=True, default=datetime.now)
    item_pic = db.Column(db.String(), nullable=False)
    seller = db.relationship('User', backref='products')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


CHAT_DIR = 'chats folder'
os.makedirs(CHAT_DIR, exist_ok=True)

def get_user_file_(username):
    return os.path.join(CHAT_DIR, f"{username}.json")

def load_user_data(username):
    """Loads all chat history for a specific user."""
    path = get_user_file_(username)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_message(sender, receiver, content):
    """Saves a message to both the sender's and receiver's JSON files."""
    message_obj = {
        'sender': sender,
        'recipient': receiver,
        'content': content,
        'time': datetime.now().strftime("%H:%M")
    }

    sender_data = load_user_data(sender)
    if receiver not in sender_data:
        sender_data[receiver] = []
    sender_data[receiver].append(message_obj)
    save_user_data(sender, sender_data)

    receiver_data = load_user_data(receiver)
    if sender not in receiver_data:
        receiver_data[sender] = []
    receiver_data[sender].append(message_obj)
    save_user_data(receiver, receiver_data)

def save_user_data(username, data):
    """Saves chat history for a specific user."""
    path = get_user_file_((username))
    json_string = json.dumps(data, indent=4, sort_keys=True)
    spaced_json_string = json_string.replace('],', '],\n')
    with open(path, 'w') as f:
        f.write(spaced_json_string)
        
def load_messages(current, target):
    data = load_user_data(current)
    return data.get(target, [])



@app.route('/')
@app.route('/home')
def home():
    item_info = Products.query.all()
    return render_template('home.html',item_list=item_info)

@app.route('/acc')
def account():
    return render_template('account.html')

@app.route('/search')
def search():
    search_query = request.args.get('q', '')
    category_filter = request.args.get('category', 'all')

    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    query = Products.query 

    if category_filter and category_filter != 'all':
        query = query.filter(Products.item_category.ilike(category_filter))

    if search_query:
        query = query.filter(Products.item_name.ilike(f'%{search_query}%'))

    if min_price is not None:
        query = query.filter(Products.price >= min_price)
        
    if max_price is not None:
        query = query.filter(Products.price <= max_price)

    matching_items = query.all()
    return render_template('item_market.html', item_list=matching_items)

@app.route('/chat')
@login_required 
def chat_list():
    search_query = request.args.get('q')
    
    try:
        user_chat_data = load_user_data(current_user.username)
        active_chat_usernames = list(user_chat_data.keys())
        active_chat_users = User.query.filter(User.username.in_(active_chat_usernames)).all()
    except Exception as e:
        active_chat_usernames = []

    if search_query:
        users = User.query.filter(
            User.id != current_user.id,
            User.username.ilike(f"%{search_query}%")
        ).all()
    else:
        users = User.query.filter(User.id != current_user.id).all()

    return render_template('chat_list.html', users=users, active_chat_users=active_chat_users)

@app.route('/chat/<target_username>' , methods=['GET', 'POST'])
@login_required
def chat_with(target_username):
    target_user = User.query.filter_by(username=target_username).first_or_404()

    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            save_message(current_user.username, target_username, content)
        return redirect(url_for('chat_with', target_username=target_username) + '#bottom')

    user_messages = load_messages(current_user.username, target_username)

    try:
        user_chat_data = load_user_data(current_user.username)
        active_chat_usernames = list(user_chat_data.keys())
    except Exception as e:
        active_chat_usernames = []

    return render_template('chat.html', messages=user_messages, target_username=target_username ,target_user=target_user, active_chat_usernames=active_chat_usernames)


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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exist.')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('This email has already been registered for an account')
            return redirect(url_for('register'))

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
    return redirect(url_for('home'))

@app.route('/profile_edit', methods=['GET', 'POST'])
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
        except Exception as e:
            flash("Error")
            print(f"Profile update failed: {e}")
            return redirect(url_for("profile_edit"))
    else:
        return render_template('profile_edit.html', user=current_user)
    
    
@app.route('/item_post/', methods=['GET', 'POST'])
@login_required
def item_post():
    if request.method == 'POST': 
        item_name = request.form.get('item_name')
        price = request.form.get('price')
        description = request.form.get('item_description')
        item_category = request.form.get('item_category')
        location = request.form.get('location')
        longitude = request.form.get('longitude')
        latitude = request.form.get('latitude')

        if not item_name or not price or not description:
            flash('Please fill out the item detail.')
            return redirect(url_for('item_post'))
        
        item_picname = None

        if 'item_pic' in request.files:
            item_pic = request.files.get('item_pic')

            if item_pic and item_pic.filename != '':
                item_filename = secure_filename(item_pic.filename)
                item_picname = str(uuid.uuid1()) + '_' + item_filename
                item_pic.save(os.path.join(app.config["UPLOAD_FOLDER"], item_picname))
                item_pic = item_picname

        product = Products(
            item_name = item_name,
            price = price,
            item_description = description,
            user_id = current_user.id,
            item_category = item_category,
            location = location,
            longitude = float(longitude) if longitude else None,
            latitude = float(latitude) if latitude else None,
            item_pic = item_picname
        )

        try:
            db.session.add(product)
            flash('Item posted!')
            db.session.commit()
            return redirect (url_for('item_post'))
        except Exception as e:
            flash('Failed to post item.')
            print(f"Item post failed: {e}")
            return redirect (url_for('item_post'))
    else:
        return render_template('item_post.html', user=current_user, mapbox_token=os.environ.get('MAPBOX_TOKEN', ''))

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/about')
def about():
    return render_template('footer/about.html')

@app.route('/contact')
def contact():
    return render_template('footer/NV_contact.html')

@app.route('/ourstores')
def ourstores():
    return render_template('home.html')

@app.route('/item_market/')
@login_required
def item_market():
    item_info = Products.query.all()

    return render_template('item_market.html', item_list=item_info, mapbox_token=os.environ.get('MAPBOX_TOKEN', ''))
    
@app.route('/item/<item_id>')
@login_required
def item(item_id):
    target_item = Products.query.get_or_404(item_id)
    seller = User.query.get(target_item.user_id)

    
    return render_template('item.html', item=target_item, seller=seller, mapbox_token=os.environ.get('MAPBOX_TOKEN', ''))

@app.route('/item_edit/<item_id>', methods=['GET', 'POST'])
@login_required
def item_edit(item_id):
    target_item = Products.query.get_or_404(item_id)

    seller = User.query.get(target_item.user_id)

    if request.method == 'POST':
        item_name = request.form.get('item_name')
        if item_name is not None and item_name != '':
            target_item.item_name = item_name

        price_val = request.form.get('price')
        if price_val is not None and price_val != '':
            try:
                target_item.price = float(price_val)
            except ValueError:
                flash('Invalid price value.')

        item_description = request.form.get('item_description')
        if item_description is not None:
            target_item.item_description = item_description

        item_category = request.form.get('item_category')
        if item_category:
            target_item.item_category = item_category

        longitude_val = request.form.get('longitude')
        latitude_val = request.form.get('latitude')
        if longitude_val:
            try:
                target_item.longitude = float(longitude_val)
            except ValueError:
                pass
        if latitude_val:
            try:
                target_item.latitude = float(latitude_val)
            except ValueError:
                pass

        if 'item_pic' in request.files:
            item_pic = request.files.get('item_pic')

            if item_pic and item_pic.filename != '':
                try:
                    item_filename = secure_filename(item_pic.filename)
                    item_picname = str(uuid.uuid1()) + '_' + item_filename
                    os.makedirs(app.config.get("UPLOAD_FOLDER", ""), exist_ok=True)
                    item_pic.save(os.path.join(app.config["UPLOAD_FOLDER"], item_picname))
                    target_item.item_pic = item_picname
                except Exception as e:
                    flash('Failed to save uploaded image.')
                    print(f"Error saving uploaded image: {e}")

        try:
            db.session.commit()
            flash('Your item information has been edited successful')
            return redirect(url_for('item_edit', item_id=item_id))
        except Exception as e:
            flash('Failed to update item.')
            print(f"Item edit failed: {e}")
            return redirect(url_for('item_edit', item_id=item_id))

    else:
        return render_template('item_edit.html', item=target_item, mapbox_token=os.environ.get('MAPBOX_TOKEN', ''))

@app.route('/delete/<item_id>')
@login_required
def delete(item_id):
    target_id = Products.query.get(item_id)
    try:
        db.session.delete(target_id)
        db.session.commit()
        return redirect (url_for('home'))

    except Exception as e:
        print(f"Delete failed: {e}")
        return redirect (url_for('home'))
    
@app.route('/my_item/')
@login_required
def my_item():
    my_products = Products.query.filter_by(user_id=current_user.id).all()

    return render_template('my_item.html', item=my_products)
    
with app.app_context():
    db.create_all()

    db_path = os.path.join(app.instance_path, 'site.db')
    if os.path.exists(db_path):
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(items)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if 'location' not in existing_columns:
            cursor.execute("ALTER TABLE items ADD COLUMN location VARCHAR(50)")
        if 'longitude' not in existing_columns:
            cursor.execute("ALTER TABLE items ADD COLUMN longitude FLOAT")
        if 'latitude' not in existing_columns:
            cursor.execute("ALTER TABLE items ADD COLUMN latitude FLOAT")

        connection.commit()
        connection.close()
    

if __name__ == '__main__':
    app.run(debug=True)