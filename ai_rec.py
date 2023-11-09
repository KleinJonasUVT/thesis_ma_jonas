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
from database import load_courses_from_db
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

# Combine 'aims' and 'content' columns
courses_df['combined_text'] = courses_df['aims'].fillna('') + ' ' + courses_df['content'].fillna('')

# Convert text to lowercase and remove special characters
courses_df['combined_text'] = courses_df['combined_text'].str.lower()
symbols = "!\"#$%&()*+-./:;<=>?@[\]^_`{|}~\n"
for i in symbols:
    courses_df['combined_text'] = courses_df['combined_text'].replace(i, ' ')

# Use the SQLAlchemy engine to execute the query and retrieve the data
with engine.connect() as conn:
    result_1 = conn.execute(text("SELECT embedding FROM courses LIMIT 1001"))

    # Convert the result to a list of embedding strings
    embedding_strings_1 = [row[0] for row in result_1]

# Convert the embedding strings to lists of floats
embeddings_list_of_lists = []
for embedding_str in embedding_strings_1:
    # Assuming the embeddings are stored as space-separated values in the 'embedding' column
    embedding_values_1 = [float(value) for value in embedding_str.split()]
    embeddings_list_of_lists.append(embedding_values_1)

with engine.connect() as conn:
    result_2 = conn.execute(text("SELECT embedding FROM courses LIMIT 1001, 1001"))

    # Convert the result to a list of embedding strings
    embedding_strings_2 = [row[0] for row in result_2]

for embedding_str in embedding_strings_2:
    # Assuming the embeddings are stored as space-separated values in the 'embedding' column
    embedding_values_2 = [float(value) for value in embedding_str.split()]
    embeddings_list_of_lists.append(embedding_values_2)

def print_recommendations_from_strings():
    session_id = session.get('session_id')

    course_codes = courses_df["course_code"].tolist()

    # get embeddings for all strings
    embeddings = embeddings_list_of_lists

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
        similar_course_codes = similar_course_codes_1
        course_codes_tuple = tuple(similar_course_codes)

        def load_similar_courses_from_db():
            with engine.connect() as conn:
                result = conn.execute(text("""
                SELECT 
                course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers 
                FROM courses 
                WHERE course_code IN :similar_course_codes
                """), {'similar_course_codes': course_codes_tuple})
                courses = []
                columns = result.keys()
                for row in result:
                    result_dict = {column: value for column, value in zip(columns, row)}
                    courses.append(result_dict)
                return courses

        similar_courses = load_similar_courses_from_db()
        return similar_courses

    starting_course_2 = row[0]

    index_of_source_string_2 = courses_df[courses_df["course_code"] == starting_course_2].index[0]

    # get the embedding of the source string
    query_embedding_2 = embeddings[index_of_source_string_2]
    # get distances between the source embedding and other embeddings (function from embeddings_utils.py)
    distances = distances_from_embeddings(query_embedding_1, embeddings, distance_metric="cosine")
    # get indices of nearest neighbors (function from embeddings_utils.py)
    indices_of_nearest_neighbors_2 = indices_of_nearest_neighbors_from_distances(distances)
    indices_of_4_nearest_neighbors_2 = indices_of_nearest_neighbors_1[:4]

    course_codes_of_nearest_neighbors_2 = [course_codes[i] for i in indices_of_4_nearest_neighbors_2]

    course_codes_of_nearest_neighbors = course_codes_of_nearest_neighbors_1 + course_codes_of_nearest_neighbors_2

    course_codes_tuple = tuple(course_codes_of_nearest_neighbors)

    def load_similar_courses_from_db():
        with engine.connect() as conn:
            result = conn.execute(text("""
            SELECT 
            course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers 
            FROM courses 
            WHERE course_code IN :similar_course_codes
            """), {'similar_course_codes': course_codes_tuple})
            courses = []
            columns = result.keys()
            for row in result:
                result_dict = {column: value for column, value in zip(columns, row)}
                courses.append(result_dict)
            return courses

    similar_courses = load_similar_courses_from_db()

    return similar_courses