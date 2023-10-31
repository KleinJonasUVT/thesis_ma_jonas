from flask import session
from sqlalchemy import create_engine
from sqlalchemy import text
import os
from datetime import datetime, timedelta
import secrets
import pytz

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
        result = conn.execute(text("SELECT * FROM courses WHERE site_placement = 'Best';"))
        explore_courses = []
        columns = result.keys()
        for row in result:
            result_dict = {column: value for column, value in zip(columns, row)}
            explore_courses.append(result_dict)
        return explore_courses

def load_compulsory_courses_from_db():
    with engine.connect() as conn:
        session_id = session.get('session_id')

        result = conn.execute(text("""
          SELECT ci.*
          FROM courses ci
          INNER JOIN (
               SELECT s.course_code, s.ID
               FROM sessions s
               WHERE s.ID = :session_id
               AND s.timestamp = (
                   SELECT MAX(timestamp)
                   FROM sessions
                   WHERE ID = s.ID AND course_code = s.course_code
               )
           ) latest_session
           ON ci.course_code = latest_session.course_code;
           """), {"session_id":session_id})
        compulsory_courses = []
        columns = result.keys()
        for row in result:
            result_dict = {column: value for column, value in zip(columns, row)}
            compulsory_courses.append(result_dict)
        return compulsory_courses

def load_favorite_courses_from_db():
  session_id = session.get('session_id')
  
  with engine.connect() as conn:
    query = text("""
      SELECT ci.*
      FROM courses ci
      JOIN (
          SELECT course_code,
              MAX(CASE WHEN activity = 'favorited' THEN timestamp END) AS favorited_time,
              MAX(CASE WHEN activity = 'unfavorited' THEN timestamp END) AS unfavorited_time
          FROM sessions
          WHERE ID = :session_id
          GROUP BY course_code
          HAVING COALESCE(favorited_time, '1900-01-01 00:00:00') > COALESCE(unfavorited_time, '1900-01-01 00:00:00')
          OR MAX(activity) = 'favorited'
      ) s
      ON ci.course_code = s.course_code;
    """)

    result = conn.execute(query, {"session_id":session_id})

    favorite_courses = []
    columns = result.keys()
    for row in result:
        result_dict = {column: value for column, value in zip(columns, row)}
        favorite_courses.append(result_dict)
      
  return favorite_courses

def add_click_to_db(session_id, course_code, data):
  time = datetime.now(pytz.timezone('Europe/Amsterdam'))

  with engine.connect() as conn:
      conn.execute(
          text("INSERT INTO sessions (ID, timestamp, course_code, activity) VALUES (:session_id, :time, :course_code, :activity)"),
          {"session_id": session_id, "time": time, "course_code": course_code, "activity": data['activity']}
      )







