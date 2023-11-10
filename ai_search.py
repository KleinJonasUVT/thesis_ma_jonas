# imports
import pandas as pd
import pickle
from sqlalchemy import create_engine
from sqlalchemy import text
import os
import numpy as np
import openai
from openai.embeddings_utils import (
    get_embedding,
    cosine_similarity
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

def ai_search_results(query):
    query_embedding = get_embedding(query, engine=EMBEDDING_MODEL)
    course_embeddings = get_embeddings_from_db()
    course_codes = courses_df["course_code"].tolist()

    df = pd.DataFrame({'embeddings': course_embeddings})

    df["similarity"] = df.embeddings.apply(lambda x: cosine_similarity(x, query_embedding))

    top_similarity_row_numbers = df.nlargest(6, 'similarity').index.tolist()

    # find courses based on the indexes
    similar_course_codes = [course_codes[i] for i in top_similarity_row_numbers]
    similar_course_codes_tuple = tuple(similar_course_codes)

    def load_search_courses_from_db():
            with engine.connect() as conn:
                query = "SELECT course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers FROM courses WHERE course_code IN :similar_course_codes ORDER BY CASE"
        
                for i, code in enumerate(similar_course_codes, start=1):
                    query += f" WHEN :code{i} THEN {i}"
                
                query += " END"
                
                # Execute the dynamically generated query
                query_params = {'similar_course_codes': similar_course_codes_tuple}
                query_params.update({f'code{i}': code for i, code in enumerate(similar_course_codes, start=1)})
                
                result = conn.execute(text(query), query_params)
                courses = []
                columns = result.keys()
                for row in result:
                    result_dict = {column: value for column, value in zip(columns, row)}
                    courses.append(result_dict)
                return courses

    similar_courses = load_search_courses_from_db()
    return similar_courses