"""Academic Management System (SGA) - Main Flask Application.

This module implements a comprehensive academic management system with CRUD operations
for courses, professors, students, instances, sections, topics, activities, and grades.
"""

# Static analysis error fixing: import order and unused import
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from Service.course_service import CourseService
from Service.user_service import UserService
from Service.section_service import SectionService
from Service.course_taken_service import CourseTakenService
from Service.topic_service import TopicService
from Service.activity_service import ActivityService
from Service.import_service import ImportService
from Service.instance_service import InstanceService
from Service.room_service import RoomService
from Service.grade_service import GradeService
from Service.schedule_service import ScheduleService

app = Flask(__name__, template_folder='Views')
app.secret_key = 'some-secret-key'

course_service = CourseService()
user_service = UserService()
section_service = SectionService()
course_taken_service = CourseTakenService()
topic_service = TopicService()
activity_service = ActivityService()
import_service = ImportService()
instance_service = InstanceService()
room_service = RoomService()
grade_service = GradeService()
schedule_service = ScheduleService()


@app.route('/')
def index():
    """Render home page."""
    return render_template('home.html')


# ---------------- COURSES ----------------

@app.route('/courses')
def list_courses():
    """List all courses with their prerequisites and instances."""
    courses = course_service.get_all()
    for course in courses:
        course['prerequisites'] = course_service.get_prerequisites(
            course['id'])
        course['instances'] = instance_service.get_by_course_id(
            course['id'])
    return render_template('courses/list.html', courses=courses)


@app.route('/courses/create', methods=['GET', 'POST'])
def create_course():
    """Create a new course."""
    if request.method == 'POST':
        name = request.form['name']
        nrc = request.form['nrc']
        # Static analysis error fixing: renamed parameter
        course_credits = int(request.form.get('credits', 0))
        prerequisites = request.form.getlist('prerequisites')
        course_service.create(name, nrc, course_credits, prerequisites)
        return redirect(url_for('list_courses'))
    all_courses = course_service.get_all()
    return render_template('courses/create.html', all_courses=all_courses)


# ----- solution ONE LEVEL OF ABSTRACTION error ---
def _get_edit_course_context(course_id):
    """Get context data for editing a course."""
    course = course_service.get_by_id(course_id)
    if not course:
        return None, None, None

    all_courses = [c for c in course_service.get_all()
                   if c['id'] != course['id']]
    current_prerequisites = course_service.get_prerequisites(course_id)

    return course, all_courses, current_prerequisites


def _process_course_update(course_id):
    """Process course update form data."""
    name = request.form['name']
    nrc = request.form['nrc']
    # Static analysis error fixing: renamed parameter
    course_credits = int(request.form.get('credits', 0))
    prerequisites = request.form.getlist('prerequisites')

    course_service.update(course_id, name, nrc, course_credits,
                          prerequisites)


# Static analysis error fixing: renamed parameter id to course_id
@app.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    """Edit an existing course."""
    course, all_courses, current_prerequisites = _get_edit_course_context(
        course_id)
    if not course:
        return "Course not found", 404

    if request.method == 'POST':
        _process_course_update(course_id)
        return redirect(url_for('list_courses'))

    return render_template('courses/edit.html',
                           course=course,
                           all_courses=all_courses,
                           current_prerequisites=[c['id'] for c in
                                                  current_prerequisites])


# ----- solution ONE LEVEL OF ABSTRACTION error ---

# Static analysis error fixing: renamed parameter id to course_id
@app.route('/courses/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    """Delete a course."""
    course_service.delete(course_id)
    return redirect(url_for('list_courses'))


# ---------------- TOPICS ----------------

@app.route('/instances/<int:instance_id>/sections/<int:section_id>/topics')
def list_topics(instance_id, section_id):
    """List topics for a specific section."""
    topics = topic_service.get_by_section_id(section_id)
    section = section_service.get_by_id(section_id)

    if section['instance_id'] != instance_id:
        return "Invalid instance ID for this section", 400

    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])

    section['course_id'] = course['id']
    section['course_name'] = course['name']
    section['period'] = instance['period']

    return render_template('topics/list.html', topics=topics,
                           section=section, instance=instance)


@app.route('/instances/<int:instance_id>/sections/<int:section_id>/topics/'
           'create', methods=['GET', 'POST'], endpoint='create_topic')
def create_topic(instance_id, section_id):
    """Create a new topic for a section."""
    section = section_service.get_by_id(section_id)

    if section['instance_id'] != instance_id:
        return "Invalid instance ID for this section", 400

    topics = topic_service.get_by_section_id(section_id)

    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])

    if request.method == 'POST':
        name = request.form['name']
        weight_or_percentage = 'weight_or_percentage' in request.form

        try:
            weight = int(request.form['weight'])
        except (KeyError, ValueError):
            flash("Invalid value for weight/percentage", "danger")
            return redirect(url_for('create_topic', instance_id=instance_id,
                                    section_id=section_id))

        topic_service.create(name, section_id, weight, weight_or_percentage)
        flash(f"Topic '{name}' created successfully.", "success")

        if section['weight_or_percentage']:
            for topic in topics:
                key = f'percentages_{topic["id"]}'
                if key in request.form:
                    try:
                        updated_weight = int(request.form[key])
                        topic_service.update(topic['id'], topic['name'],
                                             updated_weight,
                                             topic['weight_or_percentage'])
                    except ValueError:
                        flash(f"Invalid percentage for topic "
                              f"'{topic['name']}'", "danger")
                        return redirect(url_for('create_topic',
                                                instance_id=instance_id,
                                                section_id=section_id))

        return redirect(url_for('list_sections', instance_id=instance_id))

    return render_template('topics/create.html',
                           instance_id=instance_id,
                           section_id=section_id,
                           section=section,
                           topics=topics,
                           course=course,
                           instance=instance)


