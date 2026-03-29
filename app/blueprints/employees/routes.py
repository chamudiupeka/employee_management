from flask import Blueprint, flash, redirect, render_template, request, url_for
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime

from app.db import get_db
from app.blueprints.auth.routes import login_required

employees_bp = Blueprint("employees", __name__)


def validate_email_format(email):
    """Validate email format using regex"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None


def validate_phone_format(phone):
    """Validate phone format - allows various formats"""
    if not phone or phone.strip() == "":
        return True  # Phone is optional
    
    # Remove spaces, dashes, parentheses, and plus signs for validation
    cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if remaining characters are digits and length is reasonable
    return cleaned_phone.isdigit() and 7 <= len(cleaned_phone) <= 15


def validate_salary(salary):
    """Validate salary format - must be a valid decimal number"""
    if not salary or salary.strip() == "":
        return True, None  # Salary is optional
    
    try:
        salary_decimal = Decimal(salary)
        if salary_decimal < 0:
            return False, "Salary cannot be negative"
        if salary_decimal > 9999999.99:  # Based on NUMERIC(10,2) constraint
            return False, "Salary exceeds maximum allowed value"
        return True, salary_decimal
    except InvalidOperation:
        return False, "Invalid salary format"


def validate_date(date_str):
    """Validate date format"""
    if not date_str or date_str.strip() == "":
        return True  # Date is optional
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def check_email_exists(email, employee_id=None):
    """Check if email already exists in database (excluding current employee for edit)"""
    db = get_db()
    with db.cursor() as cur:
        if employee_id:  # For edit operation
            cur.execute(
                "SELECT id FROM employees WHERE email = %s AND id != %s",
                (email, employee_id)
            )
        else:  # For create operation
            cur.execute(
                "SELECT id FROM employees WHERE email = %s",
                (email,)
            )
        return cur.fetchone() is not None


def validate_employee_data(form_data, employee_id=None):
    """Validate all employee form data - returns field-specific errors"""
    field_errors = {}
    
    # Required field validation
    first_name = form_data.get('first_name', '').strip()
    last_name = form_data.get('last_name', '').strip()
    email = form_data.get('email', '').strip()
    
    if not first_name:
        field_errors['first_name'] = "First name is required"
    elif len(first_name) > 100:
        field_errors['first_name'] = "First name must not exceed 100 characters"
        
    if not last_name:
        field_errors['last_name'] = "Last name is required"
    elif len(last_name) > 100:
        field_errors['last_name'] = "Last name must not exceed 100 characters"
        
    if not email:
        field_errors['email'] = "Email is required"
    else:
        if len(email) > 150:
            field_errors['email'] = "Email must not exceed 150 characters"
        elif not validate_email_format(email):
            field_errors['email'] = "Please enter a valid email address"
        elif check_email_exists(email, employee_id):
            field_errors['email'] = "This email address is already in use"
    
    # Optional field validation
    phone = form_data.get('phone', '').strip()
    if phone and not validate_phone_format(phone):
        field_errors['phone'] = "Please enter a valid phone number format"
    
    department = form_data.get('department', '').strip()
    if department and len(department) > 100:
        field_errors['department'] = "Department must not exceed 100 characters"
        
    position = form_data.get('position', '').strip()
    if position and len(position) > 100:
        field_errors['position'] = "Position must not exceed 100 characters"
    
    salary = form_data.get('salary', '').strip()
    salary_valid, salary_error = validate_salary(salary)
    if not salary_valid:
        field_errors['salary'] = salary_error
    
    hire_date = form_data.get('hire_date', '').strip()
    if hire_date and not validate_date(hire_date):
        field_errors['hire_date'] = "Please enter a valid date"
    
    return field_errors


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
        # Validate form data
        field_errors = validate_employee_data(request.form)
        
        if field_errors:
            return render_template("employees/form.html", form_data=request.form, field_errors=field_errors)
        
        # Extract and clean form data
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip() or None
        department = request.form["department"].strip() or None
        position = request.form["position"].strip() or None
        salary_str = request.form["salary"].strip()
        hire_date_str = request.form["hire_date"].strip() or None
        
        # Convert salary to decimal if provided
        salary = None
        if salary_str:
            salary = Decimal(salary_str)

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO employees
                    (first_name, last_name, email, phone, department, position, salary, hire_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (first_name, last_name, email, phone, department, position, salary, hire_date_str),
                )
            db.commit()
            flash(f"Employee {first_name} {last_name} created successfully!", "success")
            return redirect(url_for("employees.list_employees"))
        except Exception as e:
            db.rollback()
            flash(f"Error creating employee: {str(e)}", "error")
            return render_template("employees/form.html", form_data=request.form)

    return render_template("employees/form.html")


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
        # Validate form data (including email uniqueness check for edit)
        field_errors = validate_employee_data(request.form, employee_id)
        
        if field_errors:
            # Get current employee data for the form
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
            return render_template("employees/form.html", employee=employee, form_data=request.form, field_errors=field_errors)
        
        # Extract and clean form data
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip() or None
        department = request.form["department"].strip() or None
        position = request.form["position"].strip() or None
        salary_str = request.form["salary"].strip()
        hire_date_str = request.form["hire_date"].strip() or None
        
        # Convert salary to decimal if provided
        salary = None
        if salary_str:
            salary = Decimal(salary_str)

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
                    (first_name, last_name, email, phone, department, position, salary, hire_date_str, employee_id),
                )
            db.commit()
            flash(f"Employee {first_name} {last_name} updated successfully!", "success")
            return redirect(url_for("employees.employee_detail", employee_id=employee_id))
        except Exception as e:
            db.rollback()
            flash(f"Error updating employee: {str(e)}", "error")

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

    return render_template("employees/form.html", employee=employee)


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
