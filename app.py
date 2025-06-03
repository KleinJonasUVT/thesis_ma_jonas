from flask import Flask, render_template, jsonify, request, redirect, session, url_for, make_response
from datetime import datetime, timedelta
import secrets
from database import load_courses_from_db, load_random_courses_from_db, load_last_viewed_courses_from_db, load_favorite_courses_from_db, add_click_to_db, search_courses_from_db, add_home_click_to_db, add_random_favorite_to_db, add_last_viewed_favorite_to_db
from ai_rec import print_recommendations_from_strings, ai_search_results
from content_based import get_content_based_courses
import random
import httpagentparser

app = Flask(__name__)
app.secret_key = 'test_with_password_bla' # Replace with a secure secret key

@app.route("/")
def home():
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    session_id = session.get('session_id')

    if 'algorithm_type' not in session or not session['algorithm_type']:
        algorithm_type = random.choice(['openai', 'tfidf'])
        session['algorithm_type'] = algorithm_type
    
    else:
        algorithm_type = session.get('algorithm_type')

    openai_courses = []
    content_based_courses = []
    if algorithm_type == 'openai':
        openai_courses = print_recommendations_from_strings()
        used_courses = openai_courses
        num_used_courses = len(used_courses)
    else:
        content_based_courses = get_content_based_courses()
        used_courses = content_based_courses
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
    return render_template('home.html', num_favorite_courses=num_favorite_courses, recommendation=True, used_courses=used_courses, num_used_courses=num_used_courses, random_courses=random_courses, num_random_courses=num_random_courses, last_viewed_courses=last_viewed_courses, num_last_viewed_courses=num_last_viewed_courses, session_id=session_id, favorite_courses=favorite_courses, content_based_courses=content_based_courses, num_content_based_courses=len(content_based_courses), openai_courses=openai_courses, num_openai_courses=len(openai_courses))

@app.route('/clear_session')
def clear_session():
    session.clear()  # This clears the session
    return redirect(url_for('home'))

@app.route("/api/courses")
def list_courses():
  courses = load_courses_from_db()
  return jsonify(courses)

@app.route("/course/<course_code>")
def show_course(course_code):
    if 'algorithm_type' not in session or not session['algorithm_type']:
        algorithm_type = random.choice(['openai', 'tfidf'])
        session['algorithm_type'] = algorithm_type
    else:
        algorithm_type = session.get('algorithm_type')

    openai_courses = []
    content_based_courses = []
    if algorithm_type == 'openai':
        openai_courses = print_recommendations_from_strings()
        used_courses = openai_courses
        num_used_courses = len(used_courses)
    else:
        content_based_courses = get_content_based_courses()
        used_courses = content_based_courses
        num_used_courses = len(used_courses)
    courses = load_courses_from_db()
    course = [course for course in courses if course.get('course_code') == course_code]
    favorite_courses = load_favorite_courses_from_db()
    num_favorite_courses = len(favorite_courses)
    results_ai = session.get('results_ai', [])
    if not course:
        return "Not Found", 404
    else:
        return render_template('coursepage.html', num_favorite_courses=num_favorite_courses, recommendation=True, course=course[0], favorite_courses=favorite_courses, results_ai=results_ai, openai_courses=openai_courses, content_based_courses=content_based_courses, used_courses=used_courses, num_used_courses=num_used_courses)

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

  if request.is_json:
    return jsonify({"status": "ok", "favorited": True})
  previous_page = request.referrer
  return redirect(previous_page)

@app.route("/course/<course_code>/remove_rating", methods=['POST'])
def remove_rating(course_code):
    data = request.get_json() if request.is_json else request.form
    session_id = session.get('session_id')
    add_click_to_db(session_id, course_code, data)
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
        results_ai = ai_search_results(query)
        results_keyword = search_courses_from_db(query)
    else:
        results_ai = []
        results_keyword = []

    session['results_ai'] = results_ai
    session['results_keyword'] = results_keyword

    total_results = []

    if random.choice([True, False]):
        list1, list2 = results_ai, results_keyword
    else:
        list1, list2 = results_keyword, results_ai

    # Find the length of the shorter list
    min_length = min(len(list1), len(list2))

    # Add elements alternately from both lists up to the length of the shorter list
    for i in range(min_length):
        total_results.append(list1[i])
        total_results.append(list2[i])

    # Append remaining elements from the longer list, if any
    if len(list1) > min_length:
        total_results.extend(list1[min_length:])
    if len(list2) > min_length:
        total_results.extend(list2[min_length:])

    favorite_courses = load_favorite_courses_from_db()
    num_favorite_courses = len(favorite_courses)

    return render_template('search.html', num_favorite_courses=num_favorite_courses, query=query, results=total_results, results_ai=results_ai, results_keyword=results_keyword, search=True)

@app.route("/disclaimer")
def disclaimer():
    return render_template('disclaimer.html')

@app.route("/submit")
def submit():
    return render_template('submit.html')

if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)