# Static analysis error fixing: renamed parameter id to topic_id
@app.route('/topics/edit/<int:topic_id>', methods=['GET', 'POST'])
def edit_topic(topic_id):
    """Edit an existing topic."""
    topic = topic_service.get_by_id(topic_id)
    if not topic:
        return "Topic not found", 404

    section = section_service.get_by_id(topic['section_id'])
    topics = topic_service.get_by_section_id(section['id'])

    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])

    if request.method == 'POST':
        name = request.form['name']
        try:
            weight = int(request.form['weight'])
            weight_or_percentage = 'weight_or_percentage' in request.form
            topic_service.update(topic_id, name, weight, weight_or_percentage)

            flash(f"Topic '{name}' updated successfully.", "success")

            if section['weight_or_percentage']:
                for t in topics:
                    if t['id'] == topic['id']:
                        continue
                    key = f'percentages_{t["id"]}'
                    if key in request.form:
                        try:
                            updated_weight = int(request.form[key])
                            topic_service.update(t['id'], t['name'],
                                                 updated_weight,
                                                 t['weight_or_percentage'])
                        except ValueError:
                            flash(f"Invalid percentage for topic "
                                  f"'{t['name']}'", "danger")
                            return redirect(url_for('edit_topic',
                                                    topic_id=topic_id))
        except ValueError:
            flash("Invalid weight value. Please enter a valid number.",
                  "danger")
            return redirect(url_for('edit_topic', topic_id=topic_id))

        return redirect(url_for('list_sections',
                                instance_id=section['instance_id']))

    return render_template(
        'topics/edit.html',
        topic=topic,
        section=section,
        topics=topics,
        course=course,
        instance=instance
    )


# Static analysis error fixing: renamed parameter id to topic_id
@app.post('/topics/delete/<int:topic_id>')
def delete_topic_direct(topic_id):
    """Delete a topic directly."""
    topic = topic_service.get_by_id(topic_id)
    if not topic:
        return "Topic not found", 404

    section = section_service.get_by_id(topic['section_id'])
    instance = instance_service.get_by_id(section['instance_id'])

    topic_name = topic['name']
    topic_service.delete(topic_id)
    flash(f"Topic '{topic_name}' deleted successfully.", "success")

    return redirect(url_for('list_sections', instance_id=instance['id']))


# ----- solution ONE LEVEL OF ABSTRACTION error ---
def _get_delete_topic_context(topic_id):
    """Get context data for deleting a topic."""
    topic = topic_service.get_by_id(topic_id)
    if not topic:
        return None, None, None, None, None

    section = section_service.get_by_id(topic['section_id'])
    topics = topic_service.get_by_section_id(section['id'])
    remaining_topics = [t for t in topics if t['id'] != topic_id]
    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])

    return topic, section, remaining_topics, instance, course


def _update_remaining_topics_percentages(remaining_topics):
    """Update percentages for remaining topics."""
    for t in remaining_topics:
        new_weight = int(request.form[f'percentages_{t["id"]}'])
        topic_service.update(t['id'], t['name'], new_weight,
                             t['weight_or_percentage'])


def _delete_topic_and_redirect(topic_id, topic_name, instance_id):
    """Delete topic and redirect to sections list."""
    topic_service.delete(topic_id)
    flash(f"Topic '{topic_name}' deleted successfully and percentages "
          "redistributed.", "success")
    return redirect(url_for('list_sections', instance_id=instance_id))


# Static analysis error fixing: renamed parameter id to topic_id
@app.route('/topics/delete/percentage/<int:topic_id>',
           methods=['GET', 'POST'])
def delete_topic_percentage_view(topic_id):
    """Delete a topic with percentage redistribution."""
    topic, section, remaining_topics, instance, course = (
        _get_delete_topic_context(topic_id))
    if not topic:
        return "Topic not found", 404

    if request.method == 'POST':
        try:
            _update_remaining_topics_percentages(remaining_topics)
            return _delete_topic_and_redirect(topic_id, topic['name'],
                                               instance['id'])
        except ValueError:
            flash("Invalid input. All percentages must be numbers.",
                  "danger")
            return redirect(request.url)

    return render_template(
        'topics/delete_percentage.html',
        topic=topic,
        section=section,
        topics=remaining_topics,
        course=course,
        instance=instance
    )


# ----- solution ONE LEVEL OF ABSTRACTION error ---

# ---------------- INSTANCES ----------------

# ----- solution ONE LEVEL OF ABSTRACTION error ---
def _enrich_instances_with_sections(instances):
    """Add section data to instances."""
    for instance in instances:
        instance['sections'] = section_service.get_by_instance_id(
            instance['id'])


def _get_instances_list_data(course_id):
    """Get data for instances list page."""
    instances = instance_service.get_by_course_id(course_id)
    course = course_service.get_by_id(course_id)
    _enrich_instances_with_sections(instances)
    return instances, course


@app.route('/courses/<int:course_id>/instances')
def list_instances(course_id):
    """List instances for a course."""
    instances, course = _get_instances_list_data(course_id)
    return render_template('instances/list.html', instances=instances,
                           course=course)


# ----- solution ONE LEVEL OF ABSTRACTION error ---

# ----- solution ONE LEVEL OF ABSTRACTION error ---
def _validate_course_exists(course_id):
    """Validate that a course exists."""
    course = course_service.get_by_id(course_id)
    if not course:
        return None, "Course not found", 404
    return course, None, None


