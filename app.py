from flask import Flask, render_template, jsonify, request, redirect, session, url_for, make_response
from datetime import datetime, timedelta
import secrets
from werkzeug.security import check_password_hash
from user_db import (
    init_db,
    create_user,
    authenticate_user,
    get_user_by_id,
    update_user,
    add_favorite,
    remove_favorite,
    get_favorites,
)
from database import (
    load_courses_from_db,
    load_random_courses_from_db,
    load_last_viewed_courses_from_db,
    load_favorite_courses_from_db,
    add_click_to_db,
    add_home_click_to_db,
    add_random_favorite_to_db,
    add_last_viewed_favorite_to_db,
)
from ai_rec import recommend_courses, ai_search_results

app = Flask(__name__)
app.secret_key = 'test_with_password_bla' # Replace with a secure secret key
init_db()

@app.route("/")
def home():
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    session_id = session.get('session_id')

    used_courses = recommend_courses()
    num_used_courses = len(used_courses)

    add_home_click_to_db()
    
    # Your existing code for session_id, random_courses, etc. remains unchanged
    random_courses = load_random_courses_from_db()
    random_course_codes = [course['course_code'] for course in random_courses]
    session['random_course_codes'] = random_course_codes
    num_random_courses = len(random_courses)
    last_viewed_courses = load_last_viewed_courses_from_db()
    last_viewed_course_codes = [course['course_code'] for course in last_viewed_courses]
    session['last_viewed_course_codes'] = last_viewed_course_codes
    num_last_viewed_courses = len(last_viewed_courses)
    favorite_courses = load_favorite_courses_from_db()
    num_favorite_courses = len(favorite_courses)

    # Filter random_courses as per your existing logic
    random_courses = [course for course in random_courses if course['course_code'] not in used_courses]

    # Return the template with the necessary variables
    return render_template(
        'home.html',
        num_favorite_courses=num_favorite_courses,
        recommendation=True,
        used_courses=used_courses,
        num_used_courses=num_used_courses,
        random_courses=random_courses,
        num_random_courses=num_random_courses,
        last_viewed_courses=last_viewed_courses,
        num_last_viewed_courses=num_last_viewed_courses,
        session_id=session_id,
        favorite_courses=favorite_courses,
    )

@app.route('/clear_session')
def clear_session():
    session.clear()  # This clears the session
    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = authenticate_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            return redirect(url_for('profile'))
        error = 'Invalid credentials'
        return render_template('login.html', error=error)
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if not name or not email or not password or password != confirm:
            return render_template('register.html', error='Please fill in all fields correctly')
        if authenticate_user(email, password):
            return render_template('register.html', error='Email already registered')
        create_user(name, email, password)
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    return redirect(url_for('home'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        update_user(user_id, name=name, password=password if password else None)
        if name:
            session['user_name'] = name
    user = get_user_by_id(user_id)
    favorites_codes = get_favorites(user_id)
    all_courses = load_courses_from_db()
    favorite_courses = [c for c in all_courses if c['course_code'] in favorites_codes]
    return render_template('profile.html', user=user, favorite_courses=favorite_courses)

@app.route("/api/courses")
def list_courses():
  courses = load_courses_from_db()
  return jsonify(courses)

@app.route("/course/<course_code>")
def show_course(course_code):
    used_courses = recommend_courses()
    num_used_courses = len(used_courses)
    courses = load_courses_from_db()
    course = [course for course in courses if course.get('course_code') == course_code]
    favorite_courses = load_favorite_courses_from_db()
    num_favorite_courses = len(favorite_courses)
    results_ai = session.get('results_ai', [])
    if not course:
        return "Not Found", 404
    else:
        return render_template(
            'coursepage.html',
            num_favorite_courses=num_favorite_courses,
            recommendation=True,
            course=course[0],
            favorite_courses=favorite_courses,
            results_ai=results_ai,
            used_courses=used_courses,
            num_used_courses=num_used_courses,
        )

@app.route('/favourites')
def favorite_courses():
    favorite_courses = load_favorite_courses_from_db()
    num_favorite_courses = len(favorite_courses)
    return render_template('favourites.html', favorite_courses=favorite_courses, num_favorite_courses=num_favorite_courses, favorite=True)

@app.route("/course/<course_code>/rating", methods=['POST'])
def rating_course(course_code):
  data = request.get_json() if request.is_json else request.form
  session_id = session.get('session_id')
  add_click_to_db(session_id, course_code, data)
  random_course_codes = session.get('random_course_codes')
  print(random_course_codes)
  last_viewed_course_codes = session.get('last_viewed_course_codes')
  print(last_viewed_course_codes)
  found_random = False
  for random_course_code in random_course_codes:
    if random_course_code == course_code:
        found_random = True
        break
  if found_random:
    add_random_favorite_to_db(course_code)

  found_last_viewed = False
  for last_viewed_course_code in last_viewed_course_codes:
    if last_viewed_course_code == course_code:
        found_last_viewed = True
        break
  if found_last_viewed:
    add_last_viewed_favorite_to_db(course_code)

  user_id = session.get('user_id')
  if user_id:
    add_favorite(user_id, course_code)

  if request.is_json:
    return jsonify({"status": "ok", "favorited": True})
  previous_page = request.referrer
  return redirect(previous_page)

@app.route("/course/<course_code>/remove_rating", methods=['POST'])
def remove_rating(course_code):
    data = request.get_json() if request.is_json else request.form
    session_id = session.get('session_id')
    add_click_to_db(session_id, course_code, data)
    user_id = session.get('user_id')
    if user_id:
        remove_favorite(user_id, course_code)
    if request.is_json:
        return jsonify({"status": "ok", "favorited": False})
    previous_page = request.referrer
    return redirect(previous_page)

@app.route("/course/<course_code>/clicked", methods=['POST'])
def clicked_course(course_code):
    data = request.form
    session_id = session.get('session_id')
    add_click_to_db(session_id, course_code, data)
    return redirect(url_for('show_course', course_code=course_code))

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('query', '').strip()

    if query:
        total_results = ai_search_results(query)
    else:
        total_results = []

    results_ai = total_results

    favorite_courses = load_favorite_courses_from_db()
    num_favorite_courses = len(favorite_courses)

    return render_template('search.html', num_favorite_courses=num_favorite_courses, query=query, results=total_results, results_ai=results_ai, search=True)

@app.route("/disclaimer")
def disclaimer():
    return render_template('disclaimer.html')

@app.route("/submit")
def submit():
    return render_template('submit.html')

if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)