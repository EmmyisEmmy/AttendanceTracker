from flask import Flask, request, redirect, url_for, send_file,session
import random
from datetime import datetime, timedelta
import sqlite3
import csv
import sqlite3
import socket
import qrcode
import os

from pathlib import Path

export_path = Path.home() / "Documents" / "MyAttendX"
export_path.mkdir(parents=True, exist_ok=True)

csv_file = export_path / "database_export.csv"

connection = sqlite3.connect("my_database.db")
print(os.path.abspath("my_database.db"))

cursor = connection.cursor()
cursor.execute("PRAGMA table_info(SESSIONS)")

# columns = cursor.fetchall()
# print(columns)


cursor.execute("PRAGMA foreign_keys = ON;")


cursor.execute("""
CREATE TABLE IF NOT EXISTS SESSIONS(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT NOT NULL,
    pin TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    stop_time DATETIME
)
""")

cursor.execute("PRAGMA table_info(SESSIONS)")

columns = [column[1] for column in cursor.fetchall()]

if "stop_time" not in columns:
    cursor.execute("ALTER TABLE SESSIONS ADD COLUMN stop_time DATETIME")

connection.commit()




cursor.execute("""


CREATE TABLE IF NOT EXISTS attendance(
    new_id INTEGER PRIMARY KEY,
    session_id INTEGER,
    studentid VARCHAR(10),                             
    student_name VARCHAR(100),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES SESSIONS (id),
    
    CONSTRAINT unique_student_id UNIQUE (studentid, session_id)

)
""")
cursor.execute("PRAGMA table_info(attendance)")
columns = [column[1] for column in cursor.fetchall()]

if "timestamp" not in columns:
    cursor.execute("ALTER TABLE attendance ADD COLUMN timestamp DATETIME")

connection.commit()


app = Flask(__name__)

app.secret_key = 'super_attendance'

session_pin = None
course_message = None



@app.route("/")
def home():

    head_count = session.get('count')

    session_id = None
    session_status = None
    main_id = None

    local_ip = get_local_ip()

    use_address = f"http://{local_ip}:5000/active-session"
    print(use_address)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_folder_path = os.path.join(base_dir, 'static', 'Images')
    save_path = os.path.join(image_folder_path, 'attendance_qr.png')

    
    os.makedirs(image_folder_path, exist_ok=True)

    
    qr = qrcode.QRCode(
        version=1,       
        box_size=10,     
        border=4,        
    )

    
    qr.add_data(use_address)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(save_path)
   
    

    if session_pin is not None:
      pin_message = f"<p>This Session is Active: The pin is {session_pin}</p>"
    else:
      pin_message = ""

 
    connection = sqlite3.connect("my_database.db")
    
    cursor = connection.cursor()

    use_id = "SELECT id FROM SESSIONS WHERE course = ?"

    cursor.execute("SELECT id, course FROM SESSIONS ORDER BY id DESC LIMIT 1")

    output = cursor.fetchone()

    table_row = ""

    if output is not None:

      main_id = output[0]

      sql_query = "SELECT studentid, student_name, timestamp FROM attendance WHERE session_id = ?"

      cursor.execute(sql_query,(main_id,))

      output = cursor.fetchall()

      sql_query = "SELECT status FROM SESSIONS WHERE id = ?"
      cursor.execute(sql_query, (main_id,))
      session_status = cursor.fetchone()[0]

      for id,name, submission_time in output:
      

        result = f"""<tr>
                    <td>{id}</td>
                    <td>{name}</td>
                    <td>{submission_time}</td>
                    
                  </tr>"""


        
        table_row += result

      connection.commit()
      connection.close()

    else:
      connection.commit()
      connection.close()
      table_row = ""

 
    if course_message is not None:
          message = f"<p>Course Title: {course_message}</p>"
    else:
          message = ""
    


    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lecturer Attendance</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='Images/style.css') }}">
</head>

