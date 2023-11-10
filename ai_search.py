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
from app import app, request

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

def ai_search_results(query):
    query_embedding = get_embedding(query, EMBEDDING_MODEL)
    course_embeddings = get_embeddings_from_db()

    distances = distances_from_embeddings(query_embedding, course_embeddings, distance_metric="cosine")
    # get indices of nearest neighbors (function from embeddings_utils.py)
    indices_of_nearest_neighbors = indices_of_nearest_neighbors_from_distances(distances)

    # find courses based on the indexes
    similar_course_codes = [course_codes[i] for i in indices_of_nearest_neighbors]
    similar_course_codes_tuple = tuple(similar_course_codes)

    def load_search_courses_from_db():
            with engine.connect() as conn:
                result = conn.execute(text("""
                SELECT 
                course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers 
                FROM courses 
                WHERE course_code IN :similar_course_codes
                """), {'similar_course_codes': similar_course_codes_tuple})
                courses = []
                columns = result.keys()
                for row in result:
                    result_dict = {column: value for column, value in zip(columns, row)}
                    courses.append(result_dict)
                return courses

    similar_courses = load_search_courses_from_db()
    return similar_courses