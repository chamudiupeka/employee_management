from flask import Blueprint, render_template, g, redirect, url_for
from app.db import get_db
from datetime import datetime, timedelta

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    db = get_db()
    with db.cursor() as cur:
        # Get total employees
        cur.execute("SELECT COUNT(*) FROM employees")
        total_employees = cur.fetchone()[0]
        
        # Get total departments
        cur.execute("SELECT COUNT(DISTINCT department) FROM employees WHERE department IS NOT NULL AND department != ''")
        total_departments = cur.fetchone()[0]
        
        # Get employees added this month
        current_month = datetime.now().replace(day=1)
        cur.execute(
            "SELECT COUNT(*) FROM employees WHERE hire_date >= %s",
            (current_month,)
        )
        added_this_month = cur.fetchone()[0]
    
    stats = {
        'total_employees': total_employees,
        'total_departments': total_departments,
        'added_this_month': added_this_month
    }
    
    return render_template("home/index.html", stats=stats)
