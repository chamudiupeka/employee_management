from flask import Blueprint, render_template, g, redirect, url_for

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    if g.user:
        return redirect(url_for("employees.list_employees"))
    return render_template("home/index.html")
