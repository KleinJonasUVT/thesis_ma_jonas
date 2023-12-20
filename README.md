# Prototype web application: Course Catalogus Tilburg University
This repository contains the Python and Flask-based code for the web app developed as part of Jonas Klein's Master's thesis in Marketing Analytics at Tilburg University. The app is a practical implementation to study the efficacy of AI-based embedding techniques, particularly GPT models, versus traditional TF-IDF models in recommendation systems.

# Thesis
The thesis, titled "AI-based Embedding Techniques in Recommendation Systems," compares AI-driven recommendations with traditional methods. Using Tilburg University's course catalog as a case study, it explores how these technologies affect the personalization and effectiveness of course recommendations for students.

## Running this project

### Using Docker

The easiest way to run this project is using Docker.

- [Install Docker](docs/install_docker.md) and clone this repository.
- Open the terminal at the repository's root directory and run the following command: `docker build -t thesis_ma_jonas .`
- Ask the contributors of this repository for access to the connection string to the database in which all credentials are stored and for the Open Ai API key and run the following command: `docker run -e DB_CONNECTION_STRING="actual_connection_string" -e OpenAi_API="actual_api_key" -dp 127.0.0.1:5000:5000 thesis_ma_jonas`. Replace `actual_connection_string` with the actual connection string and `actual_api_key` with the actual api key you received from the contributors.
- Wait a bit for the website and API to be launched. If the process breaks, you likely haven't allocated enough memory (e.g., the built takes about 6 GB of memory)
- Once docker has been launched, you can access the website at these addresses:
    - `[http://localhost:5000](http://127.0.0.1:5000)`
    - `[http://localhost:5000](http://172.17.0.2:5000)`
- Press Ctrl + C in the terminal to quit.
