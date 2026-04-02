# Queue Observation App

A lightweight, responsive web application built with Python, Flask, and Semantic UI. This tool is designed to observe and track the lifecycle of subjects in a queue by recording precise timestamps for when a subject arrives, when their service begins, and when their service is completed.

## Features

* **Track Subject Lifecycle:** Log individual subjects (e.g., "Person Properties") and monitor their progress through a queue.
* **Timestamp Recording:** Automatically captures the current time for `arrive_time`, `start_time`, and `fin_time` at each stage.
* **Clean User Interface:** Utilizes Semantic UI via CDN for a modern, responsive, and mobile-friendly dashboard without the need for custom CSS.
* **SQLite Database:** Uses Flask-SQLAlchemy for lightweight, local data storage.
* **Network Accessible:** Runs on `0.0.0.0`, allowing the app to be accessed by other devices on your local network (like a tablet or phone used for observation).

## Prerequisites

Make sure you have Python installed. You will also need to install the required Python packages.

```bash
pip install Flask Flask-SQLAlchemy
```

## Project Structure

Ensure your project directory is organized as follows:

```text
/your_project_folder
│
├── app.py               # The main Flask application
└── /templates           # Folder containing your HTML files
    └── base.html        # The Semantic UI dashboard template
```

## Setup & Initialization

Before running the app for the first time, you must initialize the SQLite database (`db2.sqlite`). 

Open your terminal, navigate to your project folder, and open the Python interactive shell to create the database:

```python
from app import app, db
with app.app_context():
    db.create_all()
```
This will generate the `db2.sqlite` file with the required `Todo` table schema.

## Running the Application

Start the Flask development server by running:

```bash
python app.py
```

The application will start in debug mode. You can access the dashboard in your web browser at:
* **Local Machine:** `http://127.0.0.1:5000`
* **Local Network:** `http://<your-local-ip-address>:5000` (Useful for observing on a mobile device)

## Application Endpoints

| Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Renders the main dashboard (`base.html`) and displays all queued subjects. |
| `POST` | `/add` | Captures the subject's properties from the form, logs the `arrive_time`, and adds them to the queue. |
| `GET` | `/start/<id>` | Updates the `start_time` of the specified subject to the current time. |
| `GET` | `/finish/<id>` | Updates the `fin_time` of the specified subject to the current time. |

## Exporting Observation Data

To analyze your queue metrics (such as calculating average wait times or service times), you can export the SQLite database directly to a CSV file.

Open your terminal or command prompt and run the following SQLite command (adjust the path to match your actual database location):

```bash
sqlite3 -header -csv c:/sqlite/db2.sqlite "select * from todo;" > todo.csv
```
