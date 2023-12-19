# Prototype web application: Osiris Catalogus Tilburg University
This repository hosts the code for the course catalogue web app prototype from Tilburg University. The primary goal of this project is to revolutionize the way students discover new courses by implementing and testing various recommendation systems and search algorithms. The app is built using Flask in Python.


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
