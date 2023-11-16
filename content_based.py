from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import os
from flask import session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from database import load_courses_from_db, load_last_viewed_courses_from_db

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

# Define stopwords
stop_words_english = stopwords.words('english')
stop_words_dutch = stopwords.words('dutch')
custom_stop_words = ['course', 'subject', 'objective', 'content', 'aims', 'student', 'students', 'able', 'exam', 'pass', 'study', 'program', 'ects', 'understand', 'courses',
'grade', 'grades', 'assignment', 'assignments', 'completion', 'master', 'level', 'apply', 'vak', 'cursus', 'university', 'research', 'their', 'data', "course", "program", 
"semester", "class", "lecture", "syllabus", "academic", "department", "faculty", "credit", "prerequisite", "enrollment", "registration", "study", "degree", "student",
"curriculum", "instruction", "assessment", "assignment", "grading", "exam", "teaching", "learning", "module", "professor", "instructor", "advisor", "textbook", "research", 
"thesis", "dissertation"]
stop_words = list(set(stop_words_english + stop_words_dutch + custom_stop_words))

# Define a TF-IDF Vectorizer Object. Remove all English stop words
tfidf = TfidfVectorizer(stop_words=stop_words)

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
course_codes = courses_df['course_code']
# Create a DataFrame from the cosine_sim matrix
cosine_sim_df = pd.DataFrame(cosine_sim, index=course_codes, columns=course_codes)
print(cosine_sim_df)

# Create an empty dictionary to store the similar courses
similar_courses_dict = {}

# Iterate through each column in the cosine similarity DataFrame
for course_code in cosine_sim_df.columns:
    # Sort the courses based on similarity score in descending order
    sorted_courses = cosine_sim_df[course_code].sort_values(ascending=False)

    # Exclude the course itself and get the top 15 similar courses
    similar_scores = sorted_courses[sorted_courses < 1.0]
    top_similar_courses = similar_scores.index[1:31].tolist()

    # Store the top similar courses in the dictionary
    similar_courses_dict[course_code] = top_similar_courses

def get_content_based_courses():
  session_id = session.get('session_id')
  # Take course code as input and outputs most similar courses
  last_viewed_courses = load_last_viewed_courses_from_db()
  if last_viewed_courses:
    last_viewed_course_codes = [course['course_code'] for course in last_viewed_courses]

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

  similar_course_codes_1 = similar_courses_dict[starting_course_1]
  similar_course_codes_1 = [course for course in similar_course_codes_1 if course not in last_viewed_course_codes]
  similar_course_codes_1 = similar_course_codes_1[:9]

  #with engine.connect() as conn:
  #    query = text("""
  #        SELECT `course_code`
  #        FROM `sessions`
  #        WHERE `ID` = :session_id
  #            AND (`activity` = 'clicked' OR `activity` = 'favorited')
  #        ORDER BY `timestamp` DESC
  #        LIMIT 1,1;
  #    """)
#
  #    result = conn.execute(query, {"session_id":session_id})
  #    row = result.fetchone()
#
  #if row is None:
  #    # Handle the case where no data was found
  #    course_codes_tuple_1 = tuple(similar_course_codes_1)
#
  #    def load_similar_courses_from_db():
  #      with engine.connect() as conn:
  #          query = "SELECT course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers FROM courses WHERE course_code IN :similar_course_codes ORDER BY CASE"
  #      
  #          for i, code in enumerate(similar_course_codes_1, start=1):
  #              query += f" WHEN :code{i} THEN {i}"
  #                  
  #          query += " END"
  #                  
  #          # Execute the dynamically generated query
  #          query_params = {'similar_course_codes': course_codes_tuple_1}
  #          query_params.update({f'code{i}': code for i, code in enumerate(similar_course_codes_1, start=1)})
  #                  
  #          result = conn.execute(text(query), query_params)
  #          courses = []
  #          columns = result.keys()
  #          for row in result:
  #              result_dict = {column: value for column, value in zip(columns, row)}
  #              courses.append(result_dict)
  #          return courses
#
  #    similar_courses_1 = load_similar_courses_from_db()
  #    
  #    return similar_courses_1
#
  #starting_course_2 = row[0]
#
  #similar_course_codes_2 = similar_courses_dict[starting_course_2]
  #similar_course_codes_2 = [course for course in similar_course_codes_2 if course not in last_viewed_course_codes]
  #similar_course_codes_2 = similar_course_codes_2[:4]
#
  similar_course_codes = similar_course_codes_1 #+ similar_course_codes_2
  course_codes_tuple = tuple(similar_course_codes)

  def load_similar_courses_from_db():
    with engine.connect() as conn:
        query = "SELECT course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers FROM courses WHERE course_code IN :similar_course_codes ORDER BY CASE"
        
        for i, code in enumerate(similar_course_codes, start=1):
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