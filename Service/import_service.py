import json
import re
from db import DatabaseConnection

class ImportService:
    def __init__(self):
        self.db = DatabaseConnection()

    def _success(self, message):
        print(f"[SUCCESS] {message}")

    def _error(self, message):
        print(f"[ERROR] {message}")

    def _validation_error(self, message):
        print(f"[VALIDATION ERROR] {message}")

    # ----- Basic Validations ---
    def _is_valid_email(self, email):
        """Validates email format"""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _is_valid_name(self, name):
        """Validates name field"""
        if not name or not isinstance(name, str):
            return False
        return len(name.strip()) > 0 and len(name) <= 100

    def _is_valid_nrc(self, nrc):
        """Validates NRC code format"""
        if not nrc or not isinstance(nrc, str):
            return False
        return len(nrc.strip()) > 0 and len(nrc) <= 50

    def _is_valid_year(self, year):
        """Validates year format"""
        if not isinstance(year, int):
            return False
        return 1990 <= year <= 2050

    def _is_valid_semester(self, semester):
        """Validates semester format"""
        if not isinstance(semester, int):
            return False
        return semester in [1, 2]

    def _is_valid_credits(self, credits):
        """Validates credits field"""
        if not isinstance(credits, int):
            return False
        return 1 <= credits <= 99

    def _is_valid_capacity(self, capacity):
        """Validates room capacity"""
        if not isinstance(capacity, int):
            return False
        return capacity > 0

    def _is_valid_grade(self, grade):
        """Validates grade value"""
        if not isinstance(grade, (int, float)):
            return False
        return 1.0 <= float(grade) <= 7.0

    def _is_valid_id(self, id_value):
        """Validates ID field"""
        if not isinstance(id_value, int):
            return False
        return id_value > 0

    def _is_valid_instance_number(self, instance):
        """Validates instance number"""
        if not isinstance(instance, int):
            return False
        return instance > 0

    def _is_valid_percentage_value(self, value):
        """Validates percentage/weight value (0.0-100.0)"""
        if not isinstance(value, (int, float)):
            return False
        return 0.0 <= float(value) <= 100.0

    def _is_valid_evaluation_type(self, tipo):
        """Validates evaluation type"""
        if not isinstance(tipo, str):
            return False
        return tipo in ["peso", "porcentaje"]

    # ----- Structure Validations ---
    def _validate_alumnos_structure(self, data):
        """Validates alumnos JSON structure"""
        if not isinstance(data, dict):
            self._validation_error("Root must be an object")
            return False
            
        if 'alumnos' not in data:
            self._validation_error("Missing 'alumnos' key")
            return False
            
        if not isinstance(data['alumnos'], list):
            self._validation_error("'alumnos' must be an array")
            return False
            
        return True

    def _validate_instancias_cursos_data(self, data):
        """Validates complete instancias_cursos data"""
        if not self._validate_instancias_cursos_structure(data):
            return False
            
        if not self._validate_instancia_curso_fields(data):
            return False
            
        for index, instancia in enumerate(data['instancias']):
            if not self._validate_instancia_fields(instancia, index):
                return False
                
        return True

    def _validate_secciones_data(self, data):
        """Validates complete instancias_cursos_secciones data"""
        if not self._validate_secciones_structure(data):
            return False
            
        for index, seccion in enumerate(data['secciones']):
            if not self._validate_seccion_fields(seccion, index):
                return False
                
        return True

    def _validate_alumnos_seccion_data(self, data):
        """Validates complete alumnos_seccion data"""
        if not self._validate_alumnos_seccion_structure(data):
            return False
            
        for index, entry in enumerate(data['alumnos_seccion']):
            if not self._validate_alumno_seccion_fields(entry, index):
                return False
                
        return True

    def _validate_notas_alumnos_data(self, data):
        """Validates complete notas_alumnos data"""
        if not self._validate_notas_alumnos_structure(data):
            return False
            
        for index, entry in enumerate(data['notas']):
            if not self._validate_nota_fields(entry, index):
                return False
                
        return True

    def _validate_instancias_cursos_structure(self, data):
        """Validates instancias_cursos JSON structure"""
        if not isinstance(data, dict):
            self._validation_error("Root must be an object")
            return False
            
        required_fields = ['año', 'semestre', 'instancias']
        for field in required_fields:
            if field not in data:
                self._validation_error(f"Missing '{field}' key")
                return False
        
        if not isinstance(data['instancias'], list):
            self._validation_error("'instancias' must be an array")
            return False
            
        return True

    def _validate_instancia_curso_fields(self, data):
        """Validates instancias_cursos fields"""
        errors = []
        
        if not self._is_valid_year(data.get('año')):
            errors.append("'año' must be a valid year (1990-2050)")
            
        if not self._is_valid_semester(data.get('semestre')):
            errors.append("'semestre' must be 1 or 2")
        
        if errors:
            for error in errors:
                self._validation_error(error)
            return False
            
        return True

    def _validate_instancia_fields(self, instancia, index):
        """Validates individual instancia fields"""
        errors = []
        
        required_fields = ['id', 'curso_id']
        for field in required_fields:
            if field not in instancia:
                errors.append(f"Missing required field '{field}'")
        
        if 'id' in instancia and not self._is_valid_id(instancia['id']):
            errors.append("'id' must be a positive integer")
            
        if 'curso_id' in instancia and not self._is_valid_id(instancia['curso_id']):
            errors.append("'curso_id' must be a positive integer")
        
        if errors:
            for error in errors:
                self._validation_error(f"Instancia {index}: {error}")
            return False
            
        return True

    def _validate_secciones_structure(self, data):
        """Validates instancias_cursos_secciones JSON structure"""
        if not isinstance(data, dict):
            self._validation_error("Root must be an object")
            return False
            
        if 'secciones' not in data:
            self._validation_error("Missing 'secciones' key")
            return False
            
        if not isinstance(data['secciones'], list):
            self._validation_error("'secciones' must be an array")
            return False
            
        return True

    def _validate_seccion_fields(self, seccion, index):
        """Validates individual seccion fields"""
        errors = []
        
        required_fields = ['id', 'instancia_curso', 'profesor_id', 'evaluacion']
        for field in required_fields:
            if field not in seccion:
                errors.append(f"Missing required field '{field}'")
        
        if 'id' in seccion and not self._is_valid_id(seccion['id']):
            errors.append("'id' must be a positive integer")
            
        if 'instancia_curso' in seccion and not self._is_valid_id(seccion['instancia_curso']):
            errors.append("'instancia_curso' must be a positive integer")
            
        if 'profesor_id' in seccion and not self._is_valid_id(seccion['profesor_id']):
            errors.append("'profesor_id' must be a positive integer")
            
        if 'evaluacion' in seccion:
            evaluacion = seccion['evaluacion']
            if not isinstance(evaluacion, dict):
                errors.append("'evaluacion' must be an object")
            else:
                eval_errors = self._validate_evaluacion_fields(evaluacion)
                errors.extend(eval_errors)
        
        if errors:
            for error in errors:
                self._validation_error(f"Seccion {index}: {error}")
            return False
            
        return True

    def _validate_evaluacion_fields(self, evaluacion):
        """Validates evaluacion fields"""
        errors = []
        
        required_fields = ['tipo', 'combinacion_topicos', 'topicos']
        for field in required_fields:
            if field not in evaluacion:
                errors.append(f"evaluacion missing '{field}' field")
        
        if 'tipo' in evaluacion and not self._is_valid_evaluation_type(evaluacion['tipo']):
            errors.append("evaluacion 'tipo' must be 'peso' or 'porcentaje'")
            
        if 'combinacion_topicos' in evaluacion:
            if not isinstance(evaluacion['combinacion_topicos'], list):
                errors.append("'combinacion_topicos' must be an array")
            else:
                for i, topic in enumerate(evaluacion['combinacion_topicos']):
                    topic_errors = self._validate_topic_combinacion_fields(topic, i)
                    errors.extend(topic_errors)
        
        if 'topicos' in evaluacion and not isinstance(evaluacion['topicos'], dict):
            errors.append("'topicos' must be an object")
            
        return errors

    def _validate_topic_combinacion_fields(self, topic, index):
        """Validates topic in combinacion_topicos"""
        errors = []
        
        required_fields = ['id', 'nombre', 'valor']
        for field in required_fields:
            if field not in topic:
                errors.append(f"combinacion_topicos[{index}] missing '{field}' field")
        
        if 'id' in topic and not self._is_valid_id(topic['id']):
            errors.append(f"combinacion_topicos[{index}] 'id' must be a positive integer")
            
        if 'nombre' in topic and not self._is_valid_name(topic['nombre']):
            errors.append(f"combinacion_topicos[{index}] 'nombre' must be a non-empty string")
            
        if 'valor' in topic and not self._is_valid_percentage_value(topic['valor']):
            errors.append(f"combinacion_topicos[{index}] 'valor' must be between 0.0 and 100.0")
            
        return errors

    def _validate_alumnos_seccion_structure(self, data):
        """Validates alumnos_seccion JSON structure"""
        if not isinstance(data, dict):
            self._validation_error("Root must be an object")
            return False
            
        if 'alumnos_seccion' not in data:
            self._validation_error("Missing 'alumnos_seccion' key")
            return False
            
        if not isinstance(data['alumnos_seccion'], list):
            self._validation_error("'alumnos_seccion' must be an array")
            return False
            
        return True

    def _validate_alumno_seccion_fields(self, entry, index):
        """Validates individual alumno_seccion fields"""
        errors = []
        
        required_fields = ['seccion_id', 'alumno_id']
        for field in required_fields:
            if field not in entry:
                errors.append(f"Missing required field '{field}'")
        
        if 'seccion_id' in entry and not self._is_valid_id(entry['seccion_id']):
            errors.append("'seccion_id' must be a positive integer")
            
        if 'alumno_id' in entry and not self._is_valid_id(entry['alumno_id']):
            errors.append("'alumno_id' must be a positive integer")
        
        if errors:
            for error in errors:
                self._validation_error(f"Alumno_seccion {index}: {error}")
            return False
            
        return True

    def _validate_notas_alumnos_structure(self, data):
        """Validates notas_alumnos JSON structure"""
        if not isinstance(data, dict):
            self._validation_error("Root must be an object")
            return False
            
        if 'notas' not in data:
            self._validation_error("Missing 'notas' key")
            return False
            
        if not isinstance(data['notas'], list):
            self._validation_error("'notas' must be an array")
            return False
            
        return True

    def _validate_nota_fields(self, entry, index):
        """Validates individual nota fields"""
        errors = []
        
        required_fields = ['alumno_id', 'topico_id', 'instancia', 'nota']
        for field in required_fields:
            if field not in entry:
                errors.append(f"Missing required field '{field}'")
        
        if 'alumno_id' in entry and not self._is_valid_id(entry['alumno_id']):
            errors.append("'alumno_id' must be a positive integer")
            
        if 'topico_id' in entry and not self._is_valid_id(entry['topico_id']):
            errors.append("'topico_id' must be a positive integer")
            
        if 'instancia' in entry and not self._is_valid_instance_number(entry['instancia']):
            errors.append("'instancia' must be a positive integer")
            
        if 'nota' in entry and not self._is_valid_grade(entry['nota']):
            errors.append("'nota' must be between 1.0 and 7.0")
        
        if errors:
            for error in errors:
                self._validation_error(f"Nota {index}: {error}")
            return False
            
        return True

    def _validate_alumno_fields(self, alumno, index):
        """Validates individual alumno fields"""
        errors = []
        
        # Required fields
        required_fields = ['id', 'nombre', 'correo', 'anio_ingreso']
        for field in required_fields:
            if field not in alumno:
                errors.append(f"Missing required field '{field}'")
        
        # Field validations
        if 'id' in alumno and not self._is_valid_id(alumno['id']):
            errors.append("'id' must be a positive integer")
            
        if 'nombre' in alumno and not self._is_valid_name(alumno['nombre']):
            errors.append("'nombre' must be a non-empty string (max 100 chars)")
            
        if 'correo' in alumno and not self._is_valid_email(alumno['correo']):
            errors.append("'correo' must be a valid email address (max 100 chars)")
            
        if 'anio_ingreso' in alumno and not self._is_valid_year(alumno['anio_ingreso']):
            errors.append("'anio_ingreso' must be a valid year (1990-2050)")
        
        if errors:
            for error in errors:
                self._validation_error(f"Alumno {index}: {error}")
            return False
            
        return True

    def _validate_profesores_structure(self, data):
        """Validates profesores JSON structure"""
        if not isinstance(data, dict):
            self._validation_error("Root must be an object")
            return False
            
        if 'profesores' not in data:
            self._validation_error("Missing 'profesores' key")
            return False
            
        if not isinstance(data['profesores'], list):
            self._validation_error("'profesores' must be an array")
            return False
            
        return True

    def _validate_profesor_fields(self, profesor, index):
        """Validates individual profesor fields"""
        errors = []
        
        # Required fields
        required_fields = ['id', 'nombre', 'correo']
        for field in required_fields:
            if field not in profesor:
                errors.append(f"Missing required field '{field}'")
        
        # Field validations
        if 'id' in profesor and not self._is_valid_id(profesor['id']):
            errors.append("'id' must be a positive integer")
            
        if 'nombre' in profesor and not self._is_valid_name(profesor['nombre']):
            errors.append("'nombre' must be a non-empty string (max 100 chars)")
            
        if 'correo' in profesor and not self._is_valid_email(profesor['correo']):
            errors.append("'correo' must be a valid email address (max 100 chars)")
        
        if errors:
            for error in errors:
                self._validation_error(f"Profesor {index}: {error}")
            return False
            
        return True

    def _validate_cursos_structure(self, data):
        """Validates cursos JSON structure"""
        if not isinstance(data, dict):
            self._validation_error("Root must be an object")
            return False
            
        if 'cursos' not in data:
            self._validation_error("Missing 'cursos' key")
            return False
            
        if not isinstance(data['cursos'], list):
            self._validation_error("'cursos' must be an array")
            return False
            
        return True

    def _validate_curso_fields(self, curso, index):
        """Validates individual curso fields"""
        errors = []
        
        # Required fields
        required_fields = ['id', 'codigo', 'descripcion', 'creditos', 'requisitos']
        for field in required_fields:
            if field not in curso:
                errors.append(f"Missing required field '{field}'")
        
        # Field validations
        if 'id' in curso and not self._is_valid_id(curso['id']):
            errors.append("'id' must be a positive integer")
            
        if 'codigo' in curso and not self._is_valid_nrc(curso['codigo']):
            errors.append("'codigo' must be a non-empty string (max 50 chars)")
            
        if 'descripcion' in curso and not self._is_valid_name(curso['descripcion']):
            errors.append("'descripcion' must be a non-empty string (max 100 chars)")
            
        if 'creditos' in curso and not self._is_valid_credits(curso['creditos']):
            errors.append("'creditos' must be an integer between 1 and 99")
            
        if 'requisitos' in curso and not isinstance(curso['requisitos'], list):
            errors.append("'requisitos' must be an array")
        
        if errors:
            for error in errors:
                self._validation_error(f"Curso {index}: {error}")
            return False
            
        return True

    def _validate_salas_structure(self, data):
        """Validates salas JSON structure"""
        if not isinstance(data, dict):
            self._validation_error("Root must be an object")
            return False
            
        if 'salas' not in data:
            self._validation_error("Missing 'salas' key")
            return False
            
        if not isinstance(data['salas'], list):
            self._validation_error("'salas' must be an array")
            return False
            
        return True

    def _validate_sala_fields(self, sala, index):
        """Validates individual sala fields"""
        errors = []
        
        # Required fields
        required_fields = ['id', 'nombre', 'capacidad']
        for field in required_fields:
            if field not in sala:
                errors.append(f"Missing required field '{field}'")
        
        # Field validations
        if 'id' in sala and not self._is_valid_id(sala['id']):
            errors.append("'id' must be a positive integer")
            
        if 'nombre' in sala and not self._is_valid_name(sala['nombre']):
            errors.append("'nombre' must be a non-empty string (max 100 chars)")
            
        if 'capacidad' in sala and not self._is_valid_capacity(sala['capacidad']):
            errors.append("'capacidad' must be a positive integer")
        
        if errors:
            for error in errors:
                self._validation_error(f"Sala {index}: {error}")
            return False
            
        return True

    # ----- Validation Methods ---
    def _validate_alumnos_data(self, data):
        """Validates complete alumnos data"""
        if not self._validate_alumnos_structure(data):
            return False
            
        for index, alumno in enumerate(data['alumnos']):
            if not self._validate_alumno_fields(alumno, index):
                return False
                
        return True

    def _validate_profesores_data(self, data):
        """Validates complete profesores data"""
        if not self._validate_profesores_structure(data):
            return False
            
        for index, profesor in enumerate(data['profesores']):
            if not self._validate_profesor_fields(profesor, index):
                return False
                
        return True

    def _validate_cursos_data(self, data):
        """Validates complete cursos data"""
        if not self._validate_cursos_structure(data):
            return False
            
        for index, curso in enumerate(data['cursos']):
            if not self._validate_curso_fields(curso, index):
                return False
                
        return True

    def _validate_salas_data(self, data):
        """Validates complete salas data"""
        if not self._validate_salas_structure(data):
            return False
            
        for index, sala in enumerate(data['salas']):
            if not self._validate_sala_fields(sala, index):
                return False
                
        return True

    def import_json(self, file, file_type):
        data = json.load(file)

        # Validate data before importing
        validation_methods = {
            'alumnos': self._validate_alumnos_data,
            'profesores': self._validate_profesores_data,
            'cursos': self._validate_cursos_data,
            'salas_clases': self._validate_salas_data,
            'instancias_cursos': self._validate_instancias_cursos_data,
            'instancias_cursos_secciones': self._validate_secciones_data,
            'alumnos_seccion': self._validate_alumnos_seccion_data,
            'notas_alumnos': self._validate_notas_alumnos_data
        }

        if file_type in validation_methods:
            if not validation_methods[file_type](data):
                raise ValueError(f"Validation failed for {file_type}")

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

    # ----- solution FUNCTION SIZE and SEPARATION OF QUERY AND COMMAND error ---
    def _get_professor_id_by_import_id(self, cursor, profesor_import_id):
        """Query: Gets professor ID by import_id"""
        cursor.execute("""
            SELECT id FROM Users WHERE import_id = %s AND is_professor = TRUE
        """, (profesor_import_id,))
        result = cursor.fetchone()
        return result["id"] if result else None
    
    def _get_next_section_number(self, cursor, instancia_id):
        """Query: Gets the next available section number for an instance"""
        cursor.execute("""
            SELECT COUNT(*) FROM Sections WHERE instance_id = %s
        """, (instancia_id,))
        current_count = cursor.fetchone()['COUNT(*)']
        return current_count + 1
    
    def _insert_section(self, cursor, seccion_id, instancia_id, number, profesor_id, weight_or_percentage):
        """Command: Inserts a new section into the database"""
        cursor.execute("""
            INSERT INTO Sections (id, instance_id, number, professor_id, weight_or_percentage)
            VALUES (%s, %s, %s, %s, %s)
        """, (seccion_id, instancia_id, number, profesor_id, weight_or_percentage))
    
    def _insert_topic(self, cursor, topic_id, seccion_id, topic_name, topic_valor, topic_weight_or_percentage):
        """Command: Inserts a new topic into the database"""
        cursor.execute("""
            INSERT INTO Topics (id, section_id, name, weight, weight_or_percentage)
            VALUES (%s, %s, %s, %s, %s)
        """, (topic_id, seccion_id, topic_name, topic_valor, topic_weight_or_percentage))
    
    def _insert_activity(self, cursor, topic_id, activity_weight, optional_flag, instance_number):
        """Command: Inserts a new activity into the database"""
        cursor.execute("""
            INSERT INTO Activities (topic_id, weight, optional_flag, instance)
            VALUES (%s, %s, %s, %s)
        """, (topic_id, activity_weight, optional_flag, instance_number))
    
    def _process_topic_activities(self, cursor, topic_id, topic_eval):
        """Processes and inserts all activities for a topic"""
        valores = topic_eval["valores"]
        obligatorias = topic_eval["obligatorias"]
        
        for i, (valor, obligatorio) in enumerate(zip(valores, obligatorias)):
            activity_weight = valor * 10
            optional_flag = not obligatorio
            instance_number = i + 1
            
            try:
                self._insert_activity(cursor, topic_id, activity_weight, optional_flag, instance_number)
                self._success(f"Inserted Activity {i} for Topic ID {topic_id}")
            except Exception as e:
                self._error(f"Inserting Activity {i} for Topic ID {topic_id}: {e}")
    
    def _process_section_topics(self, cursor, seccion_id, combinacion_topicos, topicos_dict):
        """Processes and inserts all topics for a section"""
        for topic in combinacion_topicos:
            topic_id = topic["id"]
            topic_name = topic["nombre"]
            topic_valor = topic["valor"] * 10
            
            topic_eval = topicos_dict[str(topic_id)]
            topic_eval_tipo = topic_eval["tipo"]
            topic_weight_or_percentage = topic_eval_tipo == "peso"
            
            try:
                self._insert_topic(cursor, topic_id, seccion_id, topic_name, topic_valor, topic_weight_or_percentage)
                self._success(f"Inserted Topic ID {topic_id} for Section ID {seccion_id}")
                
                self._process_topic_activities(cursor, topic_id, topic_eval)
                
            except Exception as e:
                self._error(f"Inserting Topic ID {topic_id} in Section ID {seccion_id}: {e}")
    
    def _process_single_section(self, cursor, seccion):
        """Processes and inserts a single section with its topics and activities"""
        seccion_id = seccion["id"]
        instancia_id = seccion["instancia_curso"]
        profesor_import_id = seccion["profesor_id"]
        tipo_evaluacion = seccion["evaluacion"]["tipo"]
        combinacion_topicos = seccion["evaluacion"]["combinacion_topicos"]
        topicos_dict = seccion["evaluacion"]["topicos"]
        
        # Get professor ID
        profesor_id = self._get_professor_id_by_import_id(cursor, profesor_import_id)
        if not profesor_id:
            self._error(f"No professor found with import_id {profesor_import_id}")
            return
        
        # Get next section number
        try:
            number = self._get_next_section_number(cursor, instancia_id)
        except Exception as e:
            self._error(f"Counting sections for instance_id {instancia_id}: {e}")
            return
        
        # Insert section
        weight_or_percentage = tipo_evaluacion == "peso"
        
        try:
            self._insert_section(cursor, seccion_id, instancia_id, number, profesor_id, weight_or_percentage)
            self._success(f"Inserted Section ID {seccion_id}")
            
            self._process_section_topics(cursor, seccion_id, combinacion_topicos, topicos_dict)
            
        except Exception as e:
            self._error(f"Inserting Section ID {seccion_id}: {e}")

    def _import_instancias_cursos_secciones(self, data):
        """Imports course instance sections with their topics and activities"""
        cursor = self.db.connect()
        secciones = data["secciones"]

        for seccion in secciones:
            self._process_single_section(cursor, seccion)

        self.db.commit()
    # ----- solution FUNCTION SIZE and SEPARATION OF QUERY AND COMMAND error ---

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