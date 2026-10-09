from flask import Flask, render_template, request, redirect, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Session secret key
app.secret_key = "hospital_secret_key"


# ---------------- DATABASE CONNECTION ----------------

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="hospitaldb"
    )


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # Hash password
        hashed_password = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users (username, password)
                VALUES (%s, %s)
                """,
                (username, hashed_password)
            )

            db.commit()

        except mysql.connector.Error:
            db.close()
            return "Username already exists"

        db.close()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )

        user = cursor.fetchone()

        db.close()

        if user and check_password_hash(user[2], password):

            session["user_id"] = user[0]
            session["username"] = user[1]

            return redirect("/")

        return "Invalid username or password"

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM patients")
    patient_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments")
    appointment_count = cursor.fetchone()[0]

    db.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        patient_count=patient_count,
        appointment_count=appointment_count
    )


# ---------------- ADD PATIENT ----------------

@app.route("/add_patient", methods=["GET", "POST"])
def add_patient():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        disease = request.form["disease"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO patients
            (name, age, gender, phone, disease)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, age, gender, phone, disease)
        )

        db.commit()
        db.close()

        return redirect("/patients")

    return render_template("add_patient.html")


# ---------------- VIEW / SEARCH PATIENTS ----------------

@app.route("/patients")
def patients():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "")

    db = get_db()
    cursor = db.cursor()

    if search:

        cursor.execute(
            """
            SELECT * FROM patients
            WHERE name LIKE %s
            OR phone LIKE %s
            OR disease LIKE %s
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        )

    else:

        cursor.execute("SELECT * FROM patients")

    patients = cursor.fetchall()

    db.close()

    return render_template(
        "patients.html",
        patients=patients
    )


# ---------------- EDIT PATIENT ----------------

@app.route("/edit_patient/<int:id>", methods=["GET", "POST"])
def edit_patient(id):

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":

        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        disease = request.form["disease"]

        cursor.execute(
            """
            UPDATE patients
            SET name=%s,
                age=%s,
                gender=%s,
                phone=%s,
                disease=%s
            WHERE id=%s
            """,
            (name, age, gender, phone, disease, id)
        )

        db.commit()
        db.close()

        return redirect("/patients")

    cursor.execute(
        "SELECT * FROM patients WHERE id=%s",
        (id,)
    )

    patient = cursor.fetchone()

    db.close()

    return render_template(
        "edit_patient.html",
        patient=patient
    )


# ---------------- DELETE PATIENT ----------------

@app.route("/delete_patient/<int:id>")
def delete_patient(id):

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM appointments WHERE patient_id=%s",
        (id,)
    )

    cursor.execute(
        "DELETE FROM patients WHERE id=%s",
        (id,)
    )

    db.commit()
    db.close()

    return redirect("/patients")


# ---------------- APPOINTMENT ----------------

@app.route("/appointment", methods=["GET", "POST"])
def appointment():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        doctor = request.form["doctor"]
        date = request.form["date"]
        time = request.form["time"]

        cursor.execute(
            """
            INSERT INTO appointments
            (patient_id, doctor, date, time)
            VALUES (%s, %s, %s, %s)
            """,
            (patient_id, doctor, date, time)
        )

        db.commit()

        db.close()

        return redirect("/")

    cursor.execute(
        "SELECT id, name FROM patients"
    )

    patients = cursor.fetchall()

    db.close()

    return render_template(
        "appointment.html",
        patients=patients
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)