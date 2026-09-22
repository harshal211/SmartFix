from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

DATABASE = "smartfix.db"

# Secret key for login session
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Medium',
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():

    category = request.form.get("category")
    location = request.form.get("location")
    description = request.form.get("description")

    # Automatic priority
    if category in ["Water Leakage", "Electrical"]:
        priority = "High"
    elif category in ["Internet", "Furniture"]:
        priority = "Medium"
    else:
        priority = "Low"

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO complaints
        (category, location, description, priority, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        category,
        location,
        description,
        priority,
        "Pending"
    ))

    complaint_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return render_template(
        "success.html",
        complaint_id=complaint_id
    )


@app.route("/success")
def success():
    return render_template("success.html")



@app.route("/track", methods=["GET", "POST"])
def track():

    complaint = None
    error = None

    if request.method == "POST":

        complaint_id = request.form.get("complaint_id")

        if complaint_id and complaint_id.isdigit():

            conn = get_db()

            complaint = conn.execute("""
                SELECT * FROM complaints
                WHERE id = ?
            """, (complaint_id,)).fetchone()

            conn.close()

            if complaint is None:
                error = "Complaint not found. Please check your Complaint ID."

        else:
            error = "Please enter a valid Complaint ID."

    return render_template(
        "track.html",
        complaint=complaint,
        error=error
    )


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        admin_username = os.environ.get(
            "ADMIN_USERNAME",
            "admin"
        )

        admin_password = os.environ.get(
            "ADMIN_PASSWORD",
            "admin123"
        )

        if username == admin_username and password == admin_password:

            session["admin_logged_in"] = True

            return redirect(url_for("admin"))

        return render_template(
            "admin_login.html",
            error="Invalid username or password"
        )

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("admin_login"))


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db()

    complaints = conn.execute("""
        SELECT * FROM complaints
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        complaints=complaints
    )


# =========================
# UPDATE STATUS
# =========================

@app.route(
    "/status/<int:complaint_id>/<new_status>",
    methods=["POST"]
)
def update_status(complaint_id, new_status):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]

    if new_status not in allowed_statuses:
        return redirect(url_for("admin"))

    conn = get_db()

    conn.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ?
    """, (new_status, complaint_id))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


init_db()


if __name__ == "__main__":
    app.run(debug=True)
