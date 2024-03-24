# CiSTUP_Vehicle_P10
Project 10 @ Web Development

# Vehicle Detection Project

This project is aimed at implementing vehicle detection using YOLOv5 model from Ultralytics. It utilizes Flask as the web framework and integrates with MySQL for data storage.

## Installation

- Clone the repository:
   ```bash
   git clone https://github.com/your-username/vehicle-detection.git

   
## 1. Navigate to the project directory:
cd vehicle-detection

## 2. Install the required dependencies:
pip install -r requirements.txt

## 3. Dataset
The dataset used for training the vehicle detection model can be found here: https://universe.roboflow.com/roboflow-100/vehicles-q0x2v

## 4. Usage
- Make sure you have a MySQL server running.

- Configure the MySQL connection in app.py:
# Modify the following variables according to your MySQL configuration
``` python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'username'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'database_name'

- Run the Flask application:
  python app.py
- Access the application in your web browser at http://localhost:80.

## 5. Directory Structure:
- app.py: *Main Flask application file.*
- templates/: *Contains HTML templates for the Flask application.*
- static/: *Contains static files (e.g., CSS, JavaScript).*
- requirements.txt: *List of Python dependencies for the project.*
- Dockerfile: *Dockerfile for building the Docker image.*
- docker-compose.yml: *Docker Compose YAML file for running the application with Docker.*

