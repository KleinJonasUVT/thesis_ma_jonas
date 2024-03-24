from flask import session
from sqlalchemy import create_engine, URL
from sqlalchemy import text
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets
import pytz

# Retrieve variables from environment
tidb_user = os.getenv('TIDB_USER')
tidb_password = os.getenv('TIDB_PASSWORD')
tidb_host = os.getenv('TIDB_HOST')
tidb_port = int(os.getenv('TIDB_PORT'))  # Port should be an integer
tidb_db_name = os.getenv('TIDB_DB_NAME')

def get_db_engine():
  connect_args = {
    "ssl_verify_cert": True,
    "ssl_verify_identity": True,
    "ssl_ca": '/etc/ssl/cert.pem',
        }
  return create_engine(
        URL.create(
            drivername="mysql+pymysql",
            username=tidb_user,
            password=tidb_password,
            host=tidb_host,
            port=tidb_port,
            database=tidb_db_name,
        ),
        connect_args=connect_args,
    )

engine = get_db_engine()

def load_courses_from_db():
  with engine.connect() as conn:
    result = conn.execute(text("SELECT course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers FROM courses"))
    courses = []
    columns = result.keys()
    for row in result:
      result_dict = {column: value for column, value in zip(columns, row)}
      courses.append(result_dict)
    return courses

def load_random_courses_from_db():
    with engine.connect() as conn:
        result = conn.execute(text("""
          SELECT course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers 
          FROM courses
          ORDER BY RAND()
          LIMIT 9;
        """))
        random_courses = []
        columns = result.keys()
        for row in result:
            result_dict = {column: value for column, value in zip(columns, row)}
            random_courses.append(result_dict)
        return random_courses

def load_last_viewed_courses_from_db():
    with engine.connect() as conn:
        session_id = session.get('session_id')

        result = conn.execute(text("""
          SELECT 
            ci.course_name,
            ci.course_code,
            ci.language,
            ci.aims,
            ci.content,
            ci.Degree,
            ci.ECTS,
            ci.school,
            ci.tests,
            ci.block,
            ci.lecturers
          FROM courses ci
          INNER JOIN (
              SELECT 
                  s.course_code, 
                  s.ID,
                  MAX(s.timestamp) as latest_timestamp
              FROM sessions s
              WHERE s.ID = :session_id
              GROUP BY s.course_code, s.ID
          ) latest_session ON ci.course_code = latest_session.course_code
          ORDER BY latest_session.latest_timestamp DESC;
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
      SELECT 
        ci.course_name,
        ci.course_code,
        ci.language,
        ci.aims,
        ci.content,
        ci.Degree,
        ci.ECTS,
        ci.school,
        ci.tests,
        ci.block,
        ci.lecturers
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
  activity = data.get('activity')
  algorithm = data.get('algorithm')
  place = data.get('place')

  with engine.connect() as conn:
      conn.execute(
          text("INSERT INTO sessions (ID, timestamp, course_code, activity, algorithm, place) VALUES (:session_id, :time, :course_code, :activity, :algorithm, :place)"),
          {"session_id": session_id, "time": time, "course_code": course_code, "activity": activity, "algorithm": algorithm, "place": place}
      )

def add_home_click_to_db():
  session_id = session.get("session_id")
  time = datetime.now(pytz.timezone('Europe/Amsterdam'))
  algorithm = session.get("algorithm_type")
  activity = 'home'
  course_code = 'none'
  place = 'home'

  with engine.connect() as conn:
      conn.execute(
          text("INSERT INTO sessions (ID, timestamp, course_code, activity, algorithm, place) VALUES (:session_id, :time, :course_code, :activity, :algorithm, :place)"),
          {"session_id": session_id, "time": time, "course_code": course_code, "activity": activity, "algorithm": algorithm, "place": place}
      )

def add_random_favorite_to_db(course_code):
  session_id = session.get("session_id")
  time = datetime.now(pytz.timezone('Europe/Amsterdam'))
  algorithm = 'random'
  activity = 'favorited'
  place = 'random'

  with engine.connect() as conn:
      conn.execute(
          text("INSERT INTO sessions (ID, timestamp, course_code, activity, algorithm, place) VALUES (:session_id, :time, :course_code, :activity, :algorithm, :place)"),
          {"session_id": session_id, "time": time, "course_code": course_code, "activity": activity, "algorithm": algorithm, "place": place}
      )

def add_last_viewed_favorite_to_db(course_code):
  session_id = session.get("session_id")
  time = datetime.now(pytz.timezone('Europe/Amsterdam'))
  algorithm = 'last_viewed'
  activity = 'favorited'
  place = 'last_viewed'

  with engine.connect() as conn:
      conn.execute(
          text("INSERT INTO sessions (ID, timestamp, course_code, activity, algorithm, place) VALUES (:session_id, :time, :course_code, :activity, :algorithm, :place)"),
          {"session_id": session_id, "time": time, "course_code": course_code, "activity": activity, "algorithm": algorithm, "place": place}
      )

def search_courses_from_db(query):
  with engine.connect() as conn:
      result = conn.execute(
          text("SELECT course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers FROM courses WHERE course_name LIKE :query OR course_code LIKE :query OR aims LIKE :query OR content LIKE :query OR lecturers LIKE :query LIMIT 6"),
          {"query": "%" + query + "%"}
      )
      courses = []
      columns = result.keys()
      for row in result:
          result_dict = {column: value for column, value in zip(columns, row)}
          courses.append(result_dict)
      return courses
