from flask import session
from sqlalchemy import create_engine, URL
from sqlalchemy import text
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets
import pytz
import pymysql
import pandas as pd

# Connect to TiDB database function
def connect_to_db():
    connection = pymysql.connect(
        host = "gateway01.eu-central-1.prod.aws.tidbcloud.com",
        port = 4000,
        user = "2CfnZX3eakH9fXm.root",
        password = "KjLMaBg1uNZ0h8BP",
        database = "course_catalogue",
        ssl_verify_cert = True,
        ssl_verify_identity = True,
        ssl_ca = "/etc/ssl/cert.pem"
        )
    return connection

def load_courses_from_db():
    connection = connect_to_db()
    courses_df = pd.read_sql("SELECT course_name, course_code, language, aims, content, Degree, ECTS, tests, block, lecturers FROM courses", con=connection)
    courses = courses_df.to_dict('records')
    return courses

def load_random_courses_from_db():
    connection = connect_to_db()
    query = "SELECT course_name, course_code, language, aims, content, Degree, ECTS, tests, block, lecturers FROM courses ORDER BY RAND() LIMIT 9;"
    random_courses_df = pd.read_sql(query, con=connection)
    random_courses = random_courses_df.to_dict('records')
    return random_courses

def load_last_viewed_courses_from_db():
    connection = connect_to_db()
    session_id = session.get('session_id')
    query = """
        SELECT 
            ci.course_name,
            ci.course_code,
            ci.language,
            ci.aims,
            ci.content,
            ci.Degree,
            ci.ECTS,
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
            WHERE s.ID = %s
            GROUP BY s.course_code, s.ID
        ) latest_session ON ci.course_code = latest_session.course_code
        ORDER BY latest_session.latest_timestamp DESC;
    """
    last_viewed_courses_df = pd.read_sql(query, con=connection, params=session_id)
    compulsory_courses = last_viewed_courses_df.to_dict('records')
    return compulsory_courses

def load_favorite_courses_from_db():
    connection = connect_to_db()
    session_id = session.get('session_id')
    query = """
        SELECT 
            ci.course_name,
            ci.course_code,
            ci.language,
            ci.aims,
            ci.content,
            ci.Degree,
            ci.ECTS,
            ci.tests,
            ci.block,
            ci.lecturers
        FROM courses ci
        JOIN (
            SELECT course_code,
                MAX(CASE WHEN activity = 'favorited' THEN timestamp END) AS favorited_time,
                MAX(CASE WHEN activity = 'unfavorited' THEN timestamp END) AS unfavorited_time
            FROM sessions
            WHERE ID = %s
            GROUP BY course_code
            HAVING COALESCE(favorited_time, '1900-01-01 00:00:00') > COALESCE(unfavorited_time, '1900-01-01 00:00:00')
            OR MAX(activity) = 'favorited'
        ) s
        ON ci.course_code = s.course_code;
    """
    favorite_courses_df = pd.read_sql(query, con=connection, params=session_id)
    favorite_courses = favorite_courses_df.to_dict('records')
    return favorite_courses

def add_click_to_db(session_id, course_code, data):
    connection = connect_to_db()
    time = datetime.now(pytz.timezone('Europe/Amsterdam'))
    activity = data.get('activity')
    algorithm = data.get('algorithm')
    place = data.get('place')
    
    with connection.cursor() as cursor:
      sql = """
          INSERT INTO sessions (ID, timestamp, course_code, activity, algorithm, place)
          VALUES (%s, %s, %s, %s, %s, %s);
          """
      cursor.execute(sql, (session_id, time, course_code, activity, algorithm, place))
    connection.commit()
    connection.close()


def add_home_click_to_db():
    connection = connect_to_db()
    session_id = session.get("session_id")
    time = datetime.now(pytz.timezone('Europe/Amsterdam'))
    activity = 'home'
    course_code = 'none'
    algorithm = session.get('algorithm_type')
    place = 'home'

    with connection.cursor() as cursor:
            sql = """
                INSERT INTO sessions (ID, timestamp, course_code, activity, algorithm, place)
                VALUES (%s, %s, %s, %s, %s, %s);
                """
            cursor.execute(sql, (session_id, time, course_code, activity, algorithm, place))
    connection.commit()
    connection.close()

def add_random_favorite_to_db(course_code):
    connection = connect_to_db()
    session_id = session.get("session_id")
    time = datetime.now(pytz.timezone('Europe/Amsterdam'))
    algorithm = 'random'
    activity = 'favorited'
    place = 'random'

    with connection.cursor() as cursor:
            sql = """
                INSERT INTO sessions (ID, timestamp, course_code, activity, algorithm, place)
                VALUES (%s, %s, %s, %s, %s, %s);
                """
            cursor.execute(sql, (session_id, time, course_code, activity, algorithm, place))
    connection.commit()
    connection.close()

def add_last_viewed_favorite_to_db(course_code):
    connection = connect_to_db()
    session_id = session.get("session_id")
    time = datetime.now(pytz.timezone('Europe/Amsterdam'))
    algorithm = 'last_viewed'
    activity = 'favorited'
    place = 'last_viewed'

    with connection.cursor() as cursor:
            sql = """
                INSERT INTO sessions (ID, timestamp, course_code, activity, algorithm, place)
                VALUES (%s, %s, %s, %s, %s, %s);
                """
            cursor.execute(sql, (session_id, time, course_code, activity, algorithm, place))
    connection.commit()
    connection.close()

def search_courses_from_db(query):
    connection = connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT course_name, course_code, language, aims, content, Degree, ECTS, tests, block, lecturers 
            FROM courses 
            WHERE course_name LIKE %s 
            OR course_code LIKE %s 
            OR aims LIKE %s 
            OR content LIKE %s 
            OR lecturers LIKE %s 
            LIMIT 6;
            """,
            ("%" + query + "%", "%" + query + "%", "%" + query + "%", "%" + query + "%", "%" + query + "%")
        )
        columns = [col[0] for col in cursor.description]
        courses = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return courses
