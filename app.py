from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = "smartfix.db"


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

    conn.execute("""
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

    conn.commit()
    conn.close()

    return redirect(url_for("success"))


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/admin")
def admin():

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


@app.route("/status/<int:complaint_id>/<new_status>", methods=["POST"])
def update_status(complaint_id, new_status):

    allowed_statuses = ["Pending", "In Progress", "Resolved"]

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
def resolve(complaint_id):

    conn = get_db()

    conn.execute("""
        UPDATE complaints
        SET status = 'Resolved'
        WHERE id = ?
    """, (complaint_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)