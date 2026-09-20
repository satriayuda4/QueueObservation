# Queue Observation App

A lightweight, responsive web application built with Python, Flask, and Semantic UI. This tool is designed to observe and track the lifecycle of subjects in a queue by recording precise timestamps for when a subject arrives, when their service begins, and when their service is completed.

## Features

* **Track Subject Lifecycle:** Log individual subjects (e.g., "Person Properties") and monitor their progress through a queue.
* **Timestamp Recording:** Automatically captures the current time for `arrive_time`, `start_time`, and `fin_time` at each stage.
* **Clean User Interface:** Utilizes Semantic UI via CDN for a modern, responsive, and mobile-friendly dashboard without the need for custom CSS.
* **Built-in Automatic Database Initialization:** Automatically creates the SQLite database and `todo` table upon startup without needing manual setup commands.
* **Multi-Database Management:** Manage multiple database files directly from the UI—create new databases for different shifts/observations, switch between them instantly, or delete unused ones.
* **One-Click CSV Export:** Export observation data directly through the browser without needing external `sqlite3` CLI tools installed.
* **Network Accessible:** Runs on `0.0.0.0`, allowing the app to be accessed by other devices on your local network (like a tablet or phone used for observation).

## Prerequisites

Make sure you have Python installed. You will also need Flask:

```bash
pip install Flask
```

## Project Structure

Ensure your project directory is organized as follows:

```text
/your_project_folder
│
├── app.py               # The main Flask application
├── config.json          # Configuration storing the active database setting
├── /instance            # Folder containing your SQLite database files
│   └── db2.sqlite       # Default SQLite database
└── /templates           # Folder containing your HTML templates
    ├── base.html        # Main dashboard and navigation template
    └── config.html      # Database configuration and management template
```

## Setup & Running the Application

The database and table schemas are initialized automatically when the app starts.

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
| `GET` | `/export` | Generates and downloads a CSV file containing all observation records from the active database. |
| `GET` | `/config` | Renders the database configuration page to create, switch, and delete databases. |
| `POST` | `/config/set` | Sets the selected database file as active. |
| `POST` | `/config/create` | Creates a new SQLite database file and initializes its tables. |
| `POST` | `/config/delete` | Deletes a specified inactive SQLite database file. |

## Exporting Observation Data

You can export your observation metrics (to calculate wait times, service times, etc.) in two ways:

1. **Directly from the Dashboard:** Click the **"Export CSV"** button in the navigation bar, which automatically triggers a download of `<database_name>.csv`.
2. **Via Endpoint:** Visit `http://127.0.0.1:5000/export` in your browser.
