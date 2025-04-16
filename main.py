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


@app.route('/cursos')
def list_cursos():
    cursos = course_service.get_all()
    return render_template('cursos/list.html', cursos=cursos)

@app.route('/cursos/create', methods=['GET', 'POST'])
def create_curso():
    if request.method == 'POST':
        name = request.form['name']
        ncr = request.form['ncr']
        course_service.create(name, ncr)
        return redirect(url_for('list_cursos'))
    return render_template('cursos/create.html')

@app.route('/cursos/edit/<int:id>', methods=['GET', 'POST'])
def edit_curso(id):
    curso = course_service.get_by_id(id)
    if not curso:
        return "Curso no encontrado", 404
    if request.method == 'POST':
        name = request.form['name']
        ncr = request.form['ncr']
        course_service.update(id, name, ncr)
        return redirect(url_for('list_cursos'))
    return render_template('cursos/edit.html', curso=curso)

@app.route('/cursos/delete/<int:id>', methods=['POST'])
def delete_curso(id):
    course_service.delete(id)
    return redirect(url_for('list_cursos'))


@app.route('/profesores')
def list_profesores():
    profesores = user_service.get_all_professors()
    return render_template('profesores/list.html', profesores=profesores)

@app.route('/profesores/create', methods=['GET', 'POST'])
def create_profesor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user_service.create(name, email, is_professor=True)
        return redirect(url_for('list_profesores'))
    return render_template('profesores/create.html')

@app.route('/profesores/edit/<int:id>', methods=['GET', 'POST'])
def edit_profesor(id):
    profesor = user_service.get_by_id(id)
    if not profesor or not profesor['Is_professor']:
        return "Profesor no encontrado", 404
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user_service.update(id, name, email)
        return redirect(url_for('list_profesores'))
    return render_template('profesores/edit.html', profesor=profesor)

@app.route('/profesores/delete/<int:id>', methods=['POST'])
def delete_profesor(id):
    user_service.delete(id)
    return redirect(url_for('list_profesores'))


@app.route('/alumnos')
def list_alumnos():
    alumnos = user_service.get_all_students()
    return render_template('alumnos/list.html', alumnos=alumnos)

@app.route('/alumnos/create', methods=['GET', 'POST'])
def create_alumno():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        entry_date = request.form['entry_date']
        user_service.create(name, email, is_professor=False, entry_date=entry_date)
        return redirect(url_for('list_alumnos'))
    return render_template('alumnos/create.html')

@app.route('/alumnos/edit/<int:id>', methods=['GET', 'POST'])
def edit_alumno(id):
    alumno = user_service.get_by_id(id)
    if not alumno or alumno['Is_professor']:
        return "Alumno no encontrado", 404
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        entry_date = request.form['entry_date']
        user_service.update(id, name, email, entry_date)
        return redirect(url_for('list_alumnos'))
    return render_template('alumnos/edit.html', alumno=alumno)

@app.route('/alumnos/delete/<int:id>', methods=['POST'])
def delete_alumno(id):
    user_service.delete(id)
    return redirect(url_for('list_alumnos'))

#####################################
# RUN APP
#####################################

if __name__ == '__main__':
    app.run(debug=True)
