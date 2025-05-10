from flask import Flask, render_template, request, redirect, url_for, flash
from Service.course_service import CourseService
from Service.user_service import UserService
from Service.section_service import SectionService
from Service.course_taken_service import CourseTakenService
from Service.topic_service import TopicService

app = Flask(__name__, template_folder='Views')
app.secret_key = 'some-secret-key'  

course_service = CourseService()
user_service = UserService()
section_service = SectionService()
course_taken_service = CourseTakenService()
topic_service = TopicService()

@app.route('/')
def index():
    return render_template('home.html')

# ---------------- COURSES ----------------

@app.route('/courses')
def list_courses():
    courses = course_service.get_all()
    for course in courses:
        course['prerequisites'] = course_service.get_prerequisites(course['id'])
    return render_template('courses/list.html', courses=courses)

@app.route('/courses/create', methods=['GET', 'POST'])
def create_course():
    if request.method == 'POST':
        name = request.form['name']
        nrc = request.form['nrc']
        prerequisites = request.form.getlist('prerequisites')  
        course_service.create(name, nrc, prerequisites)
        return redirect(url_for('list_courses'))
    all_courses = course_service.get_all()
    return render_template('courses/create.html', all_courses=all_courses)

@app.route('/courses/edit/<int:id>', methods=['GET', 'POST'])
def edit_course(id):
    course = course_service.get_by_id(id)
    if not course:
        return "Course not found", 404
    all_courses = [c for c in course_service.get_all() if c['id'] != course['id']]
    current_prerequisites = course_service.get_prerequisites(id)
    if request.method == 'POST':
        name = request.form['name']
        nrc = request.form['nrc']
        prerequisites = request.form.getlist('prerequisites')  
        course_service.update(id, name, nrc, prerequisites)
        return redirect(url_for('list_courses'))
    return render_template('courses/edit.html', course=course, all_courses=all_courses, current_prerequisites=[c['id'] for c in current_prerequisites])

@app.route('/courses/delete/<int:id>', methods=['POST'])
def delete_course(id):
    course_service.delete(id)
    return redirect(url_for('list_courses'))

# ---------------- TOPICS ----------------

@app.route('/courses/<int:course_id>/sections/<int:section_id>/topics')
def list_topics(course_id, section_id):
    topics = topic_service.get_by_section_id(section_id)
    section = section_service.get_by_id(section_id)
    return render_template('topics/list.html', topics=topics, section=section)

@app.route('/courses/<int:course_id>/sections/<int:section_id>/topics/create', methods=['GET', 'POST'], endpoint='create_topic')
def create_topic(course_id, section_id):
    if request.method == 'POST':
        name = request.form['name']
        weight = request.form['weight']
        weight_or_percentage = 'weight_or_percentage' in request.form  

        if weight_or_percentage:
            total_percentage = topic_service.calculate_total_percentage(section_id)
            if total_percentage + int(weight) > 100:
                flash("Total percentage cannot exceed 100%")
                return redirect(url_for('create_topic', course_id=course_id, section_id=section_id)) 

        topic_service.create(name, section_id, weight, weight_or_percentage)
        return redirect(url_for('list_topics', course_id=course_id, section_id=section_id))

    return render_template('topics/create.html', course_id=course_id, section_id=section_id)

@app.route('/topics/edit/<int:id>', methods=['GET', 'POST'])
def edit_topic(id):
    topic = topic_service.get_by_id(id)
    if not topic:
        return "Topic not found", 404

    if request.method == 'POST':
        name = request.form['name']
        weight = request.form['weight']
        weight_or_percentage = 'weight_or_percentage' in request.form  

        if weight_or_percentage:
            total_percentage = topic_service.calculate_total_percentage(topic['section_id'])
            if total_percentage + int(weight) > 100:
                flash("Total percentage cannot exceed 100%")
                return redirect(url_for('edit_topic', id=id)) 

        topic_service.update(id, name, weight, weight_or_percentage)
        return redirect(url_for('list_topics', course_id=topic['course_id'], section_id=topic['section_id']))

    return render_template('topics/edit.html', topic=topic)

@app.route('/topics/delete/<int:id>', methods=['POST'])
def delete_topic(id):
    topic = topic_service.get_by_id(id)
    if topic:
        section_id = topic['section_id']
        course_id = topic['course_id']
        topic_service.delete(id)
        return redirect(url_for('list_topics', course_id=course_id, section_id=section_id))
    return "Topic not found", 404

# ---------------- SECTIONS ----------------

