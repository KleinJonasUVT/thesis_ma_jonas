import os
import pandas as pd
import openai
import numpy as np
from openai.embeddings_utils import (
    get_embedding,
    cosine_similarity,
    distances_from_embeddings,
    indices_of_nearest_neighbors_from_distances,
)
from database import (
    load_courses_from_db,
    load_last_viewed_courses_from_db,
    load_favorite_courses_from_db,
)
import pymysql

openai.api_key = os.environ['OpenAi_API']
EMBEDDING_MODEL = "text-embedding-ada-002"


def connect_to_db():
    return pymysql.connect(
        host=os.environ['TIDB_HOST'],
        port=4000,
        user=os.environ['TIDB_USER'],
        password=os.environ['TIDB_PASSWORD'],
        database=os.environ['TIDB_DB_NAME'],
        ssl_verify_cert=True,
        ssl_verify_identity=True,
        ssl_ca='/etc/ssl/certs/ca-certificates.crt',
    )


connection = connect_to_db()

courses_dict = load_courses_from_db()
courses_df = pd.DataFrame(courses_dict)

embeddings_df = pd.read_sql("SELECT embedding FROM courses", con=connection)
embeddings_list_of_lists = [
    [float(v) for v in emb.split()] for emb in embeddings_df['embedding'].tolist()
]


def recommend_courses():
    """Recommend courses based on last viewed and favourite courses using embeddings."""
    course_codes = courses_df["course_code"].tolist()
    last_viewed = load_last_viewed_courses_from_db()
    favorites = load_favorite_courses_from_db()

    reference_codes = [c['course_code'] for c in last_viewed] + [c['course_code'] for c in favorites]
    if not reference_codes:
        return []

    embeddings = embeddings_list_of_lists
    valid_indices = [i for i, e in enumerate(embeddings) if len(e) > 0]
    embeddings = [embeddings[i] for i in valid_indices]
    course_codes = [course_codes[i] for i in valid_indices]
    code_to_index = {code: idx for idx, code in enumerate(course_codes)}

    indices = [code_to_index[c] for c in reference_codes if c in code_to_index]
    if not indices:
        return []

    mean_embedding = np.mean([embeddings[i] for i in indices], axis=0)
    distances = distances_from_embeddings(mean_embedding, embeddings, distance_metric="cosine")
    neighbour_indices = indices_of_nearest_neighbors_from_distances(distances)

    exclude = set(indices)
    neighbour_indices = [i for i in neighbour_indices if i not in exclude]
    top_indices = neighbour_indices[:9]

    recommended_codes = [course_codes[i] for i in top_indices]
    result_df = courses_df.set_index('course_code').loc[recommended_codes].reset_index()
    return result_df.to_dict('records')


def ai_search_results(query: str):
    query_embedding = get_embedding(query, engine=EMBEDDING_MODEL)
    df = pd.DataFrame({'embedding': embeddings_list_of_lists, 'course_code': courses_df['course_code']})
    df['similarity'] = df.embedding.apply(lambda x: cosine_similarity(x, query_embedding))
    df_sorted = df.sort_values('similarity', ascending=False)
    sorted_codes = df_sorted['course_code'].tolist()
    result_df = courses_df.set_index('course_code').loc[sorted_codes].reset_index()
    return result_df.to_dict('records')
