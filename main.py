from flask import Flask, render_template, request, redirect, url_for, flash
from Service.course_service import CourseService
from Service.user_service import UserService
from Service.section_service import SectionService
from Service.course_taken_service import CourseTakenService
from Service.topic_service import TopicService
from Service.activity_service import ActivityService

app = Flask(__name__, template_folder='Views')
app.secret_key = 'some-secret-key'  

course_service = CourseService()
user_service = UserService()
section_service = SectionService()
course_taken_service = CourseTakenService()
topic_service = TopicService()
activity_service = ActivityService()

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
    section['course_id'] = course_id
    section['course_name'] = course_service.get_by_id(course_id)['name']
    return render_template('topics/list.html', topics=topics, section=section)

@app.route('/courses/<int:course_id>/sections/<int:section_id>/topics/create', methods=['GET', 'POST'], endpoint='create_topic')
def create_topic(course_id, section_id):
    section = section_service.get_by_id(section_id)
    topics = topic_service.get_by_section_id(section_id)

    if request.method == 'POST':
        name = request.form['name']
        weight_or_percentage = 'weight_or_percentage' in request.form

        try:
            weight = int(request.form['weight'])  
        except (KeyError, ValueError):
            flash("Invalid value for weight/percentage")
            return redirect(url_for('create_topic', course_id=course_id, section_id=section_id))
        topic_service.create(name, section_id, weight, weight_or_percentage)

        if section['weight_or_percentage']:
            for topic in topics:
                key = f'percentages_{topic["id"]}'
                if key in request.form:
                    try:
                        updated_weight = int(request.form[key])
                        topic_service.update(topic['id'], topic['name'], updated_weight, topic['weight_or_percentage'])
                    except ValueError:
                        flash(f"Invalid percentage for topic '{topic['name']}'")
                        return redirect(url_for('create_topic', course_id=course_id, section_id=section_id))

        return redirect(url_for('list_sections', course_id=course_id))

    return render_template('topics/create.html', course_id=course_id, section_id=section_id, section=section, topics=topics)

@app.route('/topics/edit/<int:id>', methods=['GET', 'POST'])
def edit_topic(id):
    topic = topic_service.get_by_id(id)
    if not topic:
        return "Topic not found", 404

    section = section_service.get_by_id(topic['section_id'])
    topics = topic_service.get_by_section_id(section['id'])

    if request.method == 'POST':
        name = request.form['name']
        weight = int(request.form['weight'])
        weight_or_percentage = 'weight_or_percentage' in request.form
        topic_service.update(id, name, weight, weight_or_percentage)

        if section['weight_or_percentage']:
            for t in topics:
                if t['id'] == topic['id']:
                    continue  
                key = f'percentages_{t["id"]}'
                if key in request.form:
                    try:
                        updated_weight = int(request.form[key])
                        topic_service.update(t['id'], t['name'], updated_weight, t['weight_or_percentage'])
                    except ValueError:
                        flash(f"Invalid percentage for topic '{t['name']}'")
                        return redirect(url_for('edit_topic', id=id))

        return redirect(url_for('list_sections', course_id=section['course_id']))

    return render_template(
        'topics/edit.html',
        topic=topic,
        section=section,
        topics=topics
    )

@app.post('/topics/delete/<int:id>')
def delete_topic_direct(id):
    topic = topic_service.get_by_id(id)
    if not topic:
        return "Topic not found", 404

    section = section_service.get_by_id(topic['section_id'])
    topic_service.delete(id)
    return redirect(url_for('list_sections', course_id=section['course_id']))

@app.route('/topics/delete/percentage/<int:id>', methods=['GET', 'POST'])
def delete_topic_percentage_view(id):
    topic = topic_service.get_by_id(id)
    if not topic:
        return "Topic not found", 404

    section = section_service.get_by_id(topic['section_id'])
    topics = topic_service.get_by_section_id(section['id'])
    remaining_topics = [t for t in topics if t['id'] != id]

    if request.method == 'POST':
        try:
            for t in remaining_topics:
                new_weight = int(request.form[f'percentages_{t["id"]}'])
                topic_service.update(t['id'], t['name'], new_weight, t['weight_or_percentage'])

            topic_service.delete(id)
            return redirect(url_for('list_sections', course_id=section['course_id']))
        except ValueError:
            flash("Invalid input. All percentages must be numbers.")
            return redirect(request.url)

    return render_template(
        'topics/delete_percentage.html',
        topic=topic,
        section=section,
        topics=remaining_topics
    )

# ---------------- SECTIONS ----------------
@app.route('/courses/<int:course_id>/sections')
def list_sections(course_id):
    sections = section_service.get_by_course_id(course_id)
    course = course_service.get_by_id(course_id)
    students = user_service.get_all(is_professor=False)

    for section in sections:
        topics = topic_service.get_by_section_id(section['id'])
        section['topics'] = []
        for topic in topics:
            section['topics'].append({
                'id': topic['id'],         
                'name': topic['name'],
                'value': topic['weight'],
                'weight_or_percentage': topic.get('weight_or_percentage', False)  
            })

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

# ---------------- ACTIVITIES ----------------

@app.route('/topics/<int:topic_id>/activities')
def list_activities(topic_id):
    topic = topic_service.get_by_id(topic_id)
    if not topic:
        return "Topic not found", 404
    
    activities = activity_service.get_by_topic_id(topic_id)
    section = section_service.get_by_id(topic['section_id'])
    course = course_service.get_by_id(section['course_id'])
    
    return render_template(
        'activities/list.html',
        activities=activities,
        topic=topic,
        section=section,
        course=course
    )