<body>

    <!-- Top Portal Header -->
    <header class="header-bar">
        <div>
            <div class="portal-subtitle">Classroom Portal</div>
            <h1 class="portal-title">Lecturer Attendance</h1>
        </div>

        <div class="badge-status-pill">
            <span class="dot-live"></span>
            Live Sync
        </div>
    </header>


    <!-- Configure Session -->
    <section class="card">

        <div class="card-title-sub">Configure Session</div>

        <form action="/start-session" method="POST">

            <div class="field-group">
                <label class="field-label" for="course-title">
                    Course Title
                </label>

                <input
                    id="course-title"
                    class="input-field"
                    type="text"
                    name="course_title"
                    placeholder="e.g. URP 211"
                    required
                >
            </div>

            <div class="field-group">
                            <label class="field-label" for="head-count">
                                Head Count
                            </label>
            
                            <input
                                id="head_count"
                                class="input-field"
                                type="number"
                                min="1"
                                name="headcount"
                                placeholder="e.g. 55"
                                required
                            >
                        </div>


            <div class="field-group" style="margin-bottom: 0;">

                <label class="field-label" for="attendance-duration">
                    Attendance duration (minutes)
                </label>

                <div class="duration-row">

                    <input
                        id="attendance-duration"
                        class="input-field duration-input"
                        type="number"
                        name="duration"
                        min="1"
                        required
                    >

                    <button class="btn-primary" type="submit">
                        Start Session
                    </button>

                </div>

               

            </div>

        </form>

                    <div class="session-url-container">
               
                <div class="url-box">
                    <div class="url-text-wrapper">
                        <svg class="url-icon" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                        </svg>
                        <code class="url-code" id="sessionUrl">{use_address}</code>
                         
                    </div>

                    
                   
                </div>
                <img src="/static/Images/attendance_qr.png"
                     alt="Attendance QR Code"
                     width="350"
                     height="300">
            </div>

    </section>


    <!-- Active Session -->
    <section class="active-session-card">

        <div class="active-header">

            <div class="badge-status">
                <span class="dot-live"></span>
                THIS SESSION IS ACTIVE
            </div>

            <div class="badge-expiry">
                Active
            </div>

        </div>


        <div class="active-course">
            Course Title:
            <strong>{course_message if course_message is not None else "No active session"}</strong>
        </div>


        <div class="pin-section">

            <div>

                <div class="pin-label">
                    Session PIN
                </div>

                <div class="pin-display">
                    {session_pin if session_pin is not None else "------"}
                </div>

            </div>


            <button class="btn-copy" type="button">
                Copy PIN
            </button>

        </div>

    </section>


    <!-- Attendance Records -->
    <section class="card">

        <div class="table-header-row">

            <h2 class="table-title">
                Attendance Records
            </h2>

            <span class="badge-count">
                {f"{len(output) if output is not None else 0} Present of {head_count}" if session_status == "ACTIVE" else "No count"}
            </span>

        </div>


        <div class="table-course-sub">
            Course:
            <strong>
                {course_message if course_message is not None else "No active session"}
            </strong>
        </div>


        <div class="table-container">

            <table class="records-table">

                <thead>
                    <tr>
                        <th>Student ID</th>
                        <th>Full Name</th>
                        <th>Submission time</th>
                    </tr>
                </thead>

                <tbody>
                    
                    {"<tr><td colspan='3' style='text-align: center;'>Nothing to see here</td></tr>" if session_status != "ACTIVE" else table_row}
                </tbody>

            </table>

        </div>


        <form action="/export-table" method="POST">

            <input type="hidden" name="session_id" value="{main_id}">

            <button class="btn-export" type="submit">

                <svg
                    width="15"
                    height="15"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    viewBox="0 0 24 24"
                >
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>

                Export Table

            </button>

        </form>

    </section>

</body>
</html>
"""



def get_local_ip():
    
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip



@app.route("/export-table", methods=["POST"])
def export_attendance():
    

    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()

    session_main = request.form.get("session_id")
    
    sql_query = "SELECT studentid, student_name FROM attendance WHERE session_id = ?"
    cursor.execute(sql_query, (session_main,))

    headers = [description[0] for description in cursor.description]

    with open(csv_file, "w", newline="", encoding="utf-8") as file:

      writer = csv.writer(file)

      writer.writerow(headers)

     
      while True:
          rows = cursor.fetchmany(1000)
          if not rows:
              break
          writer.writerows(rows)

    cursor.close()
    conn.close()

    return send_file(
      csv_file,
      as_attachment=True,
      download_name="attendance.csv",
      mimetype="text/csv"
    )



@app.route("/start-session", methods=["POST"])

def generate_session():
    

    global session_pin
    global course_message

    head_count = request.form.get("headcount")
    session['count'] = head_count

    random_numbers = [random.randint(0,9) for _ in range(6)]

    session_pin =  "".join(map(str, random_numbers)) 

    course_message = request.form.get("course_title")
    attendance_duration = request.form.get("duration")
    use_attendance_duration = int(attendance_duration)

    session_starting_time = datetime.now()
    session_stop_time = session_starting_time + timedelta(minutes=use_attendance_duration)


    connection = sqlite3.connect("my_database.db")
    print("DATABASE:", os.path.abspath("my_database.db"))

    cursor = connection.cursor()

    sql_query = "INSERT INTO SESSIONS (course,pin,stop_time) VALUES (?,?,?)"
    data_tuple = (course_message,session_pin,session_stop_time)


    cursor.execute(sql_query, data_tuple)

    connection.commit()

    connection.close()



    return redirect(url_for("home"))


@app.route("/active-session")

def Active_session():

      user_submitted_title = request.args.get("course_attend_title")

      result = None

      session_id = None

      connection = sqlite3.connect("my_database.db")

      cursor = connection.cursor()


      sql_query = "SELECT * FROM SESSIONS WHERE course = ? ORDER BY id DESC LIMIT 1"

      cursor.execute(sql_query,(user_submitted_title,))

      output = cursor.fetchall()
      
      session_found = False

      if output:


          for session_id,title,_,status,_,stop_time in output:


        
            student_submit_time = datetime.now()
            stoppage_time = datetime.strptime(stop_time, "%Y-%m-%d %H:%M:%S.%f")
            

            if student_submit_time < stoppage_time:
                result = f"{title}, {status}"
                session_found = True

            else:
                result = "Attendance is closed"

          connection.close()

               
      else:
          result = "No Active Session Found"


      return f"""
       
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Active Sessions - Student Portal</title>
    <link rel="stylesheet" href="/static/style.css">
