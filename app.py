from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask import render_template
from flask import request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///week7database.sqlite3"
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

s = "SELECT * FROM student"
engine = create_engine("sqlite:///./week7_database.sqlite3")


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
    with Session(engine) as session:
      roll_no = request.form["roll"]
      '''checking for duplicationn'''
      count = session.query(student).filter(
        student.roll_number == roll_no).count()
      if (count >= 1):
        t = render_template("duplicate_student.html")
        return (t)
      '''no duplication, so going for insertion '''
      f_name = request.form["f_name"]
      l_name = request.form["l_name"]
      '''insertion to table students'''
      new_student = student(roll_number=roll_no,
                            first_name=f_name,
                            last_name=l_name)
      session.add(new_student)
      session.commit()
      '''going back to home page'''
      stud = session.query(student).all()
      return (render_template("index.html", empty=False, students=stud))

  if (request.method == "GET"):
    return (render_template("add_student.html"))


'''UPDATE STUDENT DETAILS'''


@app.route("/student/<int:student_id>/update", methods=["POST", "GET"])
def student_update(student_id):
  with Session(engine) as session:
    stud = session.query(student).filter(
      student.student_id == student_id).all()
    c = session.query(course).all()
    if (request.method == "GET"):
      return (render_template("update_student.html", students=stud, courses=c))
    if (request.method == "POST"):
      edited_fname = request.form.get("f_name")
      edited_lname = request.form.get("l_name")
      edited_course = request.form.get("course")
      '''updating student table'''
      s = session.query(student).filter(
        student.student_id == student_id).first()
      s.first_name = edited_fname
      s.last_name = edited_lname
      session.commit()
      new_enroll = enrollments(estudent_id=student_id,
                               ecourse_id=edited_course)
      session.add(new_enroll)
      session.commit()
      stud = session.query(student).all()
      return (render_template("index.html", empty=False, students=stud))


'''DELETE STUDENTS'''


@app.route("/student/<int:student_id>/delete")
def student_delete(student_id):
  '''deleting both student_id rows in enrollment and students'''
  with Session(engine) as session:
    studs = session.query(student).all()

    session.query(student).filter(student.student_id == student_id).delete()
    session.query(enrollments).filter(
      enrollments.estudent_id == student_id).delete()
    counts = session.query(student).count()
    studs = session.query(student).all()
    session.commit()

    if (counts > 0):
      return render_template("index.html", empty=False, students=studs)
    else:
      return (render_template("index.html", empty=True, students=studs))
  '''returning to home page and executing deletion'''


'''Roll numbers and enrollments'''


@app.route("/student/<int:student_id>")
def Roll_and_enroll(student_id):
  with Session(engine) as session:
    stud = session.query(student).filter(
      student.student_id == student_id).all()
    enrolls = session.query(enrollments.ecourse_id).filter(
      enrollments.estudent_id == student_id).subquery()

    enrolled_courses = session.query(course).filter(
      course.course_id.in_(enrolls)).all()
    counts = len(enrolled_courses)
    if (counts != 0):
      return (render_template("enroll_stud.html",
                              students=stud,
                              enrolled_c=enrolled_courses,
                              empty_enroll=False))
    else:
      return (render_template("enroll_stud.html",
                              students=stud,
                              enrolled_c=enrolled_courses,
                              empty_enroll=True))


#withdraw courses
@app.route("/student/<int:student_id>/withdraw/<int:course_id>",
           methods=["GET"])
def withdraw(student_id, course_id):
  with Session(engine) as session:
    e = session.query(enrollments).filter(
      enrollments.estudent_id == student_id
      and enrollments.ecourse_id == course_id).first()
    session.delete(e)
    session.commit()
    studs = session.query(student).all()
    return (render_template("index.html", students=studs, empty=False))


#courses list
@app.route("/courses")
def courses():
  with Session(engine) as session:
    c = session.query(course).all()
    if (c):
      return (render_template("courses.html", coursess=c, empty=False))
    else:
      return (render_template("courses.html", coursess=c, empty=True))


#Add course
@app.route("/course/create", methods=["POST", "GET"])
def add_course():
  with Session(engine) as session:
    if (request.method == "GET"):
      return (render_template("add_course.html"))
    if (request.method == "POST"):
      c_code = request.form["code"]
      c_name = request.form["c_name"]
      c_desc = request.form["desc"]
      c = session.query(course).filter(course.course_code == c_code).first()
      if (c):
        return (render_template("duplicate_course.html"))

      new_course = course(course_code=c_code,
                          course_name=c_name,
                          course_description=c_desc)
      session.add(new_course)
      session.commit()
      c = session.query(course).all()
      return (render_template("courses.html", coursess=c, empty=False))


#update course
@app.route("/course/<int:course_id>/update", methods=["GET", "POST"])
def update_courses(course_id):
  with Session(engine) as session:
    if (request.method == "GET"):
      c = session.query(course).filter(course.course_id == course_id).first()
      return (render_template("update_course.html", coursess=c))
    if (request.method == "POST"):
      c_name = request.form["c_name"]
      c_desc = request.form["desc"]
      c = session.query(course).filter(course.course_id == course_id).first()
      c.course_name = c_name
      c.course_description = c_desc
      session.commit()
      c = session.query(course).all()
      return (render_template("courses.html", coursess=c, empty=False))


#delete course
@app.route("/course/<int:course_id>/delete")
def delete_course(course_id):
  with Session(engine) as session:
    session.query(course).filter(course.course_id == course_id).delete()
    session.query(enrollments).filter(
      enrollments.ecourse_id == course_id).delete()
    session.commit()
    c = session.query(course).all()
    if (c):
      return (render_template("courses.html", coursess=c, empty=False))
    else:
      return (render_template("courses.html", coursess=c, empty=True))


#courses and enrolls
@app.route("/course/<int:course_id>")
def course_enrolls(course_id):
  with Session(engine) as session:

    enroll = session.query(enrollments.estudent_id).filter(
      enrollments.ecourse_id == course_id).subquery()

    enrolled_students = session.query(student).filter(
      student.student_id.in_(enroll)).all()

    c = session.query(course).filter(course.course_id == course_id).first()
    return (render_template("enroll_course.html",
                            coursess=c,
                            enrolls=enrolled_students))


if (__name__) == "__main__":
  app.run()