def _handle_instance_creation(course_id, course):
    """Handle the creation of a new instance."""
    period = request.form['period']
    existing_instance = instance_service.get_by_course_and_period(
        course_id, period)

    if existing_instance:
        flash(f"An instance for course {course['name']} in period "
              f"{period} already exists.")
        return redirect(url_for('list_instances', course_id=course_id))

    instance_service.create(course_id, period)
    flash(f"Instance created for course {course['name']} in period "
          f"{period}.")
    return redirect(url_for('list_instances', course_id=course_id))


def _get_create_instance_context(course_id, course):
    """Get context for creating an instance."""
    instances = instance_service.get_by_course_id(course_id)
    course_periods = [instance['period'] for instance in instances]

    return render_template('instances/create.html',
                           course=course,
                           course_periods=course_periods)


@app.route('/courses/<int:course_id>/instances/create',
           methods=['GET', 'POST'])
def create_instance(course_id):
    """Create a new instance for a course."""
    course, error_msg, error_code = _validate_course_exists(course_id)
    if error_msg:
        return error_msg, error_code

    if request.method == 'POST':
        return _handle_instance_creation(course_id, course)

    return _get_create_instance_context(course_id, course)


# ----- solution ONE LEVEL OF ABSTRACTION error ---

@app.route('/instances/<int:instance_id>/edit', methods=['GET', 'POST'])
def edit_instance(instance_id):
    """Edit an existing instance."""
    instance = instance_service.get_by_id(instance_id)
    if not instance:
        return "Instance not found", 404

    course = course_service.get_by_id(instance['course_id'])

    if request.method == 'POST':
        period = request.form['period']

        existing_instance = instance_service.get_by_course_and_period(
            instance['course_id'], period)
        if existing_instance and existing_instance['id'] != instance_id:
            flash(f"An instance for course {course['name']} in period "
                  f"{period} already exists.")
            return redirect(url_for('edit_instance',
                                    instance_id=instance_id))

        instance_service.update(instance_id, period)
        flash(f"Instance updated for course {course['name']} in period "
              f"{period}.")
        return redirect(url_for('list_instances',
                                course_id=instance['course_id']))

    periods = instance_service.get_periods()

    return render_template('instances/edit.html', instance=instance,
                           course=course, periods=periods)


@app.route('/instances/<int:instance_id>/delete', methods=['POST'])
def delete_instance(instance_id):
    """Delete an instance."""
    instance = instance_service.get_by_id(instance_id)
    if not instance:
        return "Instance not found", 404

    course_id = instance['course_id']

    section_count = instance_service.get_section_count(instance_id)
    if section_count > 0:
        flash(f"Cannot delete instance with {section_count} sections. "
              "Delete all sections first.")
        return redirect(url_for('list_instances', course_id=course_id))

    instance_service.delete(instance_id)
    flash("Instance deleted successfully.")
    return redirect(url_for('list_instances', course_id=course_id))


# ---------------- SECTIONS ----------------
# ----- solution ONE LEVEL OF ABSTRACTION error ---
def _validate_instance_exists(instance_id):
    """Validate that an instance exists."""
    instance = instance_service.get_by_id(instance_id)
    if not instance:
        return None, "Instance not found", 404
    return instance, None, None


def _get_sections_list_basic_data(instance):
    """Get basic data for sections list."""
    course_id = instance['course_id']
    course = course_service.get_by_id(course_id)
    sections = section_service.get_by_instance_id(instance['id'])
    students = user_service.get_all(is_professor=False)

    return course, sections, students


def _enrich_section_with_topics(section):
    """Add topic data to a section."""
    topics = topic_service.get_by_section_id(section['id'])
    section['topics'] = []
    for topic in topics:
        section['topics'].append({
            'id': topic['id'],
            'name': topic['name'],
            'value': topic['weight'],
            'weight_or_percentage': topic.get('weight_or_percentage', False)
        })


def _enrich_sections_with_topics(sections):
    """Add topic data to all sections."""
    for section in sections:
        _enrich_section_with_topics(section)


@app.route('/instances/<int:instance_id>/sections')
def list_sections(instance_id):
    """List sections for an instance."""
    instance, error_msg, error_code = _validate_instance_exists(instance_id)
    if error_msg:
        return error_msg, error_code

    course, sections, students = _get_sections_list_basic_data(instance)
    _enrich_sections_with_topics(sections)

    return render_template('sections/list.html',
                           sections=sections,
                           course=course,
                           instance=instance,
                           students=students)


# ----- solution ONE LEVEL OF ABSTRACTION error ---

@app.route('/instances/<int:instance_id>/sections/create',
           methods=['GET', 'POST'])
def create_section(instance_id):
    """Create a new section for an instance."""
    instance = instance_service.get_by_id(instance_id)
    if not instance:
        return "Instance not found", 404

    course_id = instance['course_id']
    course = course_service.get_by_id(course_id)

    if request.method == 'POST':
        number = request.form['number']
        professor_id = request.form['professor_id']
        weight_or_percentage = 'weight_or_percentage' in request.form

        if section_service.section_number_exists(instance_id, number):
            flash(f"Section number {number} already exists for this "
                  "instance.", "danger")
            professors = user_service.get_all(is_professor=True)
            return render_template('sections/create.html',
                                   course=course,
                                   instance=instance,
                                   professors=professors)

        section_service.create(instance_id, number, professor_id,
                               weight_or_percentage)
        flash(f"Section {number} created successfully.", "success")
        return redirect(url_for('list_sections', instance_id=instance_id))

    professors = user_service.get_all(is_professor=True)
    return render_template('sections/create.html',
                           course=course,
                           instance=instance,
                           professors=professors)


