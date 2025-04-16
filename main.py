from flask import Flask, render_template, request, redirect, url_for
from Service.course_service import CourseService
from Service.user_service import UserService

app = Flask(__name__, template_folder='Views')

# Services
course_service = CourseService()
user_service = UserService()


@app.route('/')
def index():
    return render_template('home.html')


# ---------------- COURSES ----------------

@app.route('/courses')
def list_courses():
    courses = course_service.get_all()
    return render_template('courses/list.html', courses=courses)

@app.route('/courses/create', methods=['GET', 'POST'])
def create_course():
    if request.method == 'POST':
        name = request.form['name']
        ncr = request.form['ncr']
        course_service.create(name, ncr)
        return redirect(url_for('list_courses'))
    return render_template('courses/create.html')

@app.route('/courses/edit/<int:id>', methods=['GET', 'POST'])
def edit_course(id):
    course = course_service.get_by_id(id)
    if not course:
        return "Course not found", 404
    if request.method == 'POST':
        name = request.form['name']
        ncr = request.form['ncr']
        course_service.update(id, name, ncr)
        return redirect(url_for('list_courses'))
    return render_template('courses/edit.html', course=course)

@app.route('/courses/delete/<int:id>', methods=['POST'])
def delete_course(id):
    course_service.delete(id)
    return redirect(url_for('list_courses'))


# ---------------- PROFESSORS ----------------

@app.route('/professors')
def list_professors():
    professors = user_service.get_all_professors()
    return render_template('professors/list.html', professors=professors)

@app.route('/professors/create', methods=['GET', 'POST'])
def create_professor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user_service.create(name, email, is_professor=True)
        return redirect(url_for('list_professors'))
    return render_template('professors/create.html')

@app.route('/professors/edit/<int:id>', methods=['GET', 'POST'])
def edit_professor(id):
    professor = user_service.get_by_id(id)
    if not professor or not professor['Is_professor']:
        return "Professor not found", 404
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user_service.update(id, name, email)
        return redirect(url_for('list_professors'))
    return render_template('professors/edit.html', professor=professor)

@app.route('/professors/delete/<int:id>', methods=['POST'])
def delete_professor(id):
    user_service.delete(id)
    return redirect(url_for('list_professors'))


# ---------------- STUDENTS ----------------

@app.route('/students')
def list_students():
    students = user_service.get_all_students()
    return render_template('students/list.html', students=students)

@app.route('/students/create', methods=['GET', 'POST'])
def create_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        entry_date = request.form['entry_date']
        user_service.create(name, email, is_professor=False, entry_date=entry_date)
        return redirect(url_for('list_students'))
    return render_template('students/create.html')

@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = user_service.get_by_id(id)
    if not student or student['Is_professor']:
        return "Student not found", 404
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        entry_date = request.form['entry_date']
        user_service.update(id, name, email, entry_date)
        return redirect(url_for('list_students'))
    return render_template('students/edit.html', student=student)

@app.route('/students/delete/<int:id>', methods=['POST'])
def delete_student(id):
    user_service.delete(id)
    return redirect(url_for('list_students'))


#####################################
# RUN APP
#####################################

if __name__ == '__main__':
    app.run(debug=True)
