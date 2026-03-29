from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.db import get_db
from app.blueprints.auth.routes import login_required

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("/")
@login_required
def list_employees():
    search = request.args.get("search", "").strip()
    db = get_db()

    with db.cursor() as cur:
        if search:
            cur.execute(
                """
                SELECT id, first_name, last_name, email, department, position
                FROM employees
                WHERE first_name ILIKE %s
                   OR last_name ILIKE %s
                   OR email ILIKE %s
                   OR department ILIKE %s
                   OR position ILIKE %s
                ORDER BY id DESC
                """,
                (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"),
            )
        else:
            cur.execute(
                """
                SELECT id, first_name, last_name, email, department, position
                FROM employees
                ORDER BY id DESC
                """
            )

        employees = cur.fetchall()

    return render_template("employees/list.html", employees=employees, search=search)


@employees_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_employee():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        department = request.form["department"]
        position = request.form["position"]
        salary = request.form["salary"]
        hire_date = request.form["hire_date"]

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO employees
                    (first_name, last_name, email, phone, department, position, salary, hire_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (first_name, last_name, email, phone, department, position, salary, hire_date),
                )
            db.commit()
            flash("Employee created successfully!", "success")
            return redirect(url_for("employees.list_employees"))
        except Exception as e:
            db.rollback()
            flash(f"Error creating employee: {e}", "error")

    return render_template("employees/create.html")


@login_required
@employees_bp.route("/<int:employee_id>")
def employee_detail(employee_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT id, first_name, last_name, email, phone, department, position, salary, hire_date
            FROM employees
            WHERE id = %s
            """,
            (employee_id,),
        )
        employee = cur.fetchone()

    if not employee:
        flash("Employee not found.", "error")
        return redirect(url_for("employees.list_employees"))

    return render_template("employees/detail.html", employee=employee)


@login_required
@employees_bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
def edit_employee(employee_id):
    db = get_db()

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        department = request.form["department"]
        position = request.form["position"]
        salary = request.form["salary"]
        hire_date = request.form["hire_date"]

        try:
            with db.cursor() as cur:
                cur.execute(
                    """
                    UPDATE employees
                    SET first_name = %s,
                        last_name = %s,
                        email = %s,
                        phone = %s,
                        department = %s,
                        position = %s,
                        salary = %s,
                        hire_date = %s
                    WHERE id = %s
                    """,
                    (first_name, last_name, email, phone, department, position, salary, hire_date, employee_id),
                )
            db.commit()
            flash("Employee updated successfully!", "success")
            return redirect(url_for("employees.employee_detail", employee_id=employee_id))
        except Exception as e:
            db.rollback()
            flash(f"Error updating employee: {e}", "error")

    with db.cursor() as cur:
        cur.execute(
            """
            SELECT id, first_name, last_name, email, phone, department, position, salary, hire_date
            FROM employees
            WHERE id = %s
            """,
            (employee_id,),
        )
        employee = cur.fetchone()

    if not employee:
        flash("Employee not found.", "error")
        return redirect(url_for("employees.list_employees"))

    return render_template("employees/edit.html", employee=employee)


@employees_bp.route("/<int:employee_id>/delete", methods=["POST"])
@login_required
def delete_employee(employee_id):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        db.commit()
        flash("Employee deleted successfully!", "success")
    except Exception as e:
        db.rollback()
        flash(f"Error deleting employee: {e}", "error")

    return redirect(url_for("employees.list_employees"))
