from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import os
from flask import session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from database import load_courses_from_db

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

# Define a TF-IDF Vectorizer Object. Remove all English stop words
tfidf = TfidfVectorizer(stop_words='english')

# Combine 'aims' and 'content' columns
courses_df['combined_text'] = courses_df['aims'].fillna('') + ' ' + courses_df['content'].fillna('')

# Convert text to lowercase and remove special characters
courses_df['combined_text'] = courses_df['combined_text'].str.lower()
symbols = "!\"#$%&()*+-./:;<=>?@[\]^_`{|}~\n"
for i in symbols:
    courses_df['combined_text'] = courses_df['combined_text'].replace(i, ' ')

# Construct the required TF-IDF matrix by fitting and transforming the data
tfidf_matrix = tfidf.fit_transform(courses_df['combined_text'])

# Compute the cosine similarity matrix
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

# Construct a reverse map of indices and course codes
indices = pd.Series(courses_df.index, index=courses_df['course_code']).drop_duplicates()

# Take course code as input and outputs most similar courses
def formula_content_based_courses():
        def get_content_based_courses():
            session_id = session.get('session_id')
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
                return [], None

            starting_course = row[0]

            # Get the index of the course that matches the course_code
            idx = indices[starting_course]

            # Get the pairwise similarity scores of all courses with that course
            sim_scores = list(enumerate(cosine_sim[idx]))

            # Sort the courses based on the similarity scores
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

            # Get the scores of the 10 most similar courses
            sim_scores = sim_scores[1:11]

            # Get the course indices
            course_indices = [i[0] for i in sim_scores]

            # Return the top 10 most similar courses
            return courses_df['course_code'].iloc[course_indices]

        content_based_courses = get_content_based_courses()

        def return_content_based_courses():
            content_based_courses = get_content_based_courses()

            with engine.connect() as conn:
                try:
                    result = conn.execute(
                        text("SELECT * FROM courses WHERE course_code IN :content_based_courses"),
                        {"content_based_courses": content_based_courses.tolist()}
                    )

                    content_based_courses_result = []
                    columns = result.keys()
                    for row in result:
                        result_dict = {column: value for column, value in zip(columns, row)}
                        content_based_courses_result.append(result_dict)
                    return content_based_courses_result
                except Exception as e:
                    return []

        rec_content_based_courses = return_content_based_courses()
        return rec_content_based_courses

