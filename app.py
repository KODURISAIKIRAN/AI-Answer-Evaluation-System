from flask import Flask, render_template, request, send_from_directory, send_file, redirect, session
from reportlab.pdfgen import canvas
from flask_mail import Mail, Message
import random
from reportlab.platypus import Table
from reportlab.platypus import TableStyle

import uuid
from reportlab.lib import colors
import os
import fitz
import re
import time
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from zoneinfo import ZoneInfo
from paddleocr import PaddleOCR
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "ai_evaluation_secret_key"
)
# =========================
# Email Configuration
# =========================

app.config["MAIL_SERVER"] = "smtp.gmail.com"

app.config["MAIL_PORT"] = 587

app.config["MAIL_USE_TLS"] = True


app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")


mail = Mail(app)
report_data = {}
UPLOAD_FOLDER = "uploads"
def delete_old_files():

    expiry_time = 30 * 60      # 30 minutes

    current_time = time.time()

    for file in os.listdir(UPLOAD_FOLDER):

        file_path = os.path.join(
            UPLOAD_FOLDER,
            file
        )

        if os.path.isfile(file_path):

            file_age = current_time - os.path.getmtime(file_path)

            if file_age > expiry_time:

                try:

                    os.remove(file_path)

                    print(f"Deleted: {file}")

                except Exception as e:

                    print(e)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

print("Loading OCR...")

ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en"
)

print("OCR Ready!")

print("Loading Similarity Model...")

similarity_model = SentenceTransformer(
    "all-mpnet-base-v2"
)

print("Similarity Model Ready!")
conn = sqlite3.connect(
    "evaluation.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS history(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_name TEXT,

    roll_number TEXT,

    subject_name TEXT,

    marks INTEGER,

    percentage REAL,

    feedback TEXT,

    evaluation_time TEXT

)

""")

conn.commit()

cursor.execute("""

CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT,

    email TEXT UNIQUE,

    password TEXT,

    role TEXT,

    roll_number TEXT

)

