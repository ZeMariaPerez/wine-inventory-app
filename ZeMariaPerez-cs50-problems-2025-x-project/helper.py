from flask import redirect, session
from functools import wraps

# Ensure a route can only be accessed if the user is in session
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

# Present numbers with 1 decimal place
def one_decimal(value):
    return f"{value:,.1f}"

# Present numbers with 2 decimal places
def two_decimals(value):
    return f"{value:,.2f}"