@app.route('/sections/edit/<int:section_id>', methods=['GET', 'POST'])
def edit_section(section_id):
    """Edit an existing section."""
    section = section_service.get_by_id(section_id)
    if not section:
        return "Section not found", 404

    instance_id = section['instance_id']
    instance = instance_service.get_by_id(instance_id)
    if not instance:
        return "Instance not found", 404

    course_id = instance['course_id']
    course = course_service.get_by_id(course_id)

    professors = user_service.get_all(is_professor=True)

    if request.method == 'POST':
        number = request.form['number']
        professor_id = request.form['professor_id']
        weight_or_percentage = 'weight_or_percentage' in request.form

        if section_service.section_number_exists(instance_id, number,
                                                  exclude_section_id=section_id):
            flash(f"Section number {number} already exists for this "
                  "instance.", "danger")
            return render_template('sections/edit.html',
                                   section=section,
                                   course=course,
                                   instance=instance,
                                   professors=professors)

        section_service.update(section_id, number, professor_id,
                               weight_or_percentage)
        flash(f"Section {number} updated successfully.", "success")
        return redirect(url_for('list_sections', instance_id=instance_id))

    return render_template('sections/edit.html',
                           section=section,
                           course=course,
                           instance=instance,
                           professors=professors)


@app.route('/sections/delete/<int:section_id>', methods=['POST'])
def delete_section(section_id):
    """Delete a section."""
    section = section_service.get_by_id(section_id)
    if section:
        instance_id = section['instance_id']
        section_service.delete(section_id)
        return redirect(url_for('list_sections', instance_id=instance_id))
    return "Section not found", 404


# ----- solution FUNCTION SIZE and ONE LEVEL OF ABSTRACTION error ---
def _validate_student_and_section(section_id, user_id):
    """Validate that both student and section exist."""
    section = section_service.get_by_id(section_id)
    if not section:
        return None, None, "Section not found", 404

    student = user_service.get_by_id(user_id)
    if not student:
        return None, None, "Student not found", 404

    return section, student, None, None


def _get_grade_calculation_context(section):
    """Get context data for grade calculation."""
    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])
    topics = topic_service.get_by_section_id(section['id'])

    return instance, course, topics


def _calculate_activity_contribution(activity, topic, user_id):
    """Calculate an activity's contribution to the topic grade."""
    grade = grade_service.get_by_activity_and_student(activity['id'], user_id)

    activity_calculation = {
        'activity': activity,
        'grade': None,
        'contribution': 0
    }

    if grade:
        activity_calculation['grade'] = float(grade['grade'])
        grade_value = float(grade['grade'])
    elif activity['optional_flag']:
        return activity_calculation, 0, 0, True
    else:
        activity_calculation['grade'] = 1.0
        grade_value = 1.0

    if topic['weight_or_percentage']:
        activity_weight = float(activity['weight']) / 10.0
        contribution = grade_value * (activity_weight / 100.0)
        total_weight_contribution = activity_weight / 100.0
    else:
        contribution = grade_value * float(activity['weight'])
        total_weight_contribution = float(activity['weight'])

    activity_calculation['contribution'] = contribution
    return activity_calculation, contribution, total_weight_contribution, False


def _calculate_topic_grade(topic, user_id):
    """Calculate a topic's grade for a student."""
    topic_calculation = {
        'topic': topic,
        'activities': [],
        'grade': 0,
        'total_weight': 0,
        'missing_percentage': 0,
        'final_contribution': 0
    }

    activities = activity_service.get_by_topic_id(topic['id'])
    topic_grade = 0
    topic_total_weight = 0

    for activity in activities:
        activity_calc, contribution, weight_contrib, skip = (
            _calculate_activity_contribution(activity, topic, user_id))

        if skip:
            topic_calculation['activities'].append(activity_calc)
            continue

        topic_grade += contribution
        topic_total_weight += weight_contrib
        topic_calculation['activities'].append(activity_calc)

    if topic_total_weight > 0:
        if topic['weight_or_percentage']:
            expected_total = 1.0
            if abs(topic_total_weight - expected_total) > 0.001:
                missing_percentage = (expected_total - topic_total_weight) * 100
                topic_calculation['missing_percentage'] = missing_percentage
            topic_grade = topic_grade / topic_total_weight
        else:
            topic_grade = topic_grade / topic_total_weight
    else:
        topic_grade = 1.0

    topic_calculation['grade'] = topic_grade
    topic_calculation['total_weight'] = topic_total_weight

    return topic_calculation


def _calculate_final_grade_from_topics(topic_calculations, section):
    """Calculate final grade from topic calculations."""
    final_grade = 0
    total_weight = 0

    for topic_calculation in topic_calculations:
        topic = topic_calculation['topic']
        topic_grade = topic_calculation['grade']

        if section['weight_or_percentage']:
            topic_weight = float(topic['weight']) / 10.0
            topic_contribution = topic_grade * (topic_weight / 100.0)
            total_weight += topic_weight / 100.0
        else:
            topic_contribution = topic_grade * float(topic['weight'])
            total_weight += float(topic['weight'])

        topic_calculation['final_contribution'] = topic_contribution
        final_grade += topic_contribution

    if total_weight > 0:
        final_grade = final_grade / total_weight
    else:
        final_grade = 1.0

    return round(final_grade * 10) / 10, total_weight


