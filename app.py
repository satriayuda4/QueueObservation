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


def duration_in_seconds(start_str, end_str):
    if not start_str or not end_str:
        return None
    try:
        t_start = datetime.datetime.strptime(start_str, "%H:%M:%S")
        t_end = datetime.datetime.strptime(end_str, "%H:%M:%S")
        delta = t_end - t_start
        total_seconds = int(delta.total_seconds())
        if total_seconds < 0:
            total_seconds += 86400
        return total_seconds
    except Exception:
        return None


def format_seconds(seconds):
    if seconds is None:
        return "-"
    seconds = int(round(seconds))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_duration(start_str, end_str):
    sec = duration_in_seconds(start_str, end_str)
    if sec is None:
        return ""
    return format_seconds(sec)


def get_observation_data():
    init_db()
    conn = get_db_connection()
    raw_todos = conn.execute("SELECT * FROM todo ORDER BY id ASC").fetchall()
    conn.close()

    enriched_todos = []
    waiting_count = 0
    in_service_count = 0
    completed_count = 0

    wait_seconds_list = []
    service_seconds_list = []
    total_seconds_list = []

    active_subject = None

    for row in raw_todos:
        item = dict(row)
        arrive = item.get("arrive_time") or ""
        start = item.get("start_time") or ""
        fin = item.get("fin_time") or ""

        wait_sec = duration_in_seconds(arrive, start)
        svc_sec = duration_in_seconds(start, fin)
        total_sec = duration_in_seconds(arrive, fin)

        if fin:
            item["status"] = "completed"
            completed_count += 1
            if wait_sec is not None:
                wait_seconds_list.append(wait_sec)
            if svc_sec is not None:
                service_seconds_list.append(svc_sec)
            if total_sec is not None:
                total_seconds_list.append(total_sec)
        elif start:
            item["status"] = "in_service"
            in_service_count += 1
            if not active_subject:
                active_subject = item
            if wait_sec is not None:
                wait_seconds_list.append(wait_sec)
        else:
            item["status"] = "waiting"
            waiting_count += 1

        item["wait_sec"] = wait_sec
        item["service_sec"] = svc_sec
        item["total_sec"] = total_sec

        item["wait_duration"] = format_seconds(wait_sec) if wait_sec is not None else ""
        item["service_duration"] = format_seconds(svc_sec) if svc_sec is not None else ""
        item["total_duration"] = format_seconds(total_sec) if total_sec is not None else ""
        enriched_todos.append(item)

    avg_wait = (sum(wait_seconds_list) / len(wait_seconds_list)) if wait_seconds_list else None
    avg_service = (sum(service_seconds_list) / len(service_seconds_list)) if service_seconds_list else None
    avg_total = (sum(total_seconds_list) / len(total_seconds_list)) if total_seconds_list else None

    stats = {
        "total": len(enriched_todos),
        "waiting": waiting_count,
        "in_service": in_service_count,
        "completed": completed_count,
        "avg_wait": format_seconds(avg_wait) if avg_wait is not None else "-",
        "avg_service": format_seconds(avg_service) if avg_service is not None else "-",
        "avg_total": format_seconds(avg_total) if avg_total is not None else "-",
        "avg_wait_sec": round(avg_wait, 1) if avg_wait is not None else 0,
        "avg_service_sec": round(avg_service, 1) if avg_service is not None else 0,
    }

    waiting_queue = [t for t in enriched_todos if t["status"] == "waiting"]
    completed_recent = [t for t in enriched_todos if t["status"] == "completed"]
    completed_recent.reverse()

    return {
        "all_todos": enriched_todos,
        "active_subject": active_subject,
        "waiting_queue": waiting_queue,
        "completed_recent": completed_recent,
        "stats": stats,
    }


def is_ajax_request():
    return (
        request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )


@app.route("/")
def index():
    data = get_observation_data()
    return render_template(
        "index.html",
        todo_list=data["all_todos"],
        active_subject=data["active_subject"],
        stats=data["stats"],
    )


