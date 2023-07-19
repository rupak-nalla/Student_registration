from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask import render_template
from flask import request
from sqlalchemy import create_engine, update, delete
from sqlalchemy.orm import Session

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

s = "SELECT * FROM student"
engine = create_engine("sqlite:///./database.sqlite3")


class student(db.Model):
  __tablename__ = 'student'
  student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  roll_number = db.Column(db.String, unique=True, nullable=False)
  first_name = db.Column(db.String, nullable=False)
  last_name = db.Column(db.String)


class course(db.Model):
  __tablename__ = 'course'
  course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  course_code = db.Column(db.String, unique=True, nullable=False)
  course_name = db.Column(db.String, nullable=False)
  course_description = db.Column(db.String)


class enrollments(db.Model):
  __tablename__ = 'enrollments'
  enrollment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  estudent_id = db.Column(db.Integer,
                          db.ForeignKey("student.student_id"),
                          nullable=False)
  ecourse_id = db.Column(db.Integer,
                         db.ForeignKey("course.course_id"),
                         nullable=False)


'''HOME PAGE'''


@app.route('/', methods=["GET"])
def home():
  if (request.method == "GET"):

    engine = create_engine("sqlite:///./database.sqlite3")
    with Session(engine) as session:
      count = session.query(student.student_id).count()
      stud = session.query(student).all()
      if (count == 0):
        return (render_template("index.html", empty=True, students=stud))
      else:
        return (render_template("index.html", empty=False, students=stud))


'''ADD STUDENTS'''


@app.route("/student/create", methods=["GET", "POST"])
def add_student():
  if (request.method == "POST"):
    engine = create_engine("sqlite:///./database.sqlite3")
    with Session(engine) as session:
      roll_no = request.form["roll"]
      '''checking for duplicationn'''

      count = session.query(student).filter(
        student.roll_number == roll_no).count()
      
      if (count >= 1):

        t = render_template("duplication.html")
        return (t)
      '''no duplication, so going for insertion '''
      f_name = request.form["f_name"]
      l_name = request.form["l_name"]
      courses_selected = request.form.getlist("courses")
      '''insertion to table students'''
      new_student = student(roll_number=roll_no,
                            first_name=f_name,
                            last_name=l_name)
      session.add(new_student)
      for i in courses_selected:
        engine = create_engine("sqlite:///./database.sqlite3")
        with engine.connect() as conn:
          new_student_id = session.query(
            student.student_id).filter(student.roll_number == roll_no).all()
          '''insertion to enrollments'''
          new_enrollment = enrollments(estudent_id=int(new_student_id[0][0]),
                                       ecourse_id=int(i[-1]))
          session.add(new_enrollment)
      session.commit()
      '''going back to home page'''
      stud = session.query(student).all()
      return (render_template("index.html", empty=False, students=stud))

  if (request.method == "GET"):
    
    return (render_template("Add_Student.html"))


'''UPDATE STUDENT DETAILS'''


@app.route("/student/<int:student_id>/update", methods=["POST", "GET"])
def student_update(student_id):
  engine = create_engine("sqlite:///./database.sqlite3")
  with Session(engine) as session:
    stud = session.query(
      student.first_name, student.last_name, student.roll_number,
      student.student_id).filter(student.student_id == student_id).all()
    if (request.method == "GET"):
      return (render_template("update.html", students=stud))
    if (request.method == "POST"):
      edited_fname = request.form.get("f_name")
      edited_lname = request.form.get("l_name")
      edited_courses = request.form.getlist("courses")
      '''updating student table'''
      stmt = update(student).where(student.student_id == student_id).values(
        first_name=edited_fname, last_name=edited_lname)

      with engine.connect() as conn:
        conn.execute(stmt)
        '''updating enrollments table'''
        del_enroll = delete(enrollments).where(
          enrollments.estudent_id == student_id)
        conn.execute(del_enroll)
        for i in edited_courses:
          new_enrollment = enrollments(estudent_id=student_id,
                                       ecourse_id=int(i[-1]))
          session.add(new_enrollment)
        session.commit()
        '''returning to home page'''
        stud = session.query(student).all()
        return (render_template("index.html", empty=False, students=stud))


'''DELETE STUDENTS'''


@app.route("/student/<int:student_id>/delete")
def student_delete(student_id):
  '''deleting both student_id rows in enrollment and students'''
  del_stud = delete(student).where(student.student_id == student_id)
  del_enroll = delete(enrollments).where(enrollments.estudent_id == student_id)
  stmt = "SELECT count(*) from student"
  stud = "SELECT * FROM student"
  '''returning to home page and executing deletion'''
  engine = create_engine("sqlite:///./database.sqlite3")
  with engine.connect() as conn:
    conn.execute(del_stud)
    conn.execute(del_enroll)
    with Session(engine) as session:
        count = session.query(student.student_id).count()
        stud =session.query(student).all()
        if (count == 0):
          return (render_template("index.html", empty=True, students=stud))
        else:
          return (render_template("index.html", empty=False, students=stud))


'''Roll numbers and enrollments'''


@app.route("/student/<int:student_id>")
def Roll_and_enroll(student_id):
  engine = create_engine("sqlite:///./database.sqlite3")
  with Session(engine) as session:
    stud = session.query(student).filter(
      student.student_id == student_id).all()
    enrolls = session.query(enrollments.ecourse_id).filter(
      enrollments.estudent_id == student_id).subquery()

    enrolled_courses = session.query(course).filter(
      course.course_id.in_(enrolls)).all()
    return (render_template("roll_and_enroll.html",
                            students=stud,
                            enrolled_c=enrolled_courses))


if (__name__) == "__main__":
  app.run(host="0.0.0.0", port=8080, debug=True)