@app.route('/topics/<int:topic_id>/activities/create', methods=['GET', 'POST'])
def create_activity(topic_id):
    topic = topic_service.get_by_id(topic_id)
    if not topic:
        return "Topic not found", 404
    
    section = section_service.get_by_id(topic['section_id'])
    course = course_service.get_by_id(section['course_id'])
    activities = activity_service.get_by_topic_id(topic_id)
    
    if request.method == 'POST':
        name = request.form['name']
        optional_flag = 'optional' in request.form
        
        try:
            weight = int(request.form['weight'])
        except (KeyError, ValueError):
            flash("Invalid value for weight/percentage")
            return redirect(url_for('create_activity', topic_id=topic_id))
        
        activity_service.create(name, topic_id, weight, optional_flag)
        
        if topic['weight_or_percentage']:
            for activity in activities:
                key = f'percentages_{activity["id"]}'
                if key in request.form:
                    try:
                        updated_weight = int(request.form[key])
                        activity_service.update(activity['id'], activity['name'], updated_weight, activity['optional_flag'])
                    except ValueError:
                        flash(f"Invalid percentage for activity '{activity['name']}'")
                        return redirect(url_for('create_activity', topic_id=topic_id))
        
        return redirect(url_for('list_activities', topic_id=topic_id))
    
    return render_template(
        'activities/create.html',
        topic=topic,
        section=section,
        course=course,
        activities=activities
    )

@app.route('/activities/edit/<int:id>', methods=['GET', 'POST'])
def edit_activity(id):
    activity = activity_service.get_by_id(id)
    if not activity:
        return "Activity not found", 404
    
    topic = topic_service.get_by_id(activity['topic_id'])
    if not topic:
        return "Topic not found", 404
    
    section = section_service.get_by_id(topic['section_id'])
    course = course_service.get_by_id(section['course_id'])
    activities = activity_service.get_by_topic_id(topic['id'])
    
    if request.method == 'POST':
        name = request.form['name']
        optional_flag = 'optional' in request.form
        
        try:
            weight = int(request.form['weight'])
        except (KeyError, ValueError):
            flash("Invalid value for weight/percentage")
            return redirect(url_for('edit_activity', id=id))
        
        activity_service.update(id, name, weight, optional_flag)
        
        if topic['weight_or_percentage']:
            for act in activities:
                if act['id'] == activity['id']:
                    continue  
                
                key = f'percentages_{act["id"]}'
                if key in request.form:
                    try:
                        updated_weight = int(request.form[key])
                        activity_service.update(act['id'], act['name'], updated_weight, act['optional_flag'])
                    except ValueError:
                        flash(f"Invalid percentage for activity '{act['name']}'")
                        return redirect(url_for('edit_activity', id=id))
        
        return redirect(url_for('list_activities', topic_id=topic['id']))
    
    return render_template(
        'activities/edit.html',
        activity=activity,
        topic=topic,
        section=section,
        course=course,
        activities=activities
    )

@app.post('/activities/delete/<int:id>')
def delete_activity_direct(id):

    activity = activity_service.get_by_id(id)
    if not activity:
        return "Activity not found", 404
    
    topic = topic_service.get_by_id(activity['topic_id'])
    activity_service.delete(id)
    
    return redirect(url_for('list_activities', topic_id=topic['id']))

@app.route('/activities/delete/percentage/<int:id>', methods=['GET', 'POST'])
def delete_activity_percentage_view(id):
    activity = activity_service.get_by_id(id)
    if not activity:
        return "Activity not found", 404
    
    topic = topic_service.get_by_id(activity['topic_id'])
    if not topic:
        return "Topic not found", 404
    
    section = section_service.get_by_id(topic['section_id'])
    activities = activity_service.get_by_topic_id(topic['id'])
    remaining_activities = [a for a in activities if a['id'] != id]
    
    if request.method == 'POST':
        try:
            for act in remaining_activities:
                new_weight = int(request.form[f'percentages_{act["id"]}'])
                activity_service.update(act['id'], act['name'], new_weight, act['optional_flag'])
            
            activity_service.delete(id)
            
            return redirect(url_for('list_activities', topic_id=topic['id']))
        except ValueError:
            flash("Invalid input. All percentages must be numbers.")
            return redirect(request.url)
    
    return render_template(
        'activities/delete_percentage.html',
        activity=activity,
        topic=topic,
        section=section,
        activities=remaining_activities,
        course=course_service.get_by_id(section['course_id'])
    )
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




# ---------------- Uploads ----------------


from Service.Import_service import ImportService

import_service = ImportService()


@app.route('/import', methods=['GET', 'POST'])
def import_data():
    file_types = [
        'alumnos',
        'profesores',
        'cursos',
        'instancias_cursos',
        'instancias_cursos_secciones',
        'alumnos_seccion',
        'notas_alumnos',
        'salas_clases'
    ]

    if request.method == 'POST':
        uploaded_file = request.files.get('json_file')
        selected_type = request.form.get('data_type')

        if not uploaded_file or not selected_type:
            flash("Please select a file and a file type.")
            return redirect(request.url)

        try:
            import_service.import_json(uploaded_file, selected_type)
            flash(f"Datos importados exitosamente como {selected_type}.")
        except Exception as e:
            flash(f"Error al importar datos: {str(e)}")

        return redirect(url_for('import_data'))

    return render_template('import/upload.html', file_types=file_types)



if __name__ == '__main__':
    app.run(debug=True)
