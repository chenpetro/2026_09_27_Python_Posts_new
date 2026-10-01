from flask_caching import Cache 

from datetime import timedelta

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory
import os
from uuid import uuid4
from dotenv import load_dotenv
from flask_login import (UserMixin, LoginManager, login_user, logout_user, login_required, current_user)
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename
from database import Post, SessionLocal, User, select
from flask_wtf.csrf import CSRFProtect
import secrets
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
app.config["MAX_FORM_MEMORY_SIZE"] = 1024 ** 2
app.config["MAX_FORM_PARTS"] = 500
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=60 * 24)
cerf = CSRFProtect(app)
cache = Cache(app)
app.config['CACHE_DEFAULT_TIMEOUT'] = 60
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_KEY_PREFIX'] = 'post_'

@app.after_request
def apply_csp(response):
    nonce = secrets.token_urlsafe(16)  # Генеруємо nonce-токен
    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        f"style-src 'self'; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    response.set_cookie('nonce', nonce)
    return response


FILE_PATH = os.path.join(os.getcwd(), "posts")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
os.makedirs(FILE_PATH, exist_ok=True)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

def find_user(username, db):
    user = db.scalars(select(User).where(User.username == username)).first()
    return user

@login_manager.user_loader
def load_user(user_id):
    with SessionLocal() as db:
        return db.get(User, user_id)



@app.route("/")
@cache.cached(timeout=120) #2 min
def main():
    user = current_user.username if current_user.is_authenticated else "Guest"
    return f"Hello {user}"



@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'GET':
        return render_template('register.html', methods=['GET', 'POST'])
    username = request.form.get("username")
    password = request.form.get("password")


    with SessionLocal() as db:
        user = db.scalars(select(User).where(User.username == username)).first()
        if user:
            return "Username already exists"
        new_user = User(username=username, password=password)
        db.add(new_user)
        db.commit()
    return redirect('/login')



@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html', methods=['GET', 'POST'])
    username = request.form.get("username")
    password = request.form.get("password")

    with SessionLocal() as db:
        user = find_user(username, db)
    if user and user.password == password:
        login_user(user)
        return redirect("/")
        
@app.route('/posts')
@login_required
def profile_page():
    with SessionLocal() as db:
        posts = db.scalars(
            select(Post)
            .options(selectinload(Post.author))
            .order_by(Post.date.desc())
        ).all()
    return render_template('posts.html', posts=posts)


@app.route('/posts/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(FILE_PATH, filename)


@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post_page():
    if request.method == 'GET':
        return render_template('new_post.html', methods=['GET', 'POST'])
    description = request.form.get("description")
    file = request.files.get("image")
    original_filename = secure_filename(file.filename) if file else ""
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if not original_filename or extension not in ALLOWED_IMAGE_EXTENSIONS:
        return "Please select a JPG, PNG, GIF, or WebP image", 400

    filename = f"{uuid4().hex}.{extension}"
    saved_path = os.path.join(FILE_PATH, filename)
    file.save(saved_path)

    try:
        with SessionLocal() as db:
            author = db.get(User, int(current_user.id))
            post = Post(
                author=author,
                image_path=filename,
                description=description or None,
            )
            db.add(post)
            db.commit()
    except Exception:
        os.remove(saved_path)
        raise

    return redirect('/posts')


@app.route('/post/{int:post_id}')
@cache.cached(timeout=30, query_string=True)
def post_page(post_id): 
    return  


@app.route('/error', methods=['GET'])
def error():
    logging.error('Error route accessed: something went wrong')
    return jsonify({"error": "Something went wrong"}), 500

@app.route('/user', methods=['POST'])
@cerf.exempt
def user():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    if not username:
        logging.warning('POST /user: username is missing')
        return jsonify({"error": "Username is required"}), 400
    logging.info('POST /user: greeted user %s', username)
    return jsonify({"message": f"Hello, {username}!"}), 200


if __name__ == '__main__':
    app.run(debug=True)