</head>

<body>

    <!-- Portal Header -->
    <header class="header-bar">
        <div>
            <div class="portal-subtitle">Student Portal</div>
            <h1 class="portal-title">Find an Active Session</h1>
        </div>

        <div class="badge-live-sync">
            <span class="dot-live"></span>
            Sessions Online
        </div>
    </header>


    <!-- Search Session -->
    <section class="card">

        <div class="card-title-sub">
            Search Attendance
        </div>

        <form action="/active-session" method="GET">

            <div class="field-group">

                <label class="field-label" for="course_attend_id">
                    Course Title
                </label>

                <input
                    type="text"
                    id="course_attend_id"
                    name="course_attend_title"
                    class="input-field"
                    placeholder="e.g. URP 211"
                    required
                >

            </div>

            <button type="submit" class="btn-primary">
                Search Session
            </button>

        </form>

    </section>


    <!-- Search Result -->

    <div class="section-meta-row">

        <span class="section-title">
            Matching Active Sessions
        </span>

    </div>


    <section class="session-result-card">

        <div class="session-card-header">

            <div>
                <span class="course-badge">
                    Attendance Session
                </span>

                <h2 class="session-course-title">
                    {result}
                </h2>
            </div>

        </div>


        <!-- Join Attendance -->

        <form action="/student-form" method="POST">

            <input
                type="hidden"
                name="session_id"
                value="{session_id}"
            >

            <button type="submit" class="btn-join" {" " if session_found else "disabled"}>
                Join Attendance Session

                <svg
                    width="16"
                    height="16"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    viewBox="0 0 24 24"
                >
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                </svg>

            </button>

        </form>

    </section>

</body>
</html>

    
          """
   


@app.route("/student-form", methods=["GET","POST"])

def student_attendance():

    error_status = request.args.get("error")

    if error_status == "incorrect_pin":
      error_status = "The pin you have entered is incorrect. Please try again"
       
    else:
        error_status = ""
    

    session_id = request.form.get("session_id")


    return f"""
    
  <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Student Attendance</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>

  <main class="attendance-container">
    <!-- Top Header -->
    <header class="header-bar">
      <div>
        <div class="portal-subtitle">Student Portal</div>
        <h1 class="portal-title">Student Attendance</h1>
      </div>
      <div class="badge-status-pill">
        <span class="dot-live"></span>
        Active Session
      </div>
    </header>

    <!-- Check-in Form Card -->

    <section class="card">
      <div class="card-header">
        <h2 class="card-title-sub">Check-in Details</h2>
        <p class="card-instruction">Enter your details to register your attendance.</p>
      </div>

    {f"""<div style="
    background-color: #f8d7da;
    color: #842029;
    border: 1px solid #f5c2c7;
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 15px;">
    {error_status}
</div>""" if error_status else ""}

      <form action="/submit-attendance" method="POST">
        
        <!-- Attendance PIN -->
        <div class="field-group">
          <div class="label-row">
            <label class="field-label" for="pin">Attendance PIN</label>
            <span class="field-hint">6-digit code from lecturer</span>
          </div>
          <div class="input-wrapper">
            <svg class="input-icon" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <input 
              type="text" 
              id="pin" 
              name="pin" 
              class="input-field" 
              placeholder="e.g. 718619" 
              inputmode="numeric" 
              required 
            />
          </div>
        </div>

        <!-- Student ID -->
        <div class="field-group">
          <div class="label-row">
            <label class="field-label" for="student_id">Student ID</label>
            <span class="field-hint">University Matric / ID</span>
          </div>
          <div class="input-wrapper">
            <svg class="input-icon" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <rect x="2" y="5" width="20" height="14" rx="2"></rect>
              <line x1="2" y1="10" x2="22" y2="10"></line>
            </svg>
            <input 
              type="text" 
              id="student_id" 
              name="student_id" 
              class="input-field" 
              placeholder="e.g. 134567" 
              required 
            />
          </div>
        </div>

        <!-- Full Name -->
        <div class="field-group">
          <div class="label-row">
            <label class="field-label" for="student_name">Full Name</label>
            <span class="field-hint">Official roster name</span>
          </div>
          <div class="input-wrapper">
            <svg class="input-icon" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <input 
              type="text" 
              id="student_name" 
              name="student_name" 
              class="input-field" 
              placeholder="e.g. Eking Okon" 
              required 
            />
          </div>
        </div>

        <!-- Notice Callout -->
        <div class="callout-box">
          <svg class="callout-icon" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
          <span>Make sure your PIN matches the screen displayed by your lecturer. Attendance submissions are timestamped automatically.</span>
        </div>

        <!-- Hidden Session ID Binding -->
        <input type="hidden" name="session_id" value="{session_id}" />

        <!-- Submit Button -->
        <button type="submit" class="btn-submit">
          Submit Attendance
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </button>

      </form>
    </section>

   
  </main>

