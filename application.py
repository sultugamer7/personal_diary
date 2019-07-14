import os
import time
import re

from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///diary.db")


@app.route("/")
@login_required
def index():
    """Show home page"""

    # View diary pages
    pages = db.execute("SELECT id, page, date, time, bookmarked from diaries WHERE user_id = :user_id ORDER BY id desc", user_id=session["user_id"])
    page_data = []

    if pages:
        for page in pages:
            date1 = datetime.strptime(page["date"], "%Y-%m-%d")
            date2 = date1.strftime("%B %d, %Y")
            data = {'id':page["id"], 'page':page["page"], 'date': date2, 'time': page["time"], 'bookmarked': page["bookmarked"]}
            page_data.append(data)

    return render_template("home.html", pages=page_data)


@app.route("/tear", methods=["POST"])
@login_required
def tear():
    """Tear home page"""

    # Get id of the page to be torn (deleted)
    page_id = request.form.get("id")
    db.execute("DELETE FROM diaries WHERE id = :page_id", page_id=page_id)

    return redirect(request.form.get("url"))


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    """Delete account"""

    # Ensure password was submitted
    if not request.form.get("password"):
        return apology("must provide password", 403)

    # Query database for password
    rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

    # Ensure password is correct
    if not check_password_hash(rows[0]["password"], request.form.get("password")):
        return apology("invalid password", 403)

    # Delete diary pages from database
    db.execute("DELETE FROM diaries WHERE user_id = :user_id", user_id=session["user_id"])

    # Delete user from database
    db.execute("DELETE FROM users WHERE id = :user_id", user_id=session["user_id"])

    # Forget any user_id
    session.clear()

    # Redirect user to login page
    return redirect("/")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    if len(request.args.get("username")) > 1:
        flag = db.execute("SELECT * FROM users WHERE username = :user", user=request.args.get("username"))
        if not flag:
            return jsonify(True), 200
        else:
            return jsonify(False), 200

    else:
        return apology("Username should be of length > 0")


@app.route("/write", methods=["GET", "POST"])
@login_required
def write():
    """Write a page in diary"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure page was submitted
        if not request.form.get("page"):
            return apology("must write in page", 403)

        # Add new page in diary in database
        new_page = db.execute("INSERT INTO diaries(user_id, page, time) VALUES(:user_id, :page, :time)",
                              user_id=session["user_id"],
                              page=request.form.get("page"),
                              time=request.form.get("time"))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Getting today's date to compare
        date = time.strftime("%Y-%m-%d")

        # Getting rows having today's date
        rows = db.execute("SELECT date FROM diaries WHERE user_id = :user_id AND date = :date",
                          user_id=session["user_id"],
                          date=date)

        # Ensure page is already not written for today's date
        if rows:
            return apology("you've already written for today", 400)

        # Get today's day in English format
        day = time.strftime("%A")

        # Get today's date
        date = time.strftime("%B %d, %Y")

        # Get current time
        current_time = time.strftime("%I %p")

        # Render write page
        return render_template("write.html", day=day, date=date, time=current_time)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Display username and change password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure if current password was submitted
        if not request.form.get("current"):
            return apology("must provide current password", 403)

        # Ensure if current password is correct
        row = db.execute("SELECT password FROM users WHERE id = :user_id", user_id=session["user_id"])
        if not check_password_hash(row[0]["password"], request.form.get("current")):
            return apology("must provide correct current password", 403)

        # Ensure if new password was submitted
        elif not request.form.get("new"):
            return apology("must provide new password", 403)

        # Ensure if new password is different than current password
        elif request.form.get("current") == request.form.get("new"):
            return apology("must provide password different than current password", 403)

        # Ensure if new password was confirmed
        elif not request.form.get("new") == request.form.get("confirm"):
            return apology("must confirm password", 403)

        # Hash the password
        hash = generate_password_hash(request.form.get("new"))

        # Query to change password
        db.execute("UPDATE users SET password = :password WHERE id = :user_id",
                    password=hash,
                    user_id=session["user_id"])

        # Redirect to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Get username of logged in user from database
        row = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])
        username = row[0]["username"]

        # Render profile page
        return render_template("profile.html", username=username)


@app.route("/bookmark", methods=["GET"])
@login_required
def bookmark():
    """Display bookmarked pages"""

    # View bookmarked pages
    pages = db.execute("SELECT id, page, date, time from diaries WHERE user_id = :user_id AND bookmarked = :bookmarked ORDER BY id desc",
                       user_id=session["user_id"],
                       bookmarked=1)
    page_data = []

    if pages:
        for page in pages:
            date1 = datetime.strptime(page["date"], "%Y-%m-%d")
            date2 = date1.strftime("%B %d, %Y")
            data = {'id':page["id"], 'page':page["page"], 'date': date2, 'time': page["time"]}
            page_data.append(data)

    return render_template("bookmark.html", pages=page_data)


@app.route("/remove_bookmark", methods=["POST"])
@login_required
def remove_bookmark():
    """Remove bookmarked pages"""

    # Remove bookmarked page
    db.execute("UPDATE diaries SET bookmarked = :bookmarked WHERE id = :page_id",
                   page_id=request.form.get("id"),
                   bookmarked=0)

    return redirect(request.form.get("url"))


@app.route("/add_bookmark", methods=["POST"])
@login_required
def add_bookmark():
    """Add bookmark"""

    # Add bookmark
    db.execute("UPDATE diaries SET bookmarked = :bookmarked WHERE id = :page_id",
               page_id=request.form.get("id"),
               bookmarked=1)

    return redirect(request.form.get("url"))


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 400)

        # Ensure email is valid
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", request.form.get("email")):
            return apology("must provide a valid email", 400)

        # Ensure username was submitted
        elif not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password was confirmed correctly
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("password must match", 400)

        # Ensure username's length > 3
        elif not len(request.form.get("username")) > 3:
            return apology("username must be at least 4 characters long", 400)

        # Ensure password's length > 7
        elif not len(request.form.get("password")) > 7:
            return apology("password must be at least 8 characters long", 400)

        # Hash the password
        hash = generate_password_hash(request.form.get("password"))

        # Register user in database
        new_user = db.execute("INSERT INTO users(email, username, password) VALUES(:email, :username, :password)",
                              email=request.form.get("email"),
                              username=request.form.get("username"),
                              password=hash)

        # Ensure username is not already taken
        if not new_user:
            return apology("username/email already exists", 400)

        # Remember the logged in user
        session["user_id"] = new_user

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)