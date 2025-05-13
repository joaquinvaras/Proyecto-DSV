import json
from db import DatabaseConnection

class ImportService:
    def __init__(self):
        self.db = DatabaseConnection()

    def _success(self, message):
        print(f"[SUCCESS] {message}")

    def _error(self, message):
        print(f"[ERROR] {message}")

    def import_json(self, file, file_type):
        data = json.load(file)

        match file_type:
            case 'alumnos': self._import_alumnos(data)
            case 'profesores': self._import_profesores(data)
            case 'cursos': self._import_cursos(data)
            case 'instancias_cursos': self._import_instancias_cursos(data)
            case 'instancias_cursos_secciones': self._import_instancias_cursos_secciones(data)
            case 'alumnos_seccion': self._import_alumnos_seccion(data)
            case 'notas_alumnos': self._import_notas_alumnos(data)
            case 'salas_clases': self._import_salas_clases(data)
            case _: raise ValueError(f"Tipo de archivo no soportado: {file_type}")

    def _import_alumnos(self, data):
        cursor = self.db.connect()
        for alumno in data['alumnos']:
            import_id = alumno['id']
            name = alumno['nombre']
            email = alumno['correo']
            admission_date = f"{alumno['anio_ingreso']}-01-01"
            is_professor = False

            query = """
                INSERT INTO Users (import_id, name, email, admission_date, is_professor)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (import_id, name, email, admission_date, is_professor)

            try:
                cursor.execute(query, values)
                self._success(f"Imported alumno: {name} ({email})")
            except Exception as err:
                self._error(f"Inserting alumno {name} ({email}): {err}")

        self.db.commit()

    def _import_profesores(self, data):
        cursor = self.db.connect()
        for profesor in data['profesores']:
            import_id = profesor['id']
            name = profesor['nombre']
            email = profesor['correo']
            admission_date = None
            is_professor = True

            query = """
                INSERT INTO Users (import_id, name, email, admission_date, is_professor)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (import_id, name, email, admission_date, is_professor)

            try:
                cursor.execute(query, values)
                self._success(f"Imported profesor: {name} ({email})")
            except Exception as err:
                self._error(f"Inserting profesor {name} ({email}): {err}")

        self.db.commit()

    def _import_cursos(self, data):
        cursor = self.db.connect()
        cursos = data['cursos']

        for curso in cursos:
            curso_id = curso['id']
            codigo = curso['codigo']
            descripcion = curso['descripcion']
            creditos = curso['creditos']

            try:
                cursor.execute("""
                    INSERT INTO Courses (id, nrc, name, credits)
                    VALUES (%s, %s, %s, %s)
                """, (curso_id, codigo, descripcion, creditos))
                self._success(f"Inserted course: {codigo} - {descripcion}")
            except Exception as e:
                self._error(f"Inserting course {codigo}: {e}")
        
        for curso in cursos:
            curso_id = curso['id']
            requisitos = curso['requisitos']

            for cod_requisito in requisitos:
                try:
                    cursor.execute("SELECT id FROM Courses WHERE nrc = %s", (cod_requisito,))
                    result = cursor.fetchone()
                    if result:
                        prereq_id = result['id']
                        cursor.execute("""
                            INSERT INTO CoursePrerequisites (course_id, prerequisite_id)
                            VALUES (%s, %s)
                        """, (curso_id, prereq_id))
                        self._success(f"Added prerequisite {cod_requisito} for course {curso_id}")
                    else:
                        self._error(f"Prerequisite course with code {cod_requisito} not found")
                except Exception as e:
                    self._error(f"Adding prerequisite {cod_requisito} for course {curso_id}: {e}")

        self.db.commit()

    def _import_instancias_cursos(self, data):
        cursor = self.db.connect()

        year = data['año']
        semester = data['semestre']
        period = f"{year}-{semester}"
        instancias = data['instancias']

        for instancia in instancias:
            instancia_id = instancia['id']
            curso_id = instancia['curso_id']

            try:
                cursor.execute("""
                    INSERT INTO Instances (id, period, course_id)
                    VALUES (%s, %s, %s)
                """, (instancia_id, period, curso_id))
                self._success(f"Inserted instance {instancia_id} for course {curso_id} in period {period}")
            except Exception as e:
                self._error(f"Inserting instance {instancia_id}: {e}")

        self.db.commit()

    def _import_instancias_cursos_secciones(self, data):
        cursor = self.db.connect()
        secciones = data["secciones"]

        for seccion in secciones:
            seccion_id = seccion["id"]
            instancia_id = seccion["instancia_curso"]
            profesor_import_id = seccion["profesor_id"]
            tipo_evaluacion = seccion["evaluacion"]["tipo"]
            combinacion_topicos = seccion["evaluacion"]["combinacion_topicos"]
            topicos_dict = seccion["evaluacion"]["topicos"]

            try:
                cursor.execute("""
                    SELECT id FROM Users WHERE import_id = %s AND is_professor = TRUE
                """, (profesor_import_id,))
                result = cursor.fetchone()
                if not result:
                    self._error(f"No professor found with import_id {profesor_import_id}")
                    continue
                profesor_id = result["id"]
            except Exception as e:
                self._error(f"Fetching professor ID for import_id {profesor_import_id}: {e}")
                continue

            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM Sections WHERE instance_id = %s
                """, (instancia_id,))
                current_count = cursor.fetchone()['COUNT(*)']
                number = current_count + 1
            except Exception as e:
                self._error(f"Counting sections for instance_id {instancia_id}: {e}")
                continue

            weight_or_percentage = tipo_evaluacion == "peso"

            try:
                cursor.execute("""
                    INSERT INTO Sections (id, instance_id, number, professor_id, weight_or_percentage)
                    VALUES (%s, %s, %s, %s, %s)
                """, (seccion_id, instancia_id, number, profesor_id, weight_or_percentage))
                self._success(f"Inserted Section ID {seccion_id}")
            except Exception as e:
                self._error(f"Inserting Section ID {seccion_id}: {e}")
                continue

            for topic in combinacion_topicos:
                topic_id = topic["id"]
                topic_name = topic["nombre"]
                topic_valor = topic["valor"] * 10

                topic_eval = topicos_dict[str(topic_id)]
                topic_eval_tipo = topic_eval["tipo"]
                topic_weight_or_percentage = topic_eval_tipo == "peso"

                try:
                    cursor.execute("""
                        INSERT INTO Topics (id, section_id, name, weight, weight_or_percentage)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (topic_id, seccion_id, topic_name, topic_valor, topic_weight_or_percentage))
                    self._success(f"Inserted Topic ID {topic_id} for Section ID {seccion_id}")
                except Exception as e:
                    self._error(f"Inserting Topic ID {topic_id} in Section ID {seccion_id}: {e}")
                    continue

                for i, (valor, obligatorio) in enumerate(zip(topic_eval["valores"], topic_eval["obligatorias"])):
                    activity_weight = valor * 10
                    optional_flag = not obligatorio

                    try:
                        cursor.execute("""
                            INSERT INTO Activities (topic_id, weight, optional_flag, instance)
                            VALUES (%s, %s, %s, %s)
                        """, (topic_id, activity_weight, optional_flag, i+1))
                        self._success(f"Inserted Activity {i} for Topic ID {topic_id}")
                    except Exception as e:
                        self._error(f"Inserting Activity {i} for Topic ID {topic_id}: {e}")

        self.db.commit()

    def _import_alumnos_seccion(self, data):
        cursor = self.db.connect()
        alumnos_seccion = data["alumnos_seccion"]

        for entry in alumnos_seccion:
            seccion_id = entry["seccion_id"]
            alumno_import_id = entry["alumno_id"]

            try:
                cursor.execute("""
                    SELECT id FROM Users WHERE import_id = %s AND is_professor = FALSE
                """, (alumno_import_id,))
                user_row = cursor.fetchone()

                if not user_row:
                    self._error(f"No user found for alumno_import_id {alumno_import_id}")
                    continue

                alumno_id = user_row["id"]

                cursor.execute("""
                    SELECT Instances.course_id
                    FROM Sections
                    JOIN Instances ON Sections.instance_id = Instances.id
                    WHERE Sections.id = %s
                """, (seccion_id,))
                result = cursor.fetchone()

                if not result:
                    self._error(f"No course found for seccion_id {seccion_id}")
                    continue

                course_id = result['course_id']

                cursor.execute("""
                    INSERT INTO Courses_Taken (user_id, section_id, course_id, final_grade)
                    VALUES (%s, %s, %s, %s)
                """, (alumno_id, seccion_id, course_id, 0))

                self._success(f"Enrolled alumno_id {alumno_id} in section_id {seccion_id} (course_id {course_id})")

            except Exception as e:
                self._error(f"Failed to enroll alumno_import_id {alumno_import_id} in section_id {seccion_id}: {e}")

        self.db.commit()

    def _import_notas_alumnos(self, data):
        cursor = self.db.connect()
        for entry in data["notas"]:
            alumno_import_id = entry["alumno_id"]
            topico_id = entry["topico_id"]
            instancia = entry["instancia"]
            nota = entry["nota"]

            try:
                cursor.execute("""
                    SELECT id FROM Users WHERE import_id = %s AND is_professor = FALSE
                """, (alumno_import_id,))
                user_row = cursor.fetchone()

                if not user_row:
                    self._error(f"No user found for alumno_import_id {alumno_import_id}")
                    continue
                
                alumno_id = user_row["id"]
                
                cursor.execute("""
                    SELECT id FROM Activities
                    WHERE topic_id = %s AND instance = %s
                """, (topico_id, instancia))
                result = cursor.fetchone()

                if not result:
                    self._error(f"No activity found for topico_id {topico_id} and instancia {instancia}")
                    continue

                activity_id = result["id"]

                cursor.execute("""
                    INSERT INTO Grades (activity_id, user_id, grade)
                    VALUES (%s, %s, %s)
                """, (activity_id, alumno_id, nota))
                self._success(f"Inserted grade for alumno_id {alumno_id}, activity_id {activity_id}: {nota}")
            except Exception as e:
                self._error(f"Inserting grade for alumno_id {alumno_id}, topico_id {topico_id}, instancia {instancia}: {e}")

        self.db.commit()

    def _import_salas_clases(self, data):
        cursor = self.db.connect()
        salas = data.get("salas", [])

        for sala in salas:
            room_id = sala["id"]
            nombre = sala["nombre"]
            capacidad = sala["capacidad"]

            try:
                cursor.execute("""
                    INSERT INTO Rooms (id, name, capacity)
                    VALUES (%s, %s, %s)
                """, (room_id, nombre, capacidad))

                self._success(f"Room inserted: id={room_id}, name='{nombre}', capacidad={capacidad}")

            except Exception as e:
                self._error(f"Failed to insert room id={room_id}, name='{nombre}': {e}")
            
        
        self.db.commit()
