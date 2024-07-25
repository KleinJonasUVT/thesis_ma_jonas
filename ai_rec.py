# imports
import os
import time
import numpy as np

import openai
from openai.embeddings_utils import get_embedding

from cosine import KNearestNeighbours

# Set your OpenAI API key here
openai.api_key = os.environ['OpenAi_API']

# constants
EMBEDDING_MODEL = "text-embedding-ada-002"

def print_recommendations_from_strings(db, session_id):

    start = time.time()
    query_embedding = db.get_latest_favourite(session_id)
    print("Time taken fetch embedding assoc. with session: ", round(time.time() - start), " s.")

    if query_embedding.empty:
        # Handle the case where no data was found
        return []
    else:
        query = np.array(query_embedding["embedding"][0].split(), dtype=float)
    
    # Calculate distances
    start = time.time()
    knearest = KNearestNeighbours(db, batch_size=500, metric="cosine")
    course_codes_tuple = tuple(knearest.fetch_k_closest(query, k=5))
    print("Time taken fetch nearest neighbours: ", round(time.time() - start), " s.")
    print("Tuples: \n", course_codes_tuple)

    start = time.time()
    courses = db.get_recommended_courses(course_codes_tuple)
    print("Time taken fetch recomm. courses: ", round(time.time() - start), " s.")

    return courses

def ai_search_results(db, query):

    query_embedding = get_embedding(query, engine=EMBEDDING_MODEL)

    # Calculate distances
    start = time.time()
    knearest = KNearestNeighbours(db, batch_size=500, metric="cosine")
    similar_course_codes = tuple(knearest.fetch_k_closest(query_embedding, k=6))
    print("Time taken fetch nearest neighbours: ", round(time.time() - start), " s.")
    print("Tuples: \n", similar_course_codes)

    start = time.time()
    similar_courses = db.get_recommended_courses(similar_course_codes)
    print("Time taken fetch recomm. courses: ", round(time.time() - start), " s.")

    return similar_courses