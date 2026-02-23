from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = "mysecretkey"

# ---------------- DATABASE ----------------

def init_users():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def init_students():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            course TEXT
        )
    """)
    conn.commit()
    conn.close()

init_users()
init_students()

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed = generate_password_hash(password)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",
                       (username, hashed))
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")


@app.route("/add-student", methods=["GET","POST"])
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        course = request.form["course"]

        # Backend validation
        if not name or not age or not course:
            flash("All fields are required")
            return redirect(url_for("add_student"))

        if not age.isdigit():
            flash("Age must be a number")
            return redirect(url_for("add_student"))

        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO students (name, age, course) VALUES (?,?,?)",
                (name, age, course)
            )
            conn.commit()
            conn.close()

            flash("Student added successfully")

        except Exception as e:
            flash("Something went wrong while adding student")

        return redirect(url_for("view_students"))

    return render_template("add_student.html")


@app.route("/view-students")
def view_students():
    search = request.args.get("search")
    page = request.args.get("page", 1, type=int)
    limit = 5
    offset = (page - 1) * limit

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if search:
        cursor.execute(
            "SELECT * FROM students WHERE name LIKE ? LIMIT ? OFFSET ?",
            ('%' + search + '%', limit, offset)
        )
    else:
        cursor.execute(
            "SELECT * FROM students LIMIT ? OFFSET ?",
            (limit, offset)
        )

    students = cursor.fetchall()
    conn.close()

    return render_template(
        "view_students.html",
        students=students,
        page=page
    )
@app.route("/delete/<int:id>")
def delete_student(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("Student deleted successfully")
    return redirect(url_for("view_students"))
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)