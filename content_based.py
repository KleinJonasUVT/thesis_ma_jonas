import pandas as pd
from flask import session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from nltk.corpus import stopwords

def get_content_based_courses(db):

  session_id = session.get('session_id')

  # # Take course code as input and outputs most similar courses
  # last_viewed_courses = db.load_last_viewed_courses_from_db(session_id)
  # if last_viewed_courses:
  #     last_viewed_course_codes = [course['course_code'] for course in last_viewed_courses]

  # Use pd.read_sql() to execute the query and retrieve data into a DataFrame
  courses_df_rec = db.get_latest_recommended(session_id)

  if courses_df_rec.empty:
      # Handle the case where no data was found
      return []

  course_codes_tuple = get_similar_courses(db.load_courses_from_db())

  return db.get_recommended_courses(course_codes_tuple)

def get_similar_courses(courses_df):

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