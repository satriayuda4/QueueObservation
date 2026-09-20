import os
import json
import sqlite3
import datetime
import csv
import io
import re
from flask import Flask, render_template, request, redirect, url_for, Response, flash

app = Flask(__name__)
app.secret_key = "queue_observation_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEFAULT_DB = "db2.sqlite"


def ensure_instance_dir():
    os.makedirs(INSTANCE_DIR, exist_ok=True)


def get_config():
    ensure_instance_dir()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    config = {"active_db": DEFAULT_DB}
    save_config(config)
    return config


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_active_db_name():
    config = get_config()
    db_name = config.get("active_db", DEFAULT_DB)
    db_name = os.path.basename(db_name)
    if not (db_name.endswith(".sqlite") or db_name.endswith(".db")):
        db_name = f"{db_name}.sqlite"
    return db_name


def get_db_connection(db_name=None):
    ensure_instance_dir()
    if not db_name:
        db_name = get_active_db_name()
    db_path = os.path.join(INSTANCE_DIR, os.path.basename(db_name))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_name=None):
    ensure_instance_dir()
    conn = get_db_connection(db_name)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(100),
                arrive_time VARCHAR(100),
                start_time VARCHAR(100),
                fin_time VARCHAR(100)
            )
        """
        )
    conn.close()


def list_databases():
    ensure_instance_dir()
    files = [
        f
        for f in os.listdir(INSTANCE_DIR)
        if f.endswith(".sqlite") or f.endswith(".db")
    ]
    files.sort()
    return files


@app.context_processor
def inject_global_vars():
    return {"active_db": get_active_db_name()}


@app.route("/")
def index():
    init_db()
    conn = get_db_connection()
    todo_list = conn.execute("SELECT * FROM todo ORDER BY id ASC").fetchall()
    conn.close()
    return render_template("base.html", todo_list=todo_list)


@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    if title:
        now = datetime.datetime.now()
        arrive_time = now.strftime("%H:%M:%S")
        conn = get_db_connection()
        with conn:
            conn.execute(
                "INSERT INTO todo (title, arrive_time, start_time, fin_time) VALUES (?, ?, ?, ?)",
                (title, arrive_time, "", ""),
            )
        conn.close()
    return redirect(url_for("index"))


@app.route("/start/<int:todo_id>")
def start(todo_id):
    now = datetime.datetime.now()
    conn = get_db_connection()
    with conn:
        conn.execute(
            "UPDATE todo SET start_time = ? WHERE id = ?",
            (now.strftime("%H:%M:%S"), todo_id),
        )
    conn.close()
    return redirect(url_for("index"))


@app.route("/finish/<int:todo_id>")
def finish(todo_id):
    now = datetime.datetime.now()
    conn = get_db_connection()
    with conn:
        conn.execute(
            "UPDATE todo SET fin_time = ? WHERE id = ?",
            (now.strftime("%H:%M:%S"), todo_id),
        )
    conn.close()
    return redirect(url_for("index"))


@app.route("/export")
def export():
    active_db = get_active_db_name()
    init_db(active_db)
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT id, title, arrive_time, start_time, fin_time FROM todo ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "arrive_time", "start_time", "fin_time"])
    for row in rows:
        writer.writerow(
            [
                row["id"],
                row["title"],
                row["arrive_time"],
                row["start_time"],
                row["fin_time"],
            ]
        )

    base_name = os.path.splitext(active_db)[0]
    filename = f"{base_name}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/config")
def config_page():
    active_db = get_active_db_name()
    init_db(active_db)
    databases = list_databases()
    return render_template("config.html", databases=databases, active_db=active_db)


@app.route("/config/set", methods=["POST"])
def set_database():
    db_name = request.form.get("db_name", "").strip()
    if db_name:
        db_name = os.path.basename(db_name)
        databases = list_databases()
        if db_name in databases:
            config = get_config()
            config["active_db"] = db_name
            save_config(config)
            init_db(db_name)
            flash(f"Switched active database to {db_name}", "success")
        else:
            flash(f"Database {db_name} does not exist.", "error")
    return redirect(url_for("config_page"))


@app.route("/config/create", methods=["POST"])
def create_database():
    new_name = request.form.get("new_db_name", "").strip()
    if new_name:
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", os.path.splitext(new_name)[0])
        if clean_name:
            filename = f"{clean_name}.sqlite"
            init_db(filename)
            if request.form.get("set_active") == "1":
                config = get_config()
                config["active_db"] = filename
                save_config(config)
                flash(f"Created and switched to database {filename}", "success")
            else:
                flash(f"Created database {filename}", "success")
        else:
            flash("Invalid database name provided.", "error")
    return redirect(url_for("config_page"))


@app.route("/config/delete", methods=["POST"])
def delete_database():
    db_name = request.form.get("db_name", "").strip()
    if db_name:
        db_name = os.path.basename(db_name)
        active_db = get_active_db_name()
        if db_name == active_db:
            flash(
                "Cannot delete the currently active database. Please switch to another database first.",
                "warning",
            )
        else:
            db_path = os.path.join(INSTANCE_DIR, db_name)
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    flash(f"Database {db_name} deleted successfully.", "info")
                except Exception as e:
                    flash(f"Failed to delete database: {str(e)}", "error")
            else:
                flash("Database file not found.", "error")
    return redirect(url_for("config_page"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", debug=True)
