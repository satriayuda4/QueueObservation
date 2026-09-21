# Queue Observation App

A modern, high-precision queue observation and time-study web application built with **Python**, **Flask**, **Tailwind CSS**, and **Lucide Icons**. 

This application is designed to conduct real-world queue timing observations (e.g., bank tellers, customer service desks, triage, point-of-sale stations, and industrial engineering time studies). It separates the operational **Live Observation Counter** from the high-level **Analytics Dashboard** to provide distraction-free real-time timing in the field alongside comprehensive performance analytics.

---

## Features

* **Real-Time Observation Counter (`/counter`):**
  * **Live Ticking Service Stopwatch:** A prominent digital timer displaying elapsed service time in real-time (`HH:MM:SS`) for the subject currently at the station.
  * **1-Click "Finish & Call Next":** Atomically completes the current subject's service and immediately starts timing the next waiting person with zero observational delay.
  * **Rapid Arrival Logging:** Quick-add input with auto-numbering fallback (`Subject #N`) and `Enter`-key support for rapid logging.
  * **FIFO Waiting Queue:** Real-time queue view showing how long each waiting subject has been in line (`Waiting: 2m 14s`) with quick Start and Cancel buttons.
  * **Zero-Reload Smooth AJAX:** All counter actions update asynchronously via background API requests, keeping the stopwatches ticking smoothly without page reloads.
  * **Recently Completed Feed:** Real-time log of recently finished observations with instant wait and service duration badges.

* **Analytics Dashboard (`/`):**
  * **Queue Efficiency Metrics:** Overview cards displaying total observations, current queue length, **Average Wait Time**, **Average Service Duration**, and **Average Total Queue Time** (Wait + Service).
  * **Active Station Status Banner:** Real-time indicator showing if the counter is currently serving a subject, with a quick shortcut to the live counter.
  * **Searchable & Filterable Records Table:** Chronological log of all subjects, timestamps, and calculated duration metrics. Includes instant client-side search and status filter tabs (`All`, `Waiting`, `In Service`, `Completed`).

* **Modern UI & Left Sidebar Navigation:**
  * Clean **Tailwind CSS** and **Lucide Icons** interface styled in a modern Indigo & Slate aesthetic.
  * Fixed desktop left sidebar with active database status indicator, quick navigation tabs, and a mobile slide-out drawer for smartphone/tablet field observation.

* **Multi-Database Management (`/config`):**
  * Create, switch, and delete individual SQLite database files directly from the UI (ideal for tracking separate shifts, days, or counter locations).
  * Auto-initializes SQLite database schemas upon creation or startup.

* **One-Click CSV Export:**
  * Download observation records from the active database directly as a `.csv` file for external statistical modeling or reporting in Excel, R, or Python.

* **Network Accessible:**
  * Runs on `0.0.0.0:5000`, enabling observation from mobile phones, tablets, or laptops over the local Wi-Fi network.

---

## Prerequisites

* Python 3.8+
* Flask (see `requirements.txt`)

To install dependencies:

```bash
pip install -r requirements.txt
```

---

## Project Structure

```text
QueueObservation/
│
├── app.py               # Main Flask application, routes, and duration math engine
├── config.json          # Configuration storing the active database setting
├── requirements.txt     # Python dependencies
├── README.md            # Application documentation
├── instance/            # SQLite database storage directory
│   └── db2.sqlite       # Default SQLite database
└── templates/           # Jinja2 HTML templates
    ├── base.html        # Main layout shell with left sidebar, mobile header & alerts
    ├── counter.html     # High-precision Observation Counter with live stopwatches
    ├── index.html       # Analytics Dashboard, metric cards & searchable records table
    └── config.html      # Database configuration and session management
```

---

## Setup & Running the Application

The database and table schemas are initialized automatically when the app starts.

Start the Flask development server:

```bash
python app.py
```

The application will start on port `5000`:
* **Local Machine:** `http://127.0.0.1:5000`
* **Local Network:** `http://<your-local-ip-address>:5000` (Open this on your mobile tablet/phone for field observation)

---

## Application Views & Navigation

| Screen | Route | Description |
| :--- | :--- | :--- |
| **Live Counter** | `/counter` | Dedicated real-time observation console with live ticking stopwatches, FIFO line, and 1-click progression. |
| **Analytics Dashboard** | `/` | Queue performance metrics, averages (wait, service, total), and searchable observation records log. |
| **Database Config** | `/config` | Manage session databases, switch active observation shift, or create new SQLite files. |

---

## Application Endpoints

| Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Renders the Analytics Dashboard with summary metrics, averages, and the records table. |
| `GET` | `/counter` | Renders the dedicated Observation Counter console. |
| `GET` | `/api/state` | Returns the live counter state as JSON (active subject, waiting queue, completed list, stats). |
| `POST` | `/add` | Logs an arrival timestamp. Auto-generates subject title if left blank. Supports both AJAX and form submission. |
| `GET` / `POST` | `/start/<id>` | Records the `start_time` for the specified subject. |
| `GET` / `POST` | `/finish/<id>` | Records the `fin_time` for the specified subject. |
| `GET` / `POST` | `/finish_and_next/<id>` | Completes the current subject and immediately starts the next waiting subject in queue. |
| `GET` / `POST` | `/delete/<id>` | Removes an accidental queue entry without polluting dataset statistics. |
| `GET` | `/export` | Generates and downloads a CSV export of all observations from the active database. |
| `GET` | `/config` | Renders the database configuration view. |
| `POST` | `/config/set` | Switches the active SQLite database. |
| `POST` | `/config/create` | Creates and initializes a new SQLite database file. |
| `POST` | `/config/delete` | Deletes an inactive SQLite database file. |

---

## Exporting Observation Data

You can export your observation metrics (including arrival time, service start time, and completion time) at any time:

1. **Via Sidebar / Navigation:** Click the **"Export CSV"** button located at the bottom of the left sidebar or at the top of the dashboard.
2. **Direct Download URL:** Visit `http://127.0.0.1:5000/export` in your browser.
