from flask import Flask, app, request, render_template, session, redirect
from flask_session import Session
from helpers import login_required, apology
from werkzeug.security import check_password_hash, generate_password_hash
from sql import SQL
from datetime import datetime, date
import itertools

app = Flask(__name__)
app.debug = True

db = SQL("sqlite:///connect.db")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    id = session["user_id"]
    students = db.execute("SELECT * FROM students WHERE parent_id = ?", id)
    ages = []
    today = date.today()
    for student in students:
        birth = datetime.strptime(student["birth"], "%Y-%m-%d").date()
        ages.append(round((today - birth).days / 365, 3))

    return render_template("index.html", stuff=zip(students, ages))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get(
                "username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["pass"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")

        if not confirm or not password or not username:
            return apology("An input field was left blank!")
        if not confirm == password:
            return apology("Sorry! The passwords don't match.", 400)

        try:
            db.execute("INSERT INTO users (username, pass) VALUES (?, ?)",
                       username, generate_password_hash(password))
        except ValueError:
            return apology("The Username was already taken!", 400)

        return redirect("/")


@app.route("/reset-password", methods=["GET", "POST"])
@login_required
def reset_password():
    """Reset password"""
    if request.method == "GET":
        return render_template("reset-password.html")

    else:
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")

        # Ensure old-password was submitted
        if not old_password:
            return apology("must provide old password", 403)

        # Ensure new-password was submitted
        elif not new_password:
            return apology("must provide new password", 403)

        # Query database for old-password
        rows = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"]
        )

        # Ensure old-password is correct
        if not check_password_hash(rows[0]["pass"], old_password):
            return apology("invalid old password", 403)

        db.execute("UPDATE users SET pass = ? WHERE id = ?",
                   generate_password_hash(new_password), session["user_id"])

        return redirect("/")


@app.route("/children", methods=["GET"])
@login_required
def children():
    """Show children"""
    id = session["user_id"]
    students = db.execute("SELECT * FROM students WHERE parent_id = ?", id)
    ages = []
    today = date.today()
    for student in students:
        birth = datetime.strptime(student["birth"], "%Y-%m-%d").date()
        ages.append(round((today - birth).days / 365, 3))

    return render_template("children.html", children=zip(students, ages))


if __name__ == "__main__":
    app.run(debug=True)