@app.route("/counter")
def counter():
    data = get_observation_data()
    return render_template(
        "counter.html",
        active_subject=data["active_subject"],
        waiting_queue=data["waiting_queue"],
        completed_recent=data["completed_recent"][:10],
        stats=data["stats"],
    )


@app.route("/api/state")
def api_state():
    data = get_observation_data()
    return {
        "active_subject": data["active_subject"],
        "waiting_queue": data["waiting_queue"],
        "completed_recent": data["completed_recent"][:10],
        "stats": data["stats"],
    }


@app.route("/add", methods=["POST"])
def add():
    title = ""
    if request.is_json and request.json:
        title = request.json.get("title", "").strip()
    elif request.form:
        title = request.form.get("title", "").strip()

    conn = get_db_connection()
    if not title:
        count_row = conn.execute("SELECT COUNT(*) as c FROM todo").fetchone()
        next_num = (count_row["c"] if count_row else 0) + 1
        title = f"Subject #{next_num}"

    now = datetime.datetime.now()
    arrive_time = now.strftime("%H:%M:%S")
    with conn:
        cursor = conn.execute(
            "INSERT INTO todo (title, arrive_time, start_time, fin_time) VALUES (?, ?, ?, ?)",
            (title, arrive_time, "", ""),
        )
        new_id = cursor.lastrowid
    conn.close()

    if is_ajax_request():
        return {"success": True, "id": new_id, "title": title, "arrive_time": arrive_time}
    return redirect(request.referrer or url_for("counter"))


@app.route("/start/<int:todo_id>", methods=["GET", "POST"])
def start(todo_id):
    now = datetime.datetime.now()
    start_time = now.strftime("%H:%M:%S")
    conn = get_db_connection()
    with conn:
        conn.execute(
            "UPDATE todo SET start_time = ? WHERE id = ?",
            (start_time, todo_id),
        )
    conn.close()
    if is_ajax_request():
        return {"success": True, "id": todo_id, "start_time": start_time}
    return redirect(request.referrer or url_for("counter"))


@app.route("/finish/<int:todo_id>", methods=["GET", "POST"])
def finish(todo_id):
    now = datetime.datetime.now()
    fin_time = now.strftime("%H:%M:%S")
    conn = get_db_connection()
    with conn:
        conn.execute(
            "UPDATE todo SET fin_time = ? WHERE id = ?",
            (fin_time, todo_id),
        )
    conn.close()
    if is_ajax_request():
        return {"success": True, "id": todo_id, "fin_time": fin_time}
    return redirect(request.referrer or url_for("counter"))


@app.route("/finish_and_next/<int:todo_id>", methods=["GET", "POST"])
def finish_and_next(todo_id):
    now = datetime.datetime.now()
    timestamp = now.strftime("%H:%M:%S")
    conn = get_db_connection()
    next_id = None
    with conn:
        conn.execute(
            "UPDATE todo SET fin_time = ? WHERE id = ?",
            (timestamp, todo_id),
        )
        next_row = conn.execute(
            "SELECT id FROM todo WHERE (start_time IS NULL OR start_time = '') AND id != ? ORDER BY id ASC LIMIT 1",
            (todo_id,),
        ).fetchone()
        if next_row:
            next_id = next_row["id"]
            conn.execute(
                "UPDATE todo SET start_time = ? WHERE id = ?",
                (timestamp, next_id),
            )
    conn.close()
    if is_ajax_request():
        return {"success": True, "finished_id": todo_id, "next_started_id": next_id}
    return redirect(request.referrer or url_for("counter"))


@app.route("/delete/<int:todo_id>", methods=["GET", "POST"])
def delete_subject(todo_id):
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM todo WHERE id = ?", (todo_id,))
    conn.close()
    if is_ajax_request():
        return {"success": True, "deleted_id": todo_id}
    return redirect(request.referrer or url_for("counter"))



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