@app.route('/sections/<int:section_id>/students/<int:user_id>/calculate_grade')
def calculate_student_grade(section_id, user_id):
    """Calculate and display a student's grade for a section."""
    section, student, error_msg, error_code = (
        _validate_student_and_section(section_id, user_id))
    if error_msg:
        return error_msg, error_code

    instance, course, topics = _get_grade_calculation_context(section)

    topic_calculations = []
    for topic in topics:
        topic_calculation = _calculate_topic_grade(topic, user_id)
        topic_calculations.append(topic_calculation)

    final_grade, total_weight = _calculate_final_grade_from_topics(
        topic_calculations, section)

    course_taken_service.update_final_grade(user_id, section_id, final_grade)

    return render_template(
        'sections/student_grade_calculation.html',
        student=student,
        section=section,
        instance=instance,
        course=course,
        topic_calculations=topic_calculations,
        final_grade=final_grade,
        total_weight=total_weight
    )


# ----- solution FUNCTION SIZE and ONE LEVEL OF ABSTRACTION error ---

@app.route('/sections/<int:section_id>/students/<int:user_id>/recalculate')
def recalculate_grade(section_id, user_id):
    """Recalculate a student's grade."""
    final_grade = grade_service.calculate_final_grade(user_id, section_id)
    course_taken_service.update_final_grade(user_id, section_id, final_grade)

    flash("Grade has been recalculated successfully", "success")
    return redirect(url_for('calculate_student_grade', section_id=section_id,
                            user_id=user_id))


def _calculate_all_students_final_grades(section_id):
    """Calculate final grades for all students in a section."""
    enrollments = course_taken_service.get_students_by_section(section_id)
    calculated_count = 0

    for enrollment in enrollments:
        user_id = enrollment['user_id']
        try:
            final_grade = grade_service.calculate_final_grade(user_id,
                                                              section_id)
            course_taken_service.update_final_grade(user_id, section_id,
                                                     final_grade)
            calculated_count += 1
        # Static analysis error fixing: more specific exception
        except (ValueError, KeyError) as e:
            flash(f"Error calculating grade for student "
                  f"{enrollment['user_name']}: {str(e)}", "warning")

    return calculated_count


@app.route('/sections/<int:section_id>/close', methods=['POST'])
def close_section(section_id):
    """Close a section and calculate final grades."""
    section = section_service.get_by_id(section_id)
    if not section:
        return "Section not found", 404

    try:
        calculated_count = _calculate_all_students_final_grades(section_id)

        section_service.close_section(section_id)

        flash(f"Section {section['number']} has been closed successfully. "
              f"Final grades calculated for {calculated_count} students. "
              "It can no longer be edited or deleted.", "success")

    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for('list_sections',
                            instance_id=section['instance_id']))


# ---------------- ENROLLMENT ----------------

@app.route('/sections/<int:section_id>/enroll', methods=['POST'])
def enroll_student_in_section(section_id):
    """Enroll a student in a section."""
    user_id = request.form['user_id']

    section = section_service.get_by_id(section_id)
    if not section:
        return "Section not found", 404

    instance = instance_service.get_by_id(section['instance_id'])
    course_id = instance['course_id']

    if course_taken_service.is_student_enrolled(user_id, section_id):
        flash("Student is already enrolled in this section.")
        return redirect(url_for('list_students_in_section',
                                section_id=section_id))

    course_taken_service.enroll_student(user_id, course_id, section_id)
    flash("Student enrolled successfully.")

    return redirect(url_for('list_students_in_section',
                            section_id=section_id))


@app.route('/sections/<int:section_id>/unenroll/<int:user_id>',
           methods=['POST'])
def unenroll_student_from_section(section_id, user_id):
    """Unenroll a student from a section."""
    section = section_service.get_by_id(section_id)
    if not section:
        return "Section not found", 404

    instance = instance_service.get_by_id(section['instance_id'])
    course_id = instance['course_id']

    course_taken_service.unenroll_student(course_id, section_id, user_id)
    flash("Student unenrolled successfully.")

    return redirect(url_for('list_students_in_section',
                            section_id=section_id))


@app.route('/sections/<int:section_id>/students')
def list_students_in_section(section_id):
    """List students enrolled in a section."""
    section = section_service.get_by_id(section_id)
    if not section:
        return "Section not found", 404

    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])

    enrollments = course_taken_service.get_students_by_section(section_id)

    enrolled_student_ids = [str(enrollment['user_id'])
                            for enrollment in enrollments]

    students = user_service.get_all(is_professor=False)

    return render_template('sections/students_in_section.html',
                           course=course,
                           section=section,
                           instance=instance,
                           enrollments=enrollments,
                           students=students,
                           enrolled_student_ids=enrolled_student_ids)


# ---------------- ACTIVITIES ----------------

@app.route('/topics/<int:topic_id>/activities')
def list_activities(topic_id):
    """List activities for a topic."""
    topic = topic_service.get_by_id(topic_id)
    if not topic:
        return "Topic not found", 404

    activities = activity_service.get_by_topic_id(topic_id)
    section = section_service.get_by_id(topic['section_id'])
    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])

    return render_template(
        'activities/list.html',
        activities=activities,
        topic=topic,
        section=section,
        instance=instance,
        course=course
    )


@app.route('/topics/<int:topic_id>/activities/create',
           methods=['GET', 'POST'])
