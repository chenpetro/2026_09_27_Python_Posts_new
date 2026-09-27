from flask import Flask, redirect, render_template, request, send_from_directory
import os
from uuid import uuid4
from dotenv import load_dotenv
from flask_login import (UserMixin, LoginManager, login_user, logout_user, login_required, current_user)
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename
from database import Post, SessionLocal, User, select


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
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


if __name__ == '__main__':
    app.run(debug=True)