</body>
</html>


      """


@app.route("/submit-attendance", methods=["POST"])

def handle_form():

    submission_time = datetime.now()


    student_name_attend = request.form.get("student_name")
    student_matric_id = request.form.get("student_id")
    session_id = request.form.get("session_id")
    user_submitted_code = request.form.get("pin")

    connection = sqlite3.connect("my_database.db")

    cursor = connection.cursor()


    sql_query = "SELECT pin FROM SESSIONS WHERE id = ?"

    cursor.execute(sql_query,(session_id,))

    output = cursor.fetchone()

    stored_pin = output[0]


    if user_submitted_code == stored_pin:

         
    
            sql_query = "INSERT INTO attendance (studentid,student_name,session_id, timestamp) VALUES (?,?,?, CURRENT_TIMESTAMP)"
            data_tuple = (student_matric_id,student_name_attend,session_id)

            cursor.execute(sql_query, data_tuple)

            connection.commit()

            connection.close()
    
            
            return f""" 
            
            <!DOCTYPE html>
          <html lang="en">
          <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Attendance Confirmed - Student Portal</title>
              <link rel="stylesheet" href="/static/style.css">
          </head>
          <body>

              <main class="page-container">

                  <!-- Top Portal Header -->
                  <header class="header-bar">
                      <div>
                          <div class="portal-subtitle">Student Portal</div>
                          <h1 class="portal-title">Attendance Recorded</h1>
                      </div>

                      <div class="badge-status-success">
                          <span class="dot-success"></span>
                          Confirmed
                      </div>
                  </header>

                  <!-- Confirmation Card -->
                  <section class="card success-card">
                      
                      <!-- Success Icon Badge -->
                      <div class="icon-circle-wrapper">
                          <div class="icon-circle">
                              <svg class="check-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                  <polyline points="20 6 9 17 4 12"></polyline>
                              </svg>
                          </div>
                      </div>

                      <h2 class="success-heading">You're Checked In!</h2>
                      <p class="success-description">
                          You attended {course_message}. Your records have been submitted succesfully.
                      </p>

                      <!-- Submission Details Summary -->
                      <div class="details-summary-box">
                          <div class="summary-row">
                              <span class="summary-label">Course</span>
                              <span class="summary-value font-highlight">{course_message}</span>
                          </div>
                          <div class="summary-divider"></div>
                          <div class="summary-row">
                              <span class="summary-label">Student ID</span>
                              <span class="summary-value">{student_matric_id}</span>
                          </div>
                          <div class="summary-divider"></div>
                            <div class="summary-row">
                                <span class="summary-label">Student Name</span>
                                <span class="summary-value">{student_name_attend}</span>
                            </div>
                          <div class="summary-divider"></div>
                          <div class="summary-row">
                              <span class="summary-label">Timestamp</span>
                              <span class="summary-value" id="currentTimestamp">{submission_time}</span>
                          </div>
                      </div>

                      <!-- Action Button -->
                      <div class="action-wrapper">
                          <a href="/active-session" class="btn-primary btn-return">
                              Done
                              <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                                  <line x1="5" y1="12" x2="19" y2="12"></line>
                                  <polyline points="12 5 19 12 12 19"></polyline>
                              </svg>
                          </a>
                      </div>

                  </section>

              </main>

          </body>
          </html>
"""
    else:
            connection.close()
            return redirect("/student-form?error=incorrect_pin")
    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