def create_activity(topic_id):
    """Create a new activity for a topic."""
    topic = topic_service.get_by_id(topic_id)
    if not topic:
        return "Topic not found", 404

    section = section_service.get_by_id(topic['section_id'])
    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])
    activities = activity_service.get_by_topic_id(topic_id)

    if request.method == 'POST':
        optional_flag = 'optional' in request.form

        try:
            weight = int(request.form['weight'])
        except (KeyError, ValueError):
            flash("Invalid value for weight/percentage")
            return redirect(url_for('create_activity', topic_id=topic_id))

        instance_number = activity_service.get_next_instance_number(topic_id)

        activity_service.create(topic_id, instance_number, weight,
                                optional_flag)

        if topic['weight_or_percentage']:
            for activity in activities:
                key = f'percentages_{activity["id"]}'
                if key in request.form:
                    try:
                        updated_weight = int(request.form[key])
                        activity_service.update(activity['id'],
                                                activity['instance'],
                                                updated_weight,
                                                activity['optional_flag'])
                    except ValueError:
                        flash(f"Invalid percentage for activity "
                              f"{topic['name']} {activity['instance']}")
                        return redirect(url_for('create_activity',
                                                topic_id=topic_id))

        return redirect(url_for('list_activities', topic_id=topic_id))

    return render_template(
        'activities/create.html',
        topic=topic,
        section=section,
        instance=instance,
        course=course,
        activities=activities
    )


# Static analysis error fixing: renamed parameter id to activity_id
@app.route('/activities/edit/<int:activity_id>', methods=['GET', 'POST'])
def edit_activity(activity_id):
    """Edit an existing activity."""
    activity = activity_service.get_by_id(activity_id)
    if not activity:
        return "Activity not found", 404

    topic = topic_service.get_by_id(activity['topic_id'])
    if not topic:
        return "Topic not found", 404

    section = section_service.get_by_id(topic['section_id'])
    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])
    activities = activity_service.get_by_topic_id(topic['id'])

    if request.method == 'POST':
        optional_flag = 'optional' in request.form

        try:
            weight = int(request.form['weight'])
        except (KeyError, ValueError):
            flash("Invalid value for weight/percentage")
            return redirect(url_for('edit_activity',
                                    activity_id=activity_id))

        activity_service.update(activity_id, activity['instance'], weight,
                                optional_flag)

        if topic['weight_or_percentage']:
            for act in activities:
                if act['id'] == activity['id']:
                    continue

                key = f'percentages_{act["id"]}'
                if key in request.form:
                    try:
                        updated_weight = int(request.form[key])
                        activity_service.update(act['id'], act['instance'],
                                                updated_weight,
                                                act['optional_flag'])
                    except ValueError:
                        flash(f"Invalid percentage for activity "
                              f"{topic['name']} {act['instance']}")
                        return redirect(url_for('edit_activity',
                                                activity_id=activity_id))

        return redirect(url_for('list_activities', topic_id=topic['id']))

    return render_template(
        'activities/edit.html',
        activity=activity,
        topic=topic,
        section=section,
        instance=instance,
        course=course,
        activities=activities
    )


# Static analysis error fixing: renamed parameter id to activity_id
@app.post('/activities/delete/<int:activity_id>')
def delete_activity_direct(activity_id):
    """Delete an activity directly."""
    activity = activity_service.get_by_id(activity_id)
    if not activity:
        return "Activity not found", 404

    topic = topic_service.get_by_id(activity['topic_id'])
    activity_service.delete(activity_id)

    return redirect(url_for('list_activities', topic_id=topic['id']))


# ----- solution ONE LEVEL OF ABSTRACTION error ---
def _validate_activity_and_topic(activity_id):
    """Validate that both activity and topic exist."""
    activity = activity_service.get_by_id(activity_id)
    if not activity:
        return None, None, "Activity not found", 404

    topic = topic_service.get_by_id(activity['topic_id'])
    if not topic:
        return None, None, "Topic not found", 404

    return activity, topic, None, None


def _get_delete_activity_context(topic):
    """Get context for deleting an activity."""
    section = section_service.get_by_id(topic['section_id'])
    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])

    return section, instance, course


def _get_remaining_activities(topic_id, activity_id):
    """Get activities remaining after deletion."""
    activities = activity_service.get_by_topic_id(topic_id)
    remaining_activities = [a for a in activities if a['id'] != activity_id]
    return remaining_activities


def _update_remaining_activities_percentages(remaining_activities):
    """Update percentages for remaining activities."""
    for act in remaining_activities:
        new_weight = int(request.form[f'percentages_{act["id"]}'])
        activity_service.update(act['id'], act['instance'], new_weight,
                                act['optional_flag'])


def _delete_activity_and_redirect(activity_id, topic_id):
    """Delete activity and redirect to activities list."""
    activity_service.delete(activity_id)
    return redirect(url_for('list_activities', topic_id=topic_id))


# Static analysis error fixing: renamed parameter id to activity_id
@app.route('/activities/delete/percentage/<int:activity_id>',
           methods=['GET', 'POST'])
def delete_activity_percentage_view(activity_id):
    """Delete an activity with percentage redistribution."""
    activity, topic, error_msg, error_code = (
        _validate_activity_and_topic(activity_id))
    if error_msg:
        return error_msg, error_code

    section, instance, course = _get_delete_activity_context(topic)
    remaining_activities = _get_remaining_activities(topic['id'],
                                                     activity_id)

    if request.method == 'POST':
        try:
            _update_remaining_activities_percentages(remaining_activities)
            return _delete_activity_and_redirect(activity_id, topic['id'])
        except ValueError:
            flash("Invalid input. All percentages must be numbers.")
            return redirect(request.url)

    return render_template(
        'activities/delete_percentage.html',
        activity=activity,
        topic=topic,
        section=section,
        instance=instance,
        course=course,
        activities=remaining_activities
    )


# ----- solution ONE LEVEL OF ABSTRACTION error ---

# ---------------- PROFESSORS ----------------
@app.route('/professors')
def list_professors():
    """List all professors."""
    professors = user_service.get_all(is_professor=True)
    return render_template('professors/list.html', professors=professors)


