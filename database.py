import os
from datetime import datetime

import pytz
import pymysql
import pandas as pd
from flask import session

from dbutils.pooled_db import PooledDB

class Database:
    """Manages database connection with a connection pool. Reduces latency."""
     
    def __init__(self, **kwargs):
          self.pool = self.create_pool(**kwargs)

    def create_pool(self, **kwargs):
        print("creating pool")
        return PooledDB(
            creator=pymysql,
            maxconnections=10,  # Maximum number of connections in the pool
            mincached=2,  # Minimum number of idle connections in the pool
            maxcached=5,  # Maximum number of idle connections in the pool
            maxshared=3,  # Maximum number of shared connections
            blocking=False,
            setsession=[],
            ping=0,
            host=os.environ['TIDB_HOST'],
            port=4000,
            user=os.environ['TIDB_USER'],
            password=os.environ['TIDB_PASSWORD'],
            database=os.environ['TIDB_DB_NAME'],
            ssl={
                'ca': os.environ["SSL_CERT_PATH"]
            },
            **kwargs
        )
    
    def get_connection(self):
        print("returning connection")
        return self.pool.connection() 

    def fetch_query_as_pandas(self, query, *params, **kwargs):
        connection = self.get_connection()
        try:
            df = pd.read_sql(query, con=connection, *params, **kwargs)
        finally:
            connection.close()  # Ensure the connection is closed
        return df

    def warm_up_query(self):
        print("Warming up query...")
        self.fetch_query_as_pandas("SELECT 1")
        print("Warm up done...")
    
    ## Queries below (using pandas read_sql)

    def load_courses_from_db(self):
        query = "SELECT course_name, course_code, language, aims, content, Degree, ECTS, tests, block, lecturers FROM courses;"
        return self.fetch_query_as_pandas(query).to_dict('records')
    
    def load_random_courses_from_db(self):
        query = "SELECT course_name, course_code, language, aims, content, Degree, ECTS, tests, block, lecturers FROM courses ORDER BY RAND() LIMIT 9;"
        return self.fetch_query_as_pandas(query).to_dict('records')
    
    def load_last_viewed_courses_from_db(self, session_id):
        # session_id = session.get('session_id')
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
        return self.fetch_query_as_pandas(query, params=session_id).to_dict('records')
        
    def load_favorite_courses_from_db(self, session_id):
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
        return self.fetch_query_as_pandas(query, params=session_id).to_dict('records')
    
    def get_latest_favourite(self, session_id):
        query = """
            SELECT embedding
            FROM course_catalogue.courses
            WHERE course_code IN (
                SELECT `course_code` FROM `sessions` WHERE `ID` = %s AND (`activity` = 'clicked' OR `activity` = 'favorited') ORDER BY `timestamp` DESC LIMIT 1
            );
        """
        return self.fetch_query_as_pandas(query, params=session_id)
    
    def get_latest_recommended(self, session_id):
        query = "SELECT `course_code` FROM `sessions` WHERE `ID` = %s AND (`activity` = 'clicked' OR `activity` = 'favorited') ORDER BY `timestamp` DESC LIMIT 1;"
        return self.fetch_query_as_pandas(query, params=session_id)
    
    def get_recommended_courses(self, course_codes_tuple):
        # Construct the SQL query string dynamically
        placeholders = ', '.join(['%s'] * len(course_codes_tuple))
        sql = f"SELECT course_name, course_code, language, aims, content, Degree, ECTS, tests, block, lecturers FROM courses WHERE course_code IN ({placeholders}) ORDER BY CASE course_name "
        
        # Constructing the WHEN clauses dynamically
        when_clauses = " ".join([f"WHEN %s THEN {index + 1}" for index in range(len(course_codes_tuple))])
        
        # Completing the SQL query string and executing the query
        sql += f"{when_clauses} END;"

        return self.fetch_query_as_pandas(sql, params=course_codes_tuple*2).to_dict('records')
        
    ## Queries below using cursors

    def add_click_to_db(self, session_id, course_code, data):
        connection = self.get_connection()

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

    def add_home_click_to_db(self, session_id):
        connection = self.get_connection()

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

    def add_random_favorite_to_db(self, session_id, course_code):
        connection = self.get_connection()
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

    def add_last_viewed_favorite_to_db(self, session_id, course_code):
        connection = self.get_connection()
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

    def search_courses_from_db(self, query):
        connection = self.get_connection()
        try:
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
        finally:
             connection.close()
        return courses

