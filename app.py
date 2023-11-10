from flask import Flask, render_template, jsonify, request, redirect, session, url_for, make_response
from datetime import datetime, timedelta
import secrets
from database import load_courses_from_db, load_random_courses_from_db, load_last_viewed_courses_from_db, load_favorite_courses_from_db, add_click_to_db, search_courses_from_db
from ai_rec import print_recommendations_from_strings
from content_based import get_content_based_courses
from ai_search import ai_search_results
import random

app = Flask(__name__)
app.secret_key = 'test_with_password_bla' # Replace with a secure secret key

@app.route("/")
def landing():
    session['session_id'] = secrets.token_hex(16)
    session_id = session.get('session_id')
    return render_template('welcome.html')

@app.route("/home")
def home():
  session_id = session.get('session_id')
  random_courses = load_random_courses_from_db()
  num_random_courses = len(random_courses)
  last_viewed_courses = load_last_viewed_courses_from_db()
  num_last_viewed_courses = len(last_viewed_courses)
  favorite_courses = load_favorite_courses_from_db()
  openai_courses = print_recommendations_from_strings()
  num_openai_courses = len(openai_courses)
  content_based_courses = get_content_based_courses()
  num_content_based_courses = len(content_based_courses)
  total_courses = []
  if random.choice([True, False]):
        list1, list2 = openai_courses, content_based_courses
  else:
        list1, list2 = content_based_courses, openai_courses

  # Voeg elementen om en om toe
  for i in range(len(openai_courses)):
        total_courses.append(list1[i])
        total_courses.append(list2[i])
  num_total_courses= len(total_courses)
  return render_template('home.html', total_courses=total_courses, num_total_courses=num_total_courses, random_courses=random_courses, num_random_courses=num_random_courses, last_viewed_courses=last_viewed_courses, num_last_viewed_courses=num_last_viewed_courses, session_id=session_id, favorite_courses=favorite_courses, content_based_courses=content_based_courses, num_content_based_courses=num_content_based_courses, openai_courses=openai_courses, num_openai_courses=num_openai_courses)

@app.route("/courses")
def hello_world():
    courses = load_courses_from_db()
    sorted_courses = sorted(courses, key=lambda x: x['course_name'])
    return render_template('courses.html', sorted_courses=sorted_courses)

@app.route("/inlogpage")
def load_inlogpage():
    return render_template('inlogpage.html')

@app.route("/welcome")
def welcome():
    return render_template('welcome.html')

@app.route("/api/courses")
def list_courses():
  courses = load_courses_from_db()
  return jsonify(courses)

@app.route("/course/<course_code>")
def show_course(course_code):
    courses = load_courses_from_db()
    course = [course for course in courses if course.get('course_code') == course_code]
    favorite_courses = load_favorite_courses_from_db()
    if not course:
        return "Not Found", 404
    else:
        return render_template('coursepage.html', course=course[0], favorite_courses=favorite_courses)

@app.route('/favourites')
def favorite_courses():
    favorite_courses = load_favorite_courses_from_db()
    return render_template('favourites.html', favorite_courses=favorite_courses)

@app.route("/interests")
def get_interests():
    return render_template('interests.html')

@app.route("/course/<course_code>/rating", methods=['POST'])
def rating_course(course_code):
  data = request.form
  session_id = session.get('session_id')
  add_click_to_db(session_id, course_code, data)
  previous_page = request.referrer
  return redirect(previous_page)

@app.route("/course/<course_code>/remove_rating", methods=['POST'])
def remove_rating(course_code):
    data = request.form
    session_id = session.get('session_id')
    add_click_to_db(session_id, course_code, data)
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
    query = request.args.get('query')  # Retrieve the query parameter from the URL
    results_ai = ai_search_results(query)

    if query:
        results_keyword = search_courses_from_db(query)
    else:
        results_keyword = []  # Initialize an empty list for the initial render

    total_results = []

    if random.choice([True, False]):
        list1, list2 = results_ai, results_keyword
    else:
        list1, list2 = results_keyword, results_ai

    # Voeg elementen om en om toe
    for i in range(len(results_ai)):
        total_results.append(list1[i])
        total_results.append(list2[i])

    return render_template('search.html', query=query, results=total_results)

if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)