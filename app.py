from flask import Flask, render_template, jsonify, request, redirect
from database import load_courses_from_db, add_rating_to_db, remove_rating_from_db, load_carousel_courses_from_db, load_best_courses_from_db, load_explore_courses_from_db, load_compulsory_courses_from_db, load_favorite_courses_from_db

app = Flask(__name__)

filters = {
    'Degree': ['Bachelor', 'Master', 'Pre-master'],
    'Block': [1, 2, 3, 4]
}

@app.route("/")
def landing():
    return render_template('welcome.html')

@app.route("/home")
def home():
    carousel_courses = load_carousel_courses_from_db()
    num_carousel_courses = len(carousel_courses)
    best_courses = load_best_courses_from_db()
    num_best_courses = len(best_courses)
    explore_courses = load_explore_courses_from_db()
    num_explore_courses = len(explore_courses)
    compulsory_courses = load_compulsory_courses_from_db()
    num_compulsory_courses = len(compulsory_courses)
    return render_template('home.html', best_courses=best_courses, num_best_courses=num_best_courses, carousel_courses=carousel_courses, num_carousel_courses=num_carousel_courses, explore_courses=explore_courses, num_explore_courses=num_explore_courses, compulsory_courses=compulsory_courses, num_compulsory_courses=num_compulsory_courses)

@app.route("/courses")
def hello_world():
    courses = load_courses_from_db()
    return render_template('courses.html', courses=courses, filters=filters)

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
  if not course:
    return "Not Found", 404
  else:
    return render_template('coursepage.html',
                        course=course[0])

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
    add_rating_to_db(course_code, data)
    previous_page = request.referrer
    return redirect(previous_page)

@app.route("/course/<course_code>/remove_rating", methods=['POST'])
def remove_rating(course_code):
    data = request.form
    remove_rating_from_db(course_code, data)
    previous_page = request.referrer
    return redirect(previous_page)

if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)