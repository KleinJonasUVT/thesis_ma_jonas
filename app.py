from flask import Flask, render_template, jsonify, request, redirect, session, url_for, make_response
import secrets
from database import Database
from ai_rec import print_recommendations_from_strings, ai_search_results
from content_based import get_content_based_courses
import random
import os

import time

import warnings
# Suppress all UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)
app.secret_key = 'test_with_password_bla' # Replace with a secure secret key

# Init database connection pool
db = Database()
db.warm_up_query()

@app.route("/")
def home():

    # Get session
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    session_id = session.get('session_id')

    # Get algorithm type
    if 'algorithm_type' not in session or not session['algorithm_type']:
        algorithm_type = random.choice(['openai', 'tfidf'])
        session['algorithm_type'] = algorithm_type
    else:
        algorithm_type = session.get('algorithm_type')

    # Get courses
    if algorithm_type == 'openai':
        start = time.time()
        used_courses = print_recommendations_from_strings(db, session_id)
        print("Time taken to load recc courses: ", round(time.time() - start), " s.")
        num_used_courses = len(used_courses)
    else:
        used_courses = get_content_based_courses(db)
        num_used_courses = len(used_courses)

    # Log the clicking of home page
    start = time.time()
    db.add_home_click_to_db(session_id)
    print("Time taken to add home click to db: ", round(time.time() - start), " s.")
    
    ## Your existing code for session_id, random_courses, etc. remains unchanged

    # Random courses
    start = time.time()
    random_courses = db.load_random_courses_from_db()
    random_course_codes = [course['course_code'] for course in random_courses]
    session['random_course_codes'] = random_course_codes
    num_random_courses = len(random_courses)
    print("Time taken to load random courses: ", round(time.time() - start), " s.")

    # Last viewed courses
    start = time.time()
    last_viewed_courses = db.load_last_viewed_courses_from_db(session_id)
    last_viewed_course_codes = [course['course_code'] for course in last_viewed_courses]
    session['last_viewed_course_codes'] = last_viewed_course_codes
    num_last_viewed_courses = len(last_viewed_courses)
    print("Time taken to load last viewed courses: ", round(time.time() - start), " s.")

    # Favourite courses
    start = time.time()
    favorite_courses = db.load_favorite_courses_from_db(session_id)
    num_favorite_courses = len(favorite_courses)
    print("Time taken to load last viewed courses: ", round(time.time() - start), " s.")

    # Filter random_courses as per your existing logic
    start = time.time()
    random_courses = [course for course in random_courses if course['course_code'] not in used_courses]
    print("Time taken to filter random courses: ", round(time.time() - start), " s.")

    # Return the template with the necessary variables
    return render_template('home.html', num_favorite_courses=num_favorite_courses, recommendation=True, used_courses=used_courses, num_used_courses=num_used_courses, random_courses=random_courses, num_random_courses=num_random_courses, last_viewed_courses=last_viewed_courses, num_last_viewed_courses=num_last_viewed_courses, session_id=session_id, favorite_courses=favorite_courses, content_based_courses=used_courses, num_content_based_courses=len(used_courses), openai_courses=used_courses, num_openai_courses=len(used_courses))

@app.route('/clear_session')
def clear_session():
    session.clear()  # This clears the session
    return redirect(url_for('home'))

@app.route("/api/courses")
def list_courses():
  courses = db.load_courses_from_db()
  return jsonify(courses)

@app.route("/course/<course_code>")
def show_course(course_code):
    # Get session
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
        openai_courses = print_recommendations_from_strings(db, session_id)
        used_courses = openai_courses
        num_used_courses = len(used_courses)
    else:
        content_based_courses = get_content_based_courses(db)
        used_courses = content_based_courses
        num_used_courses = len(used_courses)

    courses = db.load_courses_from_db()
    course = [course for course in courses if course.get('course_code') == course_code]
    favorite_courses = db.load_favorite_courses_from_db(session_id)
    num_favorite_courses = len(favorite_courses)
    results_ai = session.get('results_ai', [])

    if not course:
        return "Not Found", 404
    else:
        return render_template('coursepage.html', num_favorite_courses=num_favorite_courses, recommendation=True, course=course[0], favorite_courses=favorite_courses, results_ai=results_ai, openai_courses=openai_courses, content_based_courses=content_based_courses, used_courses=used_courses, num_used_courses=num_used_courses)

@app.route('/favourites')
def favorite_courses():
    # Get session
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    session_id = session.get('session_id')

    favorite_courses = db.load_favorite_courses_from_db(session_id)
    num_favorite_courses = len(favorite_courses)
    return render_template('favourites.html', favorite_courses=favorite_courses, num_favorite_courses=num_favorite_courses, favorite=True)

@app.route("/course/<course_code>/rating", methods=['POST'])
def rating_course(course_code):
  start = time.time()
  data = request.form
  session_id = session.get('session_id')
  db.add_click_to_db(session_id, course_code, data)
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
    db.add_random_favorite_to_db(session_id, course_code)

  found_last_viewed = False
  for last_viewed_course_code in last_viewed_course_codes:
    if last_viewed_course_code == course_code:
        found_last_viewed = True
        break
  if found_last_viewed:
    db.add_last_viewed_favorite_to_db(session_id, course_code)

  previous_page = request.referrer
  print("Time taken to rate course: ", round(time.time() - start), " s.")
  return redirect(previous_page)

@app.route("/course/<course_code>/remove_rating", methods=['POST'])
def remove_rating(course_code):
    data = request.form
    session_id = session.get('session_id')
    db.add_click_to_db(session_id, course_code, data)
    previous_page = request.referrer
    return redirect(previous_page)

@app.route("/course/<course_code>/clicked", methods=['POST'])
def clicked_course(course_code):
    data = request.form
    session_id = session.get('session_id')
    db.add_click_to_db(session_id, course_code, data)
    return redirect(url_for('show_course', course_code=course_code))

@app.route('/search', methods=['GET', 'POST'])
def search():
    # Get session
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    session_id = session.get('session_id')

    query = request.args.get('query')  # Retrieve the query parameter from the URL
    
    results_ai = ai_search_results(db, query)
    session['results_ai'] = results_ai

    if query:
        results_keyword = db.search_courses_from_db(query)
    else:
        results_keyword = []  # Initialize an empty list for the initial render

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

    favorite_courses = db.load_favorite_courses_from_db(session_id)
    num_favorite_courses = len(favorite_courses)

    return render_template('search.html', num_favorite_courses=num_favorite_courses, query=query, results=total_results, results_ai=results_ai, results_keyword=results_keyword, search=True)

@app.route("/disclaimer")
def disclaimer():
    return render_template('disclaimer.html')

@app.route("/submit")
def submit():
    return render_template('submit.html')

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=80, debug=os.environ["DEBUG"])