""")

conn.commit()

conn.close()
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        roll_number = request.form.get(
            "roll_number"
        )

        password = request.form["password"]

        role = request.form["role"]
        


        # =========================
        # Password Strength Check
        # =========================

        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'


        if not re.match(pattern, password):

            return render_template(

                "register.html",

                error="Password must contain 8 characters, uppercase, lowercase, number and special character"

            )


        conn = sqlite3.connect(

            "evaluation.db"

        )


        cursor = conn.cursor()


        # =========================
        # Existing Email Check
        # =========================

        cursor.execute(

            "SELECT * FROM users WHERE email=?",

            (email,)

        )


        existing_user = cursor.fetchone()


        if existing_user:


            conn.close()


            return render_template(

                "register.html",

                error="Account already exists with this email. Please login."

            )


        # =========================
        # Create Account
        # =========================

        hashed_password = generate_password_hash(

            password

        )


        cursor.execute(

            """

            INSERT INTO users(

                name,

                email,

                password,

                role,

                roll_number

            )

            VALUES(?,?,?,?,?)

            """,

            (

                name,

                email,

                hashed_password,

                role,

                roll_number

            )

        )


        conn.commit()


        conn.close()


        return redirect(

            "/login"

        )


    return render_template(

        "register.html"

    )
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method=="POST":

        email=request.form["email"]

        password=request.form["password"]

        conn=sqlite3.connect(
            "evaluation.db"
        )

        cursor=conn.cursor()

        cursor.execute(

            "SELECT * FROM users WHERE email=?",

            (email,)

        )

        user=cursor.fetchone()

        conn.close()


        if user and check_password_hash(
            user[3],
            password
        ):

            session["user"] = user[1]

            session["email"] = user[2]

            session["role"] = user[4].lower()

            session["roll_number"] = user[5]

            if session["role"] == "faculty":

                return redirect(
                    "/faculty_dashboard"
                )

            else:

                return redirect(
                    "/student_dashboard"
                )


        return "Invalid Login Details"


    return render_template(
        "login.html"
    )
@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        "/login"
    )
@app.route("/faculty_dashboard")
def faculty_dashboard():

    if "user" not in session:

        return redirect("/login")


    if session.get("role") != "faculty":

        return "Access Denied"


    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()


    # Total Evaluations

    cursor.execute(
        "SELECT COUNT(*) FROM history"
    )


    total_evaluations = cursor.fetchone()[0]



    # Total Students

    cursor.execute(

        """

        SELECT COUNT(DISTINCT roll_number)

        FROM history

        """

    )


    total_students = cursor.fetchone()[0]



    # Average Score

    cursor.execute(

        """

        SELECT AVG(percentage)

        FROM history

        """

    )


    avg = cursor.fetchone()[0]


    if avg:

        average_score = round(
            avg,
            2
        )

    else:

        average_score = 0




    # Reports generated
    # same as evaluations

    reports_generated = total_evaluations
    # Recent Evaluations

    cursor.execute(

        """

        SELECT *

        FROM history

        ORDER BY id DESC

        LIMIT 5

        """

    )


    recent = cursor.fetchall()




    conn.close()



    return render_template(

        "faculty_dashboard.html",

        username=session["user"],

        total_students=total_students,

        total_evaluations=total_evaluations,

        reports_generated=reports_generated,

        average_score=average_score,
        
        recent=recent

    )
@app.route("/faculty_profile")
def faculty_profile():

    if "user" not in session:

        return redirect("/login")


    conn = sqlite3.connect(
        "evaluation.db"
    )

    cursor = conn.cursor()


    cursor.execute(

        "SELECT COUNT(*) FROM history"

    )


    total = cursor.fetchone()[0]


    conn.close()


    return render_template(

        "faculty_profile.html",

        name=session["user"],

        email=session["email"],

        role=session["role"],

        total=total

    )



@app.route("/student_records")
def student_records():

    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "faculty":

        return "Access Denied"


    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()


    cursor.execute(

        """

        SELECT 

        roll_number,

        student_name,

        COUNT(*),

        ROUND(AVG(percentage),2)

        FROM history

        GROUP BY roll_number

        """

    )


    students = cursor.fetchall()


    conn.close()


    return render_template(

        "student_records.html",

        students=students

    )



@app.route("/reports")
def reports():

    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "faculty":

        return "Access Denied"


    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()


    cursor.execute(

        """

        SELECT *

        FROM history

        ORDER BY id DESC

        """

    )


    reports = cursor.fetchall()


    conn.close()


    return render_template(

        "reports.html",

        reports=reports

    )



@app.route("/analytics")
def analytics():

    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "faculty":

        return "Access Denied"


    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()


    cursor.execute(

        "SELECT COUNT(*) FROM history"

    )

    total = cursor.fetchone()[0]



    cursor.execute(

        "SELECT AVG(percentage) FROM history"

    )

    avg = cursor.fetchone()[0]


    if avg:

        avg = round(avg,2)

    else:

        avg = 0



    cursor.execute(

        """

        SELECT COUNT(*)

        FROM history

        WHERE feedback='Excellent'

        """

    )

    excellent = cursor.fetchone()[0]



    cursor.execute(

        """

        SELECT COUNT(*)

        FROM history

        WHERE feedback='Needs Improvement'

        """

    )

    weak = cursor.fetchone()[0]



    cursor.execute(

        """

        SELECT feedback, COUNT(*)

        FROM history

        GROUP BY feedback

        """

    )


    feedback_data = cursor.fetchall()



    conn.close()


    return render_template(

        "analytics.html",

        total=total,

        avg=avg,

        excellent=excellent,

        weak=weak,

        feedback_data=feedback_data

    )



@app.route("/ai_insights")
def ai_insights():

    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "faculty":

        return "Access Denied"


    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()


    # Top performer

    cursor.execute(

        """

        SELECT student_name, percentage

        FROM history

        ORDER BY percentage DESC

        LIMIT 1

        """

    )


    topper = cursor.fetchone()



    # Average score

    cursor.execute(

        "SELECT AVG(percentage) FROM history"

    )


    average = cursor.fetchone()[0]


    if average:

        average = round(
            average,
            2
        )

    else:

        average = 0



    # Weak students

    cursor.execute(

        """

        SELECT COUNT(*)

        FROM history

        WHERE percentage < 40

        """

    )


    weak_students = cursor.fetchone()[0]



    conn.close()



    # AI Suggestion Logic

    if average >= 80:

        suggestion = "Excellent overall performance. Students have strong understanding."

    elif average >= 60:

        suggestion = "Good performance. More practice can improve accuracy."

    elif average >= 40:

        suggestion = "Average performance. Students need revision and improvement."

    else:

        suggestion = "Additional support and practice sessions are recommended."



    return render_template(

        "ai_insights.html",

        topper=topper,

        average=average,

        weak_students=weak_students,

        suggestion=suggestion

    )


@app.route("/search_student", methods=["GET","POST"])
def search_student():

    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "faculty":

        return "Access Denied"


    records = None

    student = None


    if request.method == "POST":


        roll = request.form["roll_number"]


        conn = sqlite3.connect(
            "evaluation.db"
        )


        cursor = conn.cursor()


        cursor.execute(

            """

            SELECT *

            FROM history

            WHERE roll_number=?

            ORDER BY id DESC

            """,

            (
                roll,
            )

        )


        records = cursor.fetchall()



        cursor.execute(

            """

            SELECT 

            student_name,

            COUNT(*),

            ROUND(AVG(percentage),2)

            FROM history

            WHERE roll_number=?

            GROUP BY roll_number

            """,

            (
                roll,
            )

        )


        student = cursor.fetchone()


        conn.close()


    return render_template(

        "search_student.html",

        records=records,

        student=student

    )



@app.route("/settings", methods=["GET","POST"])
def settings():

    if "user" not in session:

        return redirect(
            "/login"
        )


    message = None


    if request.method == "POST":


        new_name = request.form["name"]


        new_password = request.form["password"]


        conn = sqlite3.connect(
            "evaluation.db"
        )


        cursor = conn.cursor()


        if new_password:


            pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'


            if not re.match(
                pattern,
                new_password
            ):


                conn.close()


                return render_template(

                    "settings.html",

                    error="Weak Password",

                    name=session["user"],

                    email=session["email"]

                )


            hashed = generate_password_hash(
                new_password
            )


            cursor.execute(

                """

                UPDATE users

                SET name=?,

                password=?

                WHERE email=?

                """,

                (
                    new_name,

                    hashed,

                    session["email"]

                )

            )


        else:


            cursor.execute(

                """

                UPDATE users

                SET name=?

                WHERE email=?

                """,

                (
                    new_name,

                    session["email"]

                )

            )



        conn.commit()


        conn.close()



        session["user"] = new_name


        message = "Profile Updated Successfully"



    return render_template(

        "settings.html",

        name=session["user"],

        email=session["email"],

        role=session["role"],

        message=message

    )



@app.route("/student_dashboard")
def student_dashboard():


    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "student":

        return "Access Denied"


    roll = session.get(
        "roll_number"
    )


    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()


    # get all student records

    cursor.execute(

        """

        SELECT *

        FROM history

        WHERE roll_number=?

        ORDER BY id DESC

        """,

        (
            roll,
        )

    )


    records = cursor.fetchall()



    # total tests

    total_tests = len(records)



    # average score

    cursor.execute(

        """

        SELECT AVG(percentage)

        FROM history

        WHERE roll_number=?

        """,

        (
            roll,
        )

    )


    avg = cursor.fetchone()[0]


    if avg:

        average = round(
            avg,
            2
        )

    else:

        average = 0



    # best score

    cursor.execute(

        """

        SELECT MAX(percentage)

        FROM history

        WHERE roll_number=?

        """,

        (
            roll,
        )

    )


    best = cursor.fetchone()[0]


    if not best:

        best = 0



    conn.close()

    # ======================
    # Performance Graph Data
    # ======================

    graph_labels = []

    graph_scores = []


    for r in records:

        graph_labels.append(

            r[7]

        )


        graph_scores.append(

            r[5]

        )

    return render_template(

        "student_dashboard.html",

        username=session["user"],

        roll_number=roll,

        total_tests=total_tests,

        average=average,

        best=best,

        records=records,

        graph_labels=graph_labels,

        graph_scores=graph_scores

    )
@app.route("/student_profile")
def student_profile():


    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "student":

        return "Access Denied"



    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()



    cursor.execute(

        """

        SELECT COUNT(*)

        FROM history

        WHERE roll_number=?

        """,

        (
            session["roll_number"],
        )

    )



    total = cursor.fetchone()[0]


    conn.close()



    return render_template(

        "student_profile.html",

        name=session["user"],

        email=session["email"],

        roll=session["roll_number"],

        role=session["role"],

        total=total

    )
@app.route("/my_evaluations")
def my_evaluations():


    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "student":

        return "Access Denied"


    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()


    cursor.execute(

        """

        SELECT *

        FROM history

        WHERE roll_number=?

        ORDER BY id DESC

        """,

        (
            session["roll_number"],
        )

    )


    records = cursor.fetchall()


    conn.close()



    return render_template(

        "my_evaluations.html",

        records=records
    )
@app.route("/my_reports")
def my_reports():


    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "student":

        return "Access Denied"



    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()



    cursor.execute(

        """

        SELECT *

        FROM history

        WHERE roll_number=?

        ORDER BY id DESC

        """,

        (
            session["roll_number"],
        )

    )


    reports = cursor.fetchall()


    conn.close()



    return render_template(

        "my_reports.html",

        reports=reports

    )
@app.route("/student_analytics")
def student_analytics():


    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "student":

        return "Access Denied"



    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()



    cursor.execute(

        """

        SELECT

        COUNT(*),

        AVG(percentage),

        MAX(percentage),

        MIN(percentage)

        FROM history

        WHERE roll_number=?

        """,

        (
            session["roll_number"],
        )

    )


    data = cursor.fetchone()


    conn.close()



    total = data[0]


    average = round(data[1],2) if data[1] else 0


    highest = data[2] if data[2] else 0


    lowest = data[3] if data[3] else 0



    if average >= 80:

        status = "Excellent Performance 🏆"


    elif average >= 60:

        status = "Good Performance 👍"


    elif average >= 40:

        status = "Need More Practice 📚"


    else:

        status = "Needs Improvement ⚠️"




    return render_template(

        "student_analytics.html",

        total=total,

        average=average,

        highest=highest,

        lowest=lowest,

        status=status

    )
@app.route("/student_ai_feedback")
def student_ai_feedback():


    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "student":

        return "Access Denied"



    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()



    cursor.execute(

        """

        SELECT AVG(percentage)

        FROM history

        WHERE roll_number=?

        """,

        (
            session["roll_number"],
        )

    )



    avg = cursor.fetchone()[0]


    conn.close()



    if avg:

        avg = round(
            avg,
            2
        )

    else:

        avg = 0




    if avg >= 80:


        strength = "Excellent understanding of concepts"


        improvement = "Focus on maintaining consistency and solving advanced questions"



    elif avg >= 60:


        strength = "Good subject knowledge"


        improvement = "Add more detailed explanations and examples in answers"



    elif avg >= 40:


        strength = "Basic concepts are understood"


        improvement = "Revise topics regularly and improve answer presentation"



    else:


        strength = "Learning progress started"


        improvement = "Need more practice and strengthen fundamentals"




    return render_template(

        "student_ai_feedback.html",

        average=avg,

        strength=strength,

        improvement=improvement

    )
@app.route("/achievements")
def achievements():


    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "student":

        return "Access Denied"



    conn = sqlite3.connect(
        "evaluation.db"
    )


    cursor = conn.cursor()



    cursor.execute(

        """

        SELECT

        COUNT(*),

        AVG(percentage),

        MAX(percentage)

        FROM history

        WHERE roll_number=?

        """,

        (
            session["roll_number"],
        )

    )


    data = cursor.fetchone()


    conn.close()



    total_tests = data[0]


    average = round(data[1],2) if data[1] else 0


    highest = data[2] if data[2] else 0




    badges = []



    if average >= 80:


        badges.append(

            "🏆 Excellent Performer"

        )



    if highest >= 90:


        badges.append(

            "⭐ High Scorer"

        )



    if total_tests >= 5:


        badges.append(

            "🔥 Consistent Learner"

        )



    if average >= 60:


        badges.append(

            "📈 Good Progress"

        )




    if len(badges) == 0:


        badges.append(

            "🌱 Keep Learning"

        )





    return render_template(

        "achievements.html",

        badges=badges,

        average=average,

        total_tests=total_tests

    )
@app.route("/student_settings", methods=["GET","POST"])
def student_settings():


    if "user" not in session:

        return redirect(
            "/login"
        )


    if session.get("role") != "student":

        return "Access Denied"



    message = None


    if request.method == "POST":


        new_name = request.form["name"]

        new_password = request.form["password"]



        conn = sqlite3.connect(
            "evaluation.db"
        )


        cursor = conn.cursor()



        if new_password:


            pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'


            if not re.match(
                pattern,
                new_password
            ):


                conn.close()


                return render_template(

                    "student_settings.html",

                    error="Password must contain uppercase, lowercase, number, special character and minimum 8 characters",

                    name=session["user"],

                    email=session["email"],

                    roll=session["roll_number"]

                )



            hashed_password = generate_password_hash(

                new_password

            )



            cursor.execute(

                """

                UPDATE users

                SET name=?,

                password=?

                WHERE email=?

                """,

                (

                    new_name,

                    hashed_password,

                    session["email"]

                )

            )



        else:


            cursor.execute(

                """

                UPDATE users

                SET name=?

                WHERE email=?

                """,

                (

                    new_name,

                    session["email"]

                )

            )



        conn.commit()


        conn.close()



        session["user"] = new_name


        message = "Account Updated Successfully"




    return render_template(

        "student_settings.html",

        name=session["user"],

        email=session["email"],

        roll=session["roll_number"],

        message=message

    )
@app.route("/")
def landing():

    return render_template(
        "landing.html"
    )
@app.route("/evaluation", methods=["GET", "POST"])
def home():
    if "user" not in session:

        return redirect(
            "/login"
        )
    if session.get("role") != "faculty":
        return "Access Denied"
    
    if request.method == "POST":
        delete_old_files()
        # =========================
        # Student Details
        # =========================

        student_name = request.form["student_name"]
        roll_number = request.form["roll_number"]
        subject_name = request.form["subject_name"]
        evaluation_time = datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).strftime(
            "%d-%m-%Y %I:%M %p"
        )
        # =========================
        # Questions & Model Answers
        # =========================

        questions = request.form["questions"]
        model_answers = request.form["model_answers"]

        # =========================
        # PDF Upload
        # =========================

        pdf_file = request.files["answer_pdf"]
        session_id = uuid.uuid4().hex

        pdf_filename = f"{session_id}_{pdf_file.filename}"

        pdf_path = os.path.join(
            UPLOAD_FOLDER,
            pdf_filename
        )

        pdf_file.save(pdf_path)

        print("\n===== PDF SAVED =====")
        print(pdf_path)

        # =========================
        # OCR Extraction
        # =========================

        pdf = fitz.open(pdf_path)

        full_ocr_text = ""

        saved_images = []

        for page_number in range(len(pdf)):


            page = pdf[page_number]

            pix = page.get_pixmap(
                matrix=fitz.Matrix(3,3)
            )


            image_path = os.path.join(
                UPLOAD_FOLDER,
                f"{session_id}_page_{page_number+1}.png"
            )

            pix.save(image_path)
            saved_images.append(
                os.path.basename(image_path)
            )
            print(
                f"IMAGE CREATED: {image_path}"
            )

            result = ocr.ocr(
                image_path,
                cls=True
            )

            if result:

                for line in result[0]:

                    text = line[1][0]

                    full_ocr_text += text + "\n"

        pdf.close()

        print("\n===== COMPLETE OCR TEXT =====")
        print(full_ocr_text)

        # =========================
        # Split Model Answers
        # =========================

        model_list = re.split(
            r'\bA[1-5]\.',
            model_answers
        )

        model_list = [
            x.strip()
            for x in model_list
            if x.strip()
        ]

        # =========================
        # Split Student Answers
        # =========================

        student_list = re.split(
            r'\n\s*[1-5]\.?',
            "\n" + full_ocr_text
        )

        student_list = [
            x.strip()
            for x in student_list
            if x.strip()
        ]

        print("\n===== MODEL ANSWERS =====")
        print(len(model_list))

        print("\n===== STUDENT ANSWERS =====")
        print(len(student_list))

        # =========================
        # Similarity Calculation
        # =========================

        total_marks = 0
        results = []

        for i in range(
            min(
                len(model_list),
                len(student_list)
            )
        ):

            model_text = re.sub(
                r"\s+",
                " ",
                model_list[i]
            ).strip()

            student_text = re.sub(
                r"\s+",
                " ",
                student_list[i]
            ).strip()

            emb1 = similarity_model.encode(
                model_text,
                convert_to_tensor=True
            )

            emb2 = similarity_model.encode(
                student_text,
                convert_to_tensor=True
            )

            score = util.cos_sim(
                emb1,
                emb2
            ).item()

            percentage = score * 100

            if percentage >= 90:
                marks = 10
            elif percentage >= 82:
                marks = 9
            elif percentage >= 74:
                marks = 8
            elif percentage >= 66:
                marks = 7
            elif percentage >= 58:
                marks = 6
            elif percentage >= 50:
                marks = 5
            elif percentage >= 40:
                marks = 4
            elif percentage >= 30:
                marks = 3
            elif percentage >= 20:
                marks = 2
            else:
                marks = 1

            total_marks += marks

            results.append({

                "question": i + 1,

                "percentage": round(
                    percentage,
                    2
                ),

                "marks": marks

            })

            print(
                f"\nQuestion {i+1}"
            )

            print(
                f"Similarity: {percentage:.2f}%"
            )

            print(
                f"Marks: {marks}/10"
            )

        # =========================
        # Final Percentage
        # =========================

        final_percentage = round(
            (total_marks / 50) * 100,
            2
        )

        if final_percentage >= 80:

            feedback = "Excellent"

        elif final_percentage >= 60:

            feedback = "Good"

        elif final_percentage >= 40:

            feedback = "Average"

        else:

            feedback = "Needs Improvement"

        print("\n====================")
        print(
            f"TOTAL MARKS = {total_marks}/50"
        )
        global report_data

        report_data = {

            "student_name": student_name,

            "roll_number": roll_number,

            "subject_name": subject_name,

            "evaluation_time": evaluation_time,

            "results": results,

            "total_marks": total_marks,

            "final_percentage": final_percentage,

            "feedback": feedback,

            "session_id": session_id

        }
        conn = sqlite3.connect(
            "evaluation.db",
            check_same_thread=False
        )

        cursor = conn.cursor()

        cursor.execute(

            """

            INSERT INTO history(

                student_name,
                roll_number,
                subject_name,
                marks,
                percentage,
                feedback,
                evaluation_time

            )

            VALUES(?,?,?,?,?,?,?)

            """,

            (

                student_name,
                roll_number,
                subject_name,
                total_marks,
                final_percentage,
                feedback,
                evaluation_time

            )

        )

        conn.commit()

        conn.close()
        return render_template(

            "result.html",

            student_name=student_name,
            roll_number=roll_number,
            subject_name=subject_name,
            evaluation_time=evaluation_time,

            results=results,

            total_marks=total_marks,

            final_percentage=final_percentage,

            feedback=feedback,

            image_names=saved_images

        )

    return render_template("index.html")
@app.route("/forgot_password", methods=["GET","POST"])
def forgot_password():

    if request.method == "POST":


        email = request.form["email"]


        conn = sqlite3.connect(
            "evaluation.db"
        )

        cursor = conn.cursor()


        cursor.execute(

            "SELECT * FROM users WHERE email=?",

            (email,)

        )


        user = cursor.fetchone()


        conn.close()



        if user:


            otp = str(

                random.randint(
                    100000,
                    999999
                )

            )


            session["otp"] = otp

            session["reset_email"] = email



            msg = Message(

                "AI Evaluation Password Reset OTP",

                sender=app.config["MAIL_USERNAME"],

                recipients=[email]

            )


            msg.body = f"""

