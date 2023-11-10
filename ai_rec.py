# imports
import pandas as pd
import pickle
from sqlalchemy import create_engine
from sqlalchemy import text
import os
import openai
from openai.embeddings_utils import (
    get_embedding,
    distances_from_embeddings,
    tsne_components_from_embeddings,
    chart_from_components,
    indices_of_nearest_neighbors_from_distances,
)
from database import load_courses_from_db, get_embeddings_from_db
from flask import session

# Set your OpenAI API key here
openai.api_key = os.environ['OpenAi_API']

# constants
EMBEDDING_MODEL = "text-embedding-ada-002"

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

courses_dict = load_courses_from_db()
courses_df = pd.DataFrame(courses_dict)

def print_recommendations_from_strings():
    session_id = session.get('session_id')

    course_codes = courses_df["course_code"].tolist()

    # get embeddings for all strings
    embeddings = get_embeddings_from_db()

    # Check for empty embeddings and remove them
    valid_indices = [i for i, emb in enumerate(embeddings) if len(emb) > 0]
    embeddings = [emb for emb in embeddings if len(emb) > 0]
    course_codes = [course_codes[i] for i in valid_indices]

    with engine.connect() as conn:
        query = text("""
            SELECT `course_code`
            FROM `sessions`
            WHERE `ID` = :session_id
                AND (`activity` = 'clicked' OR `activity` = 'favorited')
            ORDER BY `timestamp` DESC
            LIMIT 1;
        """)

        result = conn.execute(query, {"session_id":session_id})
        row = result.fetchone()

    if row is None:
        # Handle the case where no data was found
        return []

    starting_course_1 = row[0]

    index_of_source_string_1 = courses_df[courses_df["course_code"] == starting_course_1].index[0]

    # get the embedding of the source string
    query_embedding_1 = embeddings[index_of_source_string_1]
    # get distances between the source embedding and other embeddings (function from embeddings_utils.py)
    distances = distances_from_embeddings(query_embedding_1, embeddings, distance_metric="cosine")
    # get indices of nearest neighbors (function from embeddings_utils.py)
    indices_of_nearest_neighbors_1 = indices_of_nearest_neighbors_from_distances(distances)
    indices_of_5_nearest_neighbors_1 = indices_of_nearest_neighbors_1[:5]

    course_codes_of_nearest_neighbors_1 = [course_codes[i] for i in indices_of_5_nearest_neighbors_1]

    with engine.connect() as conn:
        query = text("""
            SELECT `course_code`
            FROM `sessions`
            WHERE `ID` = :session_id
                AND (`activity` = 'clicked' OR `activity` = 'favorited')
            ORDER BY `timestamp` DESC
            LIMIT 1,1;
        """)

        result = conn.execute(query, {"session_id":session_id})
        row = result.fetchone()

    if row is None:
        # Handle the case where no data was found
        course_codes_of_nearest_neighbors_1 = course_codes_of_nearest_neighbors_1
        course_codes_tuple_1 = tuple(course_codes_of_nearest_neighbors_1)

        def load_similar_courses_from_db():
            with engine.connect() as conn:
                query = "SELECT course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers FROM courses WHERE course_code IN :similar_course_codes ORDER BY CASE"
        
                for i, code in enumerate(course_codes_of_nearest_neighbors_1, start=1):
                    query += f" WHEN :code{i} THEN {i}"
                        
                query += " END"
                        
                # Execute the dynamically generated query
                query_params = {'similar_course_codes': course_codes_tuple_1}
                query_params.update({f'code{i}': code for i, code in enumerate(similar_course_codes, start=1)})
                        
                result = conn.execute(text(query), query_params)
                courses = []
                columns = result.keys()
                for row in result:
                    result_dict = {column: value for column, value in zip(columns, row)}
                    courses.append(result_dict)
                return courses

        similar_courses_1 = load_similar_courses_from_db()
        return similar_courses_1

    starting_course_2 = row[0]

    index_of_source_string_2 = courses_df[courses_df["course_code"] == starting_course_2].index[0]

    # get the embedding of the source string
    query_embedding_2 = embeddings[index_of_source_string_2]
    # get distances between the source embedding and other embeddings (function from embeddings_utils.py)
    distances = distances_from_embeddings(query_embedding_2, embeddings, distance_metric="cosine")
    # get indices of nearest neighbors (function from embeddings_utils.py)
    indices_of_nearest_neighbors_2 = indices_of_nearest_neighbors_from_distances(distances)
    indices_of_4_nearest_neighbors_2 = indices_of_nearest_neighbors_2[:4]

    course_codes_of_nearest_neighbors_2 = [course_codes[i] for i in indices_of_4_nearest_neighbors_2]

    course_codes_of_nearest_neighbors = course_codes_of_nearest_neighbors_1 + course_codes_of_nearest_neighbors_2

    course_codes_tuple = tuple(course_codes_of_nearest_neighbors)

    def load_similar_courses_from_db():
        with engine.connect() as conn:
            query = "SELECT course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers FROM courses WHERE course_code IN :similar_course_codes ORDER BY CASE"
    
            for i, code in enumerate(course_codes_of_nearest_neighbors, start=1):
                query += f" WHEN :code{i} THEN {i}"
                    
            query += " END"
                    
            # Execute the dynamically generated query
            query_params = {'similar_course_codes': course_codes_tuple}
            query_params.update({f'code{i}': code for i, code in enumerate(similar_course_codes, start=1)})
                    
            result = conn.execute(text(query), query_params)
            courses = []
            columns = result.keys()
            for row in result:
                result_dict = {column: value for column, value in zip(columns, row)}
                courses.append(result_dict)
            return courses

    similar_courses = load_similar_courses_from_db()

    return similar_courses