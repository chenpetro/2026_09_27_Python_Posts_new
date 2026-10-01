# Завдання 1. Налаштування Flask-Caching з SimpleCache
# Налаштуй кешування у Flask додатку, використовуючи SimpleCache.
# Кешуй результат функції, що повертає дані про користувача, на 60 секунд.

# Завдання 2. Простий кеш для функції
# Створи простий Flask-додаток із функцією, яка повертає випадкове
# число від 1 до 100. Використай Flask-Caching, щоб кешувати результат
# на 20 секунд. Перевір, як кешування впливає на результат.


from flask import Flask, render_template, request, redirect, url_for
from flask_caching import Cache
from random import randrange
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 5
cache = Cache(app)

@cache.cached(timeout=10)
def random_number():
    return str(randrange(1, 101))


users = [
    {'username': 'alice', 'email': 'alice@example.com'},
    {'username': 'bob', 'email': 'bob@example.com'},
]


@app.route('/new_user', methods=['POST'])
def new_user():
    users.append({
        'username': request.form['username'].strip(),
        'email': request.form['useremail'].strip(),
    })
    return redirect(url_for('cashed_user'))


@cache.memoize(timeout=5)
def get_cached_users():
    # copy, so users added later are not visible until the cache expires
    return [dict(u) for u in users]


@app.route('/cashed_user')
@cache.cached(timeout=5, query_string=True)
def cashed_user():
    search = request.args.get('search', '').strip().lower()
    found = [u for u in get_cached_users() if search in u['username'].lower()]
    loaded_at = datetime.now().strftime('%H:%M:%S')
    return render_template('cashed_user.html', users=found, search=search, loaded_at=loaded_at)


@app.route('/random_number')
def index():
    return render_template('random_number.html', random_number=random_number())


if __name__ == '__main__':
    app.run(debug=True)