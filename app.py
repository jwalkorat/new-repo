from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from sqlalchemy.orm import *
from sqlalchemy import *
import datetime


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students-data.db'
app.secret_key = 'this-is-my-app'
db.init_app(app)

class Students(db.Model):

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    roll_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    math_score: Mapped[int] = mapped_column(nullable=False)
    reading_score: Mapped[int] = mapped_column(nullable=False)
    writing_score: Mapped[int] = mapped_column(nullable=False)
    attendance: Mapped[int] = mapped_column(nullable=False)

    added_on: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=datetime.datetime.now
    )

    def __repr__(self):
        return f"<Student: {self.name}>"

with app.app_context():
    db.create_all()


class MyForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    roll_number = StringField(label="Roll number", validators=[DataRequired()])
    gender = StringField(label="Gender", validators=[DataRequired()])
    math_score = IntegerField(label="Math score", validators=[DataRequired(), NumberRange(min=0, max=100)])
    reading_score = IntegerField(label="Reading score", validators=[DataRequired(), NumberRange(min=0, max=100)])
    writing_score = IntegerField(label="Writing score", validators=[DataRequired(), NumberRange(min=0, max=100)])
    attendance = IntegerField(label="Attendance", validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField(label="Add Student")

class DeleteForm(FlaskForm):
    submit = SubmitField(label="Delete")

# with app.app_context():
#     new_student = Students(name="Jaivik", roll_no="25BCE133", gender="Male", math_score=79, reading_score=45, writing_score=99, attendance=90)
#     db.session.add(new_student)
#     db.session.commit() this is for add students to database

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/students")
def students():
    form = DeleteForm()
    results = db.session.execute(db.select(Students)).scalars().all()

    for i in results:
        i.total_score = i.math_score + i.reading_score + i.writing_score
        i.avg_score = round(i.total_score / 3,2)
        i.performance_label = "Needs Improvement" if 0 <= i.avg_score < 70 else "Good" if 70 <= i.avg_score < 85 else "Excellent"

    return render_template("students.html",results=results, form=form)


@app.route("/add", methods=['GET', 'POST'])
def add():
    form = MyForm()
    if form.validate_on_submit():

        results = db.session.execute(db.select(Students)).scalars().all()
        arr = [i.roll_no.lower() for i in results]

        if form.roll_number.data.lower() in arr:
            form.roll_number.errors.append("Roll number already exists. Please enter a different roll number.")
            return render_template("add.html", form=form)
        else:
            new_student = Students(name=form.name.data, roll_no=form.roll_number.data, gender=form.gender.data,
                                   math_score=form.math_score.data, reading_score=form.reading_score.data,
                                   writing_score=form.writing_score.data, attendance=form.attendance.data)
            db.session.add(new_student)
            db.session.commit()
            return redirect(url_for("students"))

    return render_template("add.html", form=form)


@app.route("/edit/<int:id>", methods=['GET', 'POST'])
def edit(id):
    result = db.session.execute(db.select(Students).where(Students.id == id)).scalar()
    if result:
        form = MyForm()
        if request.method == "GET":
            form.name.data = result.name
            form.roll_number.data = result.roll_no
            form.gender.data = result.gender
            form.math_score.data = result.math_score
            form.reading_score.data = result.reading_score
            form.writing_score.data = result.writing_score
            form.attendance.data = result.attendance

        if form.validate_on_submit():

            all_results = db.session.execute(db.select(Students).where(Students.id != id)).scalars().all()
            arr = [i.roll_no.lower() for i in all_results]

            if form.roll_number.data.lower() in arr:
                form.roll_number.errors.append("Roll number already exists. Please enter a different roll number.")
                return render_template("edit.html", form=form, id=id, is_exists=True)
            else:
                result.name = form.name.data
                result.roll_no = form.roll_number.data
                result.gender = form.gender.data
                result.math_score = form.math_score.data
                result.reading_score = form.reading_score.data
                result.writing_score = form.writing_score.data
                result.attendance = form.attendance.data

                db.session.commit()
                return redirect(url_for("students"))

        return render_template("edit.html", form=form, is_exists=True, id=id)

    else:
        return render_template("edit.html", is_exists=False)


@app.route("/delete/<int:id>", methods=['POST'])
def delete(id):
    result = db.session.execute(db.select(Students).where(Students.id == id)).scalar()
    db.session.delete(result)
    db.session.commit()
    return redirect(url_for('students'))


@app.route("/student/<int:id>")
def detail(id):
    result = db.session.execute(db.select(Students).where(Students.id == id)).scalar()

    if result:
        result.total_score = result.math_score + result.reading_score + result.writing_score
        result.avg_score = round(result.total_score / 3, 2)
        result.performance_label = "Needs Improvement" if 0 <= result.avg_score < 70 else "Good" if 70 <= result.avg_score < 85 else "Excellent"

    return render_template("detail.html", result=result)


@app.route("/analytics")
def analytics():
    data_dict = {
        'total_students': 0,
        'main_marks_avg': 0,
        'excellent': 0,
        'good': 0,
        'needs_improvement': 0,
        'avg_attendance': 0,
        'below_75': 0,
        'above_and_75': 0,
        'top_students': [],
        'weak_students': [],
    }

    data = db.session.execute(db.select(Students)).scalars().all()
    main_marks_avg = 0
    main_attendance_avg = 0

    for i in data:
        i.total_score = i.math_score + i.reading_score + i.writing_score
        i.avg_score = round(i.total_score / 3, 2)
        main_marks_avg += i.avg_score
        main_attendance_avg += i.attendance

        if 0 <= i.avg_score < 70:
            i.performance_label = "Needs Improvement"
            data_dict['needs_improvement'] += 1
            data_dict['weak_students'].append(i)
        elif 70 <= i.avg_score < 85:
            i.performance_label = "Good"
            data_dict['good'] += 1
        else:
            i.performance_label = "Excellent"
            data_dict['excellent'] += 1

        if i.attendance < 75:
            data_dict['below_75'] += 1
        else:
            data_dict['above_and_75'] += 1

    data_dict['total_students'] = len(data)
    if data_dict['total_students'] == 0:
        return render_template("analytics.html", data=data_dict)

    main_marks_avg /= data_dict['total_students']
    main_marks_avg = round(main_marks_avg, 2)
    data_dict['main_marks_avg'] = main_marks_avg

    main_attendance_avg /= data_dict['total_students']
    main_attendance_avg = round(main_attendance_avg, 2)
    data_dict['avg_attendance'] = main_attendance_avg

    data.sort(key=lambda x: x.avg_score, reverse=True)

    if len(data) >= 5:
        data_dict['top_students'] = data[:5]
    else:
        data_dict['top_students'] = data

    print(data_dict)
    return render_template("analytics.html", data=data_dict)


if __name__ == "__main__":
    app.run(debug=True)