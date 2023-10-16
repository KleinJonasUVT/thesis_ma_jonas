from flask import session
from sqlalchemy import create_engine
from sqlalchemy import text
import os
from datetime import datetime, timedelta
import secrets

db_connection_string = os.environ['DB_CONNECTION_STRING']

engine = create_engine(
  db_connection_string,
  connect_args={
    "ssl": {
      "ssl_ca": "/etc/ssl/cert.pem"
    }
  }
)

def load_courses_from_db():
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM courses"))
    courses = []
    columns = result.keys()
    for row in result:
      result_dict = {column: value for column, value in zip(columns, row)}
      courses.append(result_dict)
    return courses

def load_carousel_courses_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM courses WHERE site_placement = 'Carousel'"))
        carousel_courses = []
        columns = result.keys()
        for row in result:
            result_dict = {column: value for column, value in zip(columns, row)}
            carousel_courses.append(result_dict)
        return carousel_courses

def load_best_courses_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM courses WHERE site_placement = 'Best'"))
        best_courses = []
        columns = result.keys()
        for row in result:
            result_dict = {column: value for column, value in zip(columns, row)}
            best_courses.append(result_dict)
        return best_courses

def load_explore_courses_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM courses WHERE site_placement = 'Explore'"))
        explore_courses = []
        columns = result.keys()
        for row in result:
            result_dict = {column: value for column, value in zip(columns, row)}
            explore_courses.append(result_dict)
        return explore_courses

def load_compulsory_courses_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM courses WHERE site_placement = 'Compulsory'"))
        compulsory_courses = []
        columns = result.keys()
        for row in result:
            result_dict = {column: value for column, value in zip(columns, row)}
            compulsory_courses.append(result_dict)
        return compulsory_courses

def load_favorite_courses_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM courses WHERE favorite = 'favorited'"))
        favorite_courses = []
        columns = result.keys()
        for row in result:
            result_dict = {column: value for column, value in zip(columns, row)}
            favorite_courses.append(result_dict)
        return favorite_courses

def add_rating_to_db(course_code, data):
    with engine.connect() as conn:
            conn.execute(
                text("UPDATE courses SET favorite = :rating WHERE course_code = :course_code"),
                {"course_code": course_code, "rating": data['activity']}
            )

def remove_rating_from_db(course_code):
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE courses SET favorite = DEFAULT WHERE course_code = :course_code"),
            {"course_code": course_code}
        )

def add_click_to_db(session_id, course_code, data):
  time = datetime.now()

  with engine.connect() as conn:
      conn.execute(
          text("INSERT INTO sessions (ID, timestamp, course_code, activity) VALUES (:session_id, :time, :course_code, :activity)"),
          {"session_id": session_id, "time": time, "course_code": course_code, "activity": data['activity']}
      )







