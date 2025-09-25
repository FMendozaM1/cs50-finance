import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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
    """Show portfolio of stocks"""
# obtener stocks
    stocks = db.execute("SELECT * FROM stocks WHERE users_id = ?", session["user_id"])
    current_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cash = current_cash[0]["cash"]
    networth = 0

    for stock in stocks:
        current_stock = lookup(stock["symbol"])
        stock["price"] = current_stock["price"]
        stock["total_value"] = int(stock["shares"]) * stock["price"]
        networth = networth + stock["total_value"]

    networth = networth + cash
    return render_template("index.html", stocks=stocks, cash=cash, networth=networth)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # Ensure no errors were commited
        stock = lookup(request.form.get("symbol"))

        if not request.form.get("symbol"):
            return apology("Must provide Symbol", 400)

        # Validar que sea un número entero positivo
        shares_str = request.form.get("shares")
        if not shares_str or not shares_str.isdigit():
            return apology("Shares must be a positive integer", 400)

        shares = int(shares_str)
        if shares <= 0:
            return apology("Shares must be greater than zero", 400)
        if stock is None:
            return apology("Stock not found", 400)

    # buy if there's enough cash
        current_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        total_cost = stock["price"] * shares
        if total_cost > current_cash[0]["cash"]:
            return apology("Not enough cash", 400)

    # check if the user already has the stock
        existing = db.execute("SELECT shares FROM stocks WHERE users_id = ? AND symbol = ?",
                              session["user_id"], stock["symbol"])
        if existing:
            new_total = existing[0]["shares"] + shares
            db.execute("UPDATE stocks SET shares = ?, price = ? WHERE users_id = ? AND symbol = ?",
                       new_total, stock["price"], session["user_id"], stock["symbol"])
        else:
            buy = db.execute("INSERT INTO stocks (name, symbol, price, shares, users_id) VALUES (?,?,?,?,?)",
                             stock["name"], stock["symbol"], stock["price"], shares, session["user_id"])

    # update cash
        updated_cash = current_cash[0]["cash"] - total_cost
        update = db.execute("UPDATE users SET cash = ? WHERE id = ?",
                            updated_cash, session["user_id"])

    # update history
        db.execute("INSERT INTO history (users_id, name, symbol, price, shares, type) VALUES (?,?,?,?,?,?)",
                   session["user_id"], stock["name"], stock["symbol"], stock["price"], shares, "bought")

    # display succes message
        flash("Purchase succesful")
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT * FROM history WHERE users_id = ?", session["user_id"])
    return render_template("history.html", history=history)


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
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
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
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        stock = lookup(request.form.get("symbol"))

        if stock is None:
            return apology("Stock not found", 400)
        return render_template("quote.html", stock=stock)
    else:
        return render_template("quote.html", stock=None)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username doesn't exist already
        if len(rows) != 0:
            return apology("Username already exists", 400)

        # Registers the user
        hashed_password = generate_password_hash(request.form.get("password"))
        new_user = db.execute("INSERT INTO users (username, hash) VALUES (?,?)",
                              request.form.get("username"), hashed_password)

        # Redirect user to login
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    stocks = db.execute("SELECT * FROM stocks WHERE users_id = ?", session["user_id"])
    current_shares = int(stocks[0]["shares"])
    if request.method == "POST":

        # Check for errors
        if not request.form.get("symbol"):
            return apology("Must provide Symbol", 403)
        if int(request.form.get("shares")) < 0 or int(request.form.get("shares")) > current_shares:
            return apology("Must provide a valid number of shares")

    # check if the user has the stock
        user_stock = db.execute("SELECT shares FROM stocks WHERE users_id = ? AND symbol = ?",
                                session["user_id"], request.form.get("symbol"))
        if len(user_stock) != 1:
            return apology("You don't own that stock")

    # Sell the stock
        current_stock = lookup(request.form.get("symbol"))
        total_cost = current_stock["price"] * int(request.form.get("shares"))
        remaining_shares = user_stock[0]["shares"] - int(request.form.get("shares"))
        if remaining_shares > 0:
            sell = db.execute(" UPDATE stocks SET shares = ? WHERE users_id = ? AND symbol = ?",
                              remaining_shares, session["user_id"], request.form.get("symbol"))
        else:
            sell_and_delete = db.execute(
                "DELETE FROM stocks WHERE users_id = ? AND symbol = ?", session["user_id"], request.form.get("symbol"))
    # Update cash
        current_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        updated_cash = current_cash[0]["cash"] + total_cost
        update = db.execute("UPDATE users SET cash = ? WHERE id = ?",
                            updated_cash, session["user_id"])
    # update history
        db.execute("INSERT INTO history (users_id, name, symbol, price, shares, type) VALUES (?,?,?,?,?,?)",
                   session["user_id"], current_stock["name"], current_stock["symbol"], current_stock["price"], int(request.form.get("shares")), "sold")

    # display succes message
        flash("Sell was succesful")
        return redirect("/")
    else:
        return render_template("sell.html", stocks=stocks)


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        # Ensure old password was submitted
        if not request.form.get("current_password"):
            return apology("must provide current password", 403)

        # Ensure password was submitted
        elif not request.form.get("new_password"):
            return apology("must provide password", 403)

        # Ensure passwords match
        elif request.form.get("new_password") != request.form.get("confirm_password"):
            return apology("passwords don't match", 403)

        # Ensure password is correct
        rows = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"]
        )
        stored_hash = rows[0]["hash"]
        if not check_password_hash(stored_hash, request.form.get("current_password")):
            return apology("current password is incorrect", 403)

        # Change password
        hashed_new_password = generate_password_hash(request.form.get("confirm_password"))
        change_password = db.execute("UPDATE users SET hash = ? WHERE id = ? ",
                                     hashed_new_password, session["user_id"])

        # Redirect user to index and display success message
        flash("Password was succesfully changed")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change-password.html")