@app.route('/courses/<int:course_id>/sections')
def list_sections(course_id):
    sections = section_service.get_by_course_id(course_id)  
    course = course_service.get_by_id(course_id)  
    students = user_service.get_all(is_professor=False)  
    return render_template('sections/list.html', sections=sections, course=course, students=students)


@app.route('/courses/<int:course_id>/sections/create', methods=['GET', 'POST'])
def create_section(course_id):
    if request.method == 'POST':
        period = request.form['period']
        number = request.form['number']
        professor_id = request.form['professor_id']
        weight_or_percentage = 'weight_or_percentage' in request.form  

        section_service.create(course_id, period, number, professor_id, weight_or_percentage)
        return redirect(url_for('list_sections', course_id=course_id))

    professors = user_service.get_all(is_professor=True)
    course = course_service.get_by_id(course_id)
    return render_template('sections/create.html', course=course, professors=professors)


@app.route('/sections/edit/<int:section_id>', methods=['GET', 'POST'])
def edit_section(section_id):
    section = section_service.get_by_id(section_id)
    if not section:
        return "Section not found", 404

    course = course_service.get_by_id(section['course_id'])
    if not course:
        return "Course not found", 404

    professors = user_service.get_all(is_professor=True)

    if request.method == 'POST':
        period = request.form['period']
        number = request.form['number']
        professor_id = request.form['professor_id']
        weight_or_percentage = 'weight_or_percentage' in request.form  

        section_service.update(section_id, course['id'], period, number, professor_id, weight_or_percentage)
        return redirect(url_for('list_sections', course_id=course['id']))

    return render_template('sections/edit.html', section=section, course=course, professors=professors)


@app.route('/sections/delete/<int:section_id>', methods=['POST'])
def delete_section(section_id):
    section = section_service.get_by_id(section_id)
    if section:
        course_id = section['course_id']
        section_service.delete(section_id)
        return redirect(url_for('list_sections', course_id=course_id))
    return "Section not found", 404

# ---------------- ENROLLMENT ----------------

@app.route('/courses/<int:course_id>/sections/<int:section_id>/enroll', methods=['POST'])
def enroll_student_in_section(course_id, section_id):
    user_id = request.form['user_id']  
    course_taken_service.enroll_student(user_id, course_id, section_id)  
    return redirect(url_for('list_sections', course_id=course_id))

@app.route('/courses/<int:course_id>/sections/<int:section_id>/unenroll/<int:user_id>', methods=['POST'])
def unenroll_student_from_section(course_id, section_id, user_id):
    course_service.unenroll_student_from_section(course_id, section_id, user_id)
    
    return redirect(url_for('list_students_in_section', course_id=course_id, section_id=section_id))

@app.route('/courses/<int:course_id>/sections/<int:section_id>/students')
def list_students_in_section(course_id, section_id):
    course = course_service.get_by_id(course_id)  
    section = section_service.get_by_id(section_id)  
    enrollments = course_service.get_enrollments_in_section(section_id)  
    return render_template('sections/students_in_section.html', 
                           course=course, section=section, enrollments=enrollments)

# ---------------- PROFESSORS ----------------

@app.route('/professors')
def list_professors():
    professors = user_service.get_all(is_professor=True)
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
    if not professor or not professor['is_professor']:
        return "Professor not found", 404
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user_service.update(id, name, email, is_professor=True)
        return redirect(url_for('list_professors'))
    return render_template('professors/edit.html', professor=professor)

@app.route('/professors/delete/<int:id>', methods=['POST'])
def delete_professor(id):
    user_service.delete(id)
    return redirect(url_for('list_professors'))

# ---------------- STUDENTS ----------------

@app.route('/students')
def list_students():
    students = user_service.get_all(is_professor=False)
    return render_template('students/list.html', students=students)

@app.route('/students/create', methods=['GET', 'POST'])
def create_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        admission_date = request.form['admission_date']      
        user_service.create(name, email, False, admission_date)  
        return redirect(url_for('list_students'))
    return render_template('students/create.html')

@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = user_service.get_by_id(id)
    if not student or student['is_professor']:
        return "Student not found", 404
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        admission_date = request.form['admission_date']      
        user_service.update(id, name, email, False, admission_date)  
        return redirect(url_for('list_students'))
    return render_template('students/edit.html', student=student)

@app.route('/students/delete/<int:id>', methods=['POST'])
def delete_student(id):
    user_service.delete(id)
    return redirect(url_for('list_students'))

if __name__ == '__main__':
    app.run(debug=True)