@app.route('/professors/create', methods=['GET', 'POST'])
def create_professor():
    """Create a new professor."""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        if 'import_id' in request.form and request.form['import_id']:
            import_id = int(request.form['import_id'])
        else:
            import_id = None

        user_service.create(name, email, is_professor=True,
                            import_id=import_id)
        flash(f"Professor {name} created successfully.")
        return redirect(url_for('list_professors'))

    next_import_id = user_service.get_next_import_id(is_professor=True)

    return render_template('professors/create.html',
                           next_import_id=next_import_id)


# Static analysis error fixing: renamed parameter id to professor_id
@app.route('/professors/edit/<int:professor_id>', methods=['GET', 'POST'])
def edit_professor(professor_id):
    """Edit an existing professor."""
    professor = user_service.get_by_id(professor_id)
    if not professor or not professor['is_professor']:
        return "Professor not found", 404

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        if 'import_id' in request.form and request.form['import_id']:
            import_id = int(request.form['import_id'])
            user_service.update(professor_id, name, email,
                                is_professor=True, import_id=import_id)
        else:
            user_service.update(professor_id, name, email,
                                is_professor=True)

        flash(f"Professor {name} updated successfully.")
        return redirect(url_for('list_professors'))

    return render_template('professors/edit.html', professor=professor)


# Static analysis error fixing: renamed parameter id to professor_id
@app.route('/professors/delete/<int:professor_id>', methods=['POST'])
def delete_professor(professor_id):
    """Delete a professor."""
    professor = user_service.get_by_id(professor_id)
    if professor:
        name = professor['name']
        user_service.delete(professor_id)
        flash(f"Professor {name} deleted successfully.")

    return redirect(url_for('list_professors'))


# ---------------- STUDENTS ----------------
@app.route('/students')
def list_students():
    """List all students."""
    students = user_service.get_all(is_professor=False)
    return render_template('students/list.html', students=students)


@app.route('/students/create', methods=['GET', 'POST'])
def create_student():
    """Create a new student."""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        admission_date = request.form['admission_date']

        if 'import_id' in request.form and request.form['import_id']:
            import_id = int(request.form['import_id'])
        else:
            import_id = None

        user_service.create(name, email, is_professor=False,
                            admission_date=admission_date,
                            import_id=import_id)
        flash(f"Student {name} created successfully.")
        return redirect(url_for('list_students'))

    next_import_id = user_service.get_next_import_id(is_professor=False)

    return render_template('students/create.html',
                           next_import_id=next_import_id)


# Static analysis error fixing: renamed parameter id to student_id
@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit an existing student."""
    student = user_service.get_by_id(student_id)
    if not student or student['is_professor']:
        return "Student not found", 404

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        admission_date = request.form['admission_date']

        if 'import_id' in request.form and request.form['import_id']:
            import_id = int(request.form['import_id'])
            user_service.update(student_id, name, email,
                                is_professor=False,
                                admission_date=admission_date,
                                import_id=import_id)
        else:
            user_service.update(student_id, name, email,
                                is_professor=False,
                                admission_date=admission_date)

        flash(f"Student {name} updated successfully.")
        return redirect(url_for('list_students'))

    return render_template('students/edit.html', student=student)


# Static analysis error fixing: renamed parameter id to student_id
@app.route('/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Delete a student."""
    student = user_service.get_by_id(student_id)
    if student:
        name = student['name']
        user_service.delete(student_id)
        flash(f"Student {name} deleted successfully.")

    return redirect(url_for('list_students'))


# ---------------- Grades ----------------

# ----- solution ONE LEVEL OF ABSTRACTION error ---
def _validate_activity_exists(activity_id):
    """Validate that an activity exists."""
    activity = activity_service.get_by_id(activity_id)
    if not activity:
        return None, "Activity not found", 404
    return activity, None, None


def _get_evaluation_context(activity):
    """Get context data for evaluation."""
    topic = topic_service.get_by_id(activity['topic_id'])
    section = section_service.get_by_id(topic['section_id'])
    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])

    return topic, section, instance, course


def _build_student_with_grade(enrollment, activity_id):
    """Build student data with grade information."""
    grade = grade_service.get_by_activity_and_student(activity_id,
                                                      enrollment['user_id'])

    student = {
        'id': enrollment['user_id'],
        'name': enrollment['user_name'],
        'email': enrollment['user_email']
    }

    if grade:
        student['grade'] = grade['grade']
        student['grade_id'] = grade['id']

    return student


def _get_students_with_grades(section_id, activity_id):
    """Get students with their grades for an activity."""
    enrollments = course_taken_service.get_students_by_section(section_id)
    students = []

    for enrollment in enrollments:
        student = _build_student_with_grade(enrollment, activity_id)
        students.append(student)

    return students


@app.route('/activities/<int:activity_id>/evaluate',
           methods=['GET', 'POST'])
def evaluate_students(activity_id):
    """Evaluate students for an activity."""
    activity, error_msg, error_code = _validate_activity_exists(activity_id)
    if error_msg:
        return error_msg, error_code

    topic, section, instance, course = _get_evaluation_context(activity)
    students = _get_students_with_grades(section['id'], activity_id)

    return render_template(
        'activities/evaluate_students.html',
        activity=activity,
        topic=topic,
        section=section,
        instance=instance,
        course=course,
        students=students
    )


# ----- solution ONE LEVEL OF ABSTRACTION error ---