Hello,

Your OTP for password reset is:

{otp}


This OTP is valid for password reset.

AI Answer Evaluation System

"""


            mail.send(msg)



            return redirect(

                "/verify_otp"

            )


        else:


            return render_template(

                "forgot_password.html",

                error="Email not registered"

            )



    return render_template(

        "forgot_password.html"

    )
@app.route("/verify_otp", methods=["GET","POST"])
def verify_otp():


    if request.method=="POST":


        entered=request.form["otp"]


        if entered == session["otp"]:


            return redirect(

                "/reset_password"

            )


        else:


            return render_template(

                "verify_otp.html",

                error="Invalid OTP"

            )



    return render_template(

        "verify_otp.html"

    )
@app.route("/reset_password", methods=["GET","POST"])
def reset_password():

    if "reset_email" not in session:

        return redirect(
            "/forgot_password"
        )


    if request.method == "POST":


        new_password = request.form["password"]


        # =====================
        # Strong Password Check
        # =====================

        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'


        if not re.match(pattern, new_password):

            return render_template(

                "reset_password.html",

                error="Password must contain uppercase, lowercase, number, special character and minimum 8 characters"

            )


        hashed_password = generate_password_hash(
            new_password
        )


        conn = sqlite3.connect(
            "evaluation.db"
        )


        cursor = conn.cursor()


        cursor.execute(

            """

            UPDATE users

            SET password=?

            WHERE email=?

            """,

            (
                hashed_password,
                session["reset_email"]
            )

        )


        conn.commit()


        conn.close()


        session.pop(
            "otp",
            None
        )


        session.pop(
            "reset_email",
            None
        )


        return redirect(
            "/login"
        )


    return render_template(
        "reset_password.html"
    )
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "faculty":
        return "Access Denied"
    conn = sqlite3.connect(
        "evaluation.db",
        check_same_thread=False
    )

    cursor = conn.cursor()

    cursor.execute(

        """

        SELECT *

        FROM history

        ORDER BY id DESC

        """

    )

    records = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        records=records
    )
@app.route("/delete_history")
def delete_history():
    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "faculty":
        return "Access Denied"
    conn = sqlite3.connect(
        "evaluation.db",
        check_same_thread=False
    )

    cursor = conn.cursor()

    cursor.execute("DELETE FROM history")

    cursor.execute(
        "DELETE FROM sqlite_sequence WHERE name='history'"
    )

    conn.commit()

    conn.close()

    return redirect("/history")
@app.route("/download_report")
def download_report():
    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "faculty":
        return "Access Denied"
    global report_data

    student = report_data[
        "student_name"
    ].replace(" ", "_")

    roll = report_data[
        "roll_number"
    ]

    pdf_file = os.path.join(
        UPLOAD_FOLDER,
        f"{student}_{roll}_Report.pdf"
    )

    c = canvas.Canvas(pdf_file)

    width = 595
    height = 842

    # =====================
    # Title
    # =====================

    c.setFont(
        "Helvetica-Bold",
        18
    )

    c.drawCentredString(
        width/2,
        800,
        "AI ASSISTED ANSWER EVALUATION REPORT"
    )

    # =====================
    # Student Details
    # =====================

    c.line(
        40,
        780,
        550,
        780
    )

    c.setFont(
        "Helvetica-Bold",
        14
    )

    c.drawString(
        50,
        750,
        "Student Information"
    )

    c.setFont(
        "Helvetica",
        12
    )

    c.drawString(
        60,
        720,
        f"Student Name : {report_data['student_name']}"
    )

    c.drawString(
        60,
        700,
        f"Roll Number : {report_data['roll_number']}"
    )

    c.drawString(
        60,
        680,
        f"Subject : {report_data['subject_name']}"
    )

    c.drawString(
        60,
        660,
        f"Date & Time : {report_data['evaluation_time']}"
    )

    # =====================
    # Question Table
    # =====================

    data = [

        [
            "Question",
            "Similarity",
            "Marks"
        ]

    ]

    for result in report_data["results"]:

        data.append(

            [

                f"Q{result['question']}",

                f"{result['percentage']}%",

                f"{result['marks']}/10"

            ]

        )

    table = Table(
        data,
        colWidths=[
            120,
            150,
            120
        ]
    )

    table.setStyle(

        TableStyle([

            (
                'BACKGROUND',
                (0,0),
                (-1,0),
                colors.lightblue
            ),

            (
                'GRID',
                (0,0),
                (-1,-1),
                1,
                colors.black
            ),

            (
                'ALIGN',
                (0,0),
                (-1,-1),
                'CENTER'
            )

        ])

    )

    table.wrapOn(
        c,
        width,
        height
    )

    table.drawOn(
        c,
        70,
        450
    )

    # =====================
    # Final Result
    # =====================

    c.setFont(
        "Helvetica-Bold",
        15
    )

    c.drawString(
        50,
        380,
        "Final Result"
    )

    c.setFont(
        "Helvetica",
        13
    )

    c.drawString(
        70,
        350,
        f"Total Marks : {report_data['total_marks']}/50"
    )

    c.drawString(
        70,
        325,
        f"Percentage : {report_data['final_percentage']}%"
    )

    c.drawString(
        70,
        300,
        f"Feedback : {report_data['feedback']}"
    )

    # =====================
    # Footer
    # =====================

    c.line(
        40,
        120,
        550,
        120
    )

    c.setFont(
        "Helvetica-Oblique",
        10
    )

    c.drawCentredString(
        width/2,
        90,
        "Generated by AI Assisted Descriptive Answer Evaluation System"
    )

    c.save()

    response = send_file(
        pdf_file,
        as_attachment=True
    )

    return response
@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )