from sqlalchemy import create_engine, text
import pandas as pd
import os
import random
from flask import session

def predict_next_course_from_db():
    # Database connection setup
    db_connection_string = os.environ['DB_CONNECTION_STRING']
  
    engine = create_engine(
      db_connection_string,
      connect_args={
        "ssl": {
          "ssl_ca": "/etc/ssl/cert.pem"
        }
      }
    )

    def load_sessions_from_db():
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM sessions"))
            sessions = []
            columns = result.keys()
            for row in result:
                result_dict = {column: value for column, value in zip(columns, row)}
                sessions.append(result_dict)
            return sessions

    sessions_dict = load_sessions_from_db()
    sessions_df = pd.DataFrame(sessions_dict)

    # Sort the data by ID and timestamp
    sorted_sessions = sessions_df.sort_values(by=['ID', 'timestamp'])

    # Filter out rows where activity is not 'clicked'
    clicked_data = sessions_df[sessions_df['activity'] == 'clicked']

    # Initialize a dictionary to hold transition frequencies
    transition_freq = {}

    # Iterate through each user and their sequence of clicked courses
    for user, group in clicked_data.groupby('ID'):
        courses = group['course_code'].tolist()
        for i in range(len(courses) - 1):
            current_course = courses[i]
            next_course = courses[i + 1]

            # Check if current_course key exists
            if current_course not in transition_freq:
                transition_freq[current_course] = {}

            # Check if next_course key exists under current_course
            if next_course not in transition_freq[current_course]:
                transition_freq[current_course][next_course] = 0

            # Increment the transition frequency
            transition_freq[current_course][next_course] += 1

    # Create a transition matrix using the transition frequencies
    transition_matrix = {}

    # Calculate the transition probabilities
    for current_course, next_courses in transition_freq.items():
        # Get the total number of transitions from the current course
        total_transitions = sum(next_courses.values())

        # Initialize an inner dictionary for the current course in the transition matrix
        transition_matrix[current_course] = {}

        # Calculate the transition probabilities for each subsequent course
        for next_course, freq in next_courses.items():
            transition_matrix[current_course][next_course] = freq / total_transitions

    def predict_next_course():
        session_id = session.get('session_id')

        with engine.connect() as conn:
            query = text("""
                SELECT `course_code`
                FROM `sessions`
                WHERE `ID` = :session_id
                AND `activity` = 'clicked'
                ORDER BY `timestamp` DESC
                LIMIT 1;
            """)

            result = conn.execute(query, {"session_id":session_id})
            row = result.fetchone()

        if row is None:
            # Handle the case where no data was found
            return [], None

        starting_course = row[0]

        if starting_course not in transition_matrix:
            return [], None

        next_courses = list(transition_matrix[starting_course].keys())
        probabilities = list(transition_matrix[starting_course].values())
      
        return next_courses, random.choices(next_courses, weights=probabilities, k=1)[0]

    next_courses, predicted_course = predict_next_course()

    def return_next_courses(next_courses):
        if not next_courses:
          return []
      
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM courses WHERE course_code IN :next_courses"),
                {"next_courses": tuple(next_courses)}
            )

            next_courses = []
            columns = result.keys()
            for row in result:
                result_dict = {column: value for column, value in zip(columns, row)}
                next_courses.append(result_dict)
            return next_courses

    recommended_courses = return_next_courses(next_courses)

    return recommended_courses