@app.route('/activities/<int:activity_id>/save_grades', methods=['POST'])
def save_grades(activity_id):
    """Save grades for an activity."""
    activity = activity_service.get_by_id(activity_id)
    if not activity:
        return "Activity not found", 404

    topic = topic_service.get_by_id(activity['topic_id'])

    section = section_service.get_by_id(topic['section_id'])
    enrollments = course_taken_service.get_students_by_section(section['id'])

    for enrollment in enrollments:
        user_id = enrollment['user_id']
        grade_key = f'grade_{user_id}'
        grade_id_key = f'grade_id_{user_id}'

        if grade_key in request.form:
            try:
                grade_value = float(request.form[grade_key])
                grade_value = max(1.0, min(7.0, grade_value))
                grade_value = round(grade_value * 10) / 10

                if grade_id_key in request.form:
                    grade_id = request.form[grade_id_key]
                    grade_service.update(grade_id, grade_value)
                else:
                    grade_service.create(grade_value, user_id, activity_id)

            except ValueError:
                flash(f"Invalid grade format for student "
                      f"{enrollment['user_name']}", "danger")
                return redirect(url_for('evaluate_students',
                                        activity_id=activity_id))

    flash("Grades saved successfully", "success")
    return redirect(url_for('list_activities', topic_id=topic['id']))


# ---------------- Uploads ----------------

@app.route('/import', methods=['GET', 'POST'])
def import_data():
    """Import data from JSON files."""
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
            # Static analysis error fixing: removed f-string without interpolation
            flash(f"Correctly imported {selected_type} data")
        # Static analysis error fixing: more specific exception
        except (ValueError, KeyError) as e:
            flash(f"Error importing data: {str(e)}")

        return redirect(url_for('import_data'))

    return render_template('import/upload.html', file_types=file_types)


# ---------------- Schedule ----------------

@app.route('/schedule', methods=['GET'])
def schedule_page():
    """Display schedule generation page."""
    periods = instance_service.get_periods()

    if not periods:
        flash("No periods available in the system.", "warning")

    return render_template('schedule/index.html', periods=periods)


@app.route('/schedule/generate', methods=['POST'])
def generate_schedule():
    """Generate schedule for a period."""
    period = request.form.get('period')

    if not period:
        flash("No period selected.", "danger")
        return redirect(url_for('schedule_page'))

    schedule = schedule_service.generate_schedule(period)

    if not schedule:
        flash("Could not generate a valid schedule. Please review room or "
              "teacher availability.", "danger")
        return redirect(url_for('schedule_page'))

    csv_content = schedule_service.create_csv(period)
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition":
                 f"attachment; filename=schedule_{period}.csv"}
    )


# ---------------- REPORTS ----------------

def _get_reports_initial_data():
    """Get initial data for reports page."""
    students = user_service.get_all(is_professor=False)
    closed_sections = section_service.get_closed_sections()
    activities = activity_service.get_all_with_context()

    return students, closed_sections, activities


def _generate_topic_instance_report(activity_id):
    """Generate topic instance report."""
    activity = activity_service.get_by_id(activity_id)
    if not activity:
        return None, "Activity not found"

    topic = topic_service.get_by_id(activity['topic_id'])
    section = section_service.get_by_id(topic['section_id'])
    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])

    enrollments = course_taken_service.get_students_by_section(section['id'])
    grades_data = []

    for enrollment in enrollments:
        grade = grade_service.get_by_activity_and_student(
            activity_id, enrollment['user_id'])
        grades_data.append({
            'student_name': enrollment['user_name'],
            'student_email': enrollment['user_email'],
            'grade': grade['grade'] if grade else 'Not graded'
        })

    context = {
        'type': 'topic_instance',
        'course': course,
        'instance': instance,
        'section': section,
        'topic': topic,
        'activity': activity,
        'grades_data': grades_data
    }

    return context, None


def _generate_section_final_grades_report(section_id):
    """Generate section final grades report."""
    section = section_service.get_by_id(section_id)
    if not section or not section['is_closed']:
        return None, "Section not found or not closed"

    instance = instance_service.get_by_id(section['instance_id'])
    course = course_service.get_by_id(instance['course_id'])
    enrollments = course_taken_service.get_students_by_section(section_id)

    context = {
        'type': 'section_final',
        'course': course,
        'instance': instance,
        'section': section,
        'enrollments': enrollments
    }

    return context, None


def _generate_student_transcript_report(student_id):
    """Generate student transcript report."""
    student = user_service.get_by_id(student_id)
    if not student:
        return None, "Student not found"

    closed_courses = course_taken_service.get_closed_courses_by_student(
        student_id)

    context = {
        'type': 'student_transcript',
        'student': student,
        'closed_courses': closed_courses
    }

    return context, None


def _process_report_generation(report_type, report_data):
    """Process report generation based on type."""
    if report_type == 'topic_instance':
        activity_id = report_data.get('activity_id')
        return _generate_topic_instance_report(activity_id)

    if report_type == 'section_final':
        section_id = report_data.get('section_id')
        return _generate_section_final_grades_report(section_id)

    if report_type == 'student_transcript':
        student_id = report_data.get('student_id')
        return _generate_student_transcript_report(student_id)

    return None, "Invalid report type"


@app.route('/reports', methods=['GET', 'POST'])
def reports():
    """Generate and display reports."""
    if request.method == 'GET':
        students, closed_sections, activities = _get_reports_initial_data()
        return render_template('reports/reports.html',
                               students=students,
                               closed_sections=closed_sections,
                               activities=activities)

    report_type = request.form.get('report_type')
    if not report_type:
        flash("Please select a report type", "danger")
        return redirect(url_for('reports'))

    report_context, error = _process_report_generation(report_type,
                                                       request.form)

    if error:
        flash(error, "danger")
        return redirect(url_for('reports'))

    students, closed_sections, activities = _get_reports_initial_data()

    return render_template('reports/reports.html',
                           students=students,
                           closed_sections=closed_sections,
                           activities=activities,
                           report_context=report_context)


if __name__ == '__main__':
    app.run(debug=True)
