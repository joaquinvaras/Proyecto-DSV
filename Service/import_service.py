"""Import Service module for JSON data imports.

This module provides comprehensive JSON data validation and import functionality
for the academic management system, including students, professors, courses,
instances, sections, enrollments, grades, and room data.
"""

import json
import re
from datetime import datetime
from db import DatabaseConnection


class ImportService:
    """Service class for importing and validating JSON data."""

    def __init__(self):
        """Initialize the import service with database connection."""
        self.db = DatabaseConnection()

    def _success(self, message):
        """Print success message."""
        print(f"[SUCCESS] {message}")

    def _error(self, message):
        """Print error message."""
        print(f"[ERROR] {message}")

    def _validation_error(self, message):
        """Print validation error message."""
        print(f"[VALIDATION ERROR] {message}")

    # ----- Basic Validations ---
    def _is_valid_email(self, email):
        """Validate email format."""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _is_valid_name(self, name):
        """Validate name field."""
        if not name or not isinstance(name, str):
            return False
        return len(name.strip()) > 0 and len(name) <= 100

    def _is_valid_nrc(self, nrc):
        """Validate NRC code format."""
        if not nrc or not isinstance(nrc, str):
            return False
        return len(nrc.strip()) > 0 and len(nrc) <= 50

    def _is_valid_year(self, year):
        """Validate year format."""
        if not isinstance(year, int):
            return False
        return 1990 <= year <= 2050

    def _is_valid_semester(self, semester):
        """Validate semester format."""
        if not isinstance(semester, int):
            return False
        return semester in [1, 2]

    def _is_valid_credits(self, course_credits):
        """Validate credits field."""
        if not isinstance(course_credits, int):
            return False
        return 1 <= course_credits <= 99

    def _is_valid_capacity(self, capacity):
        """Validate room capacity."""
        if not isinstance(capacity, int):
            return False
        return capacity > 0

    def _is_valid_grade(self, grade):
        """Validate grade value."""
        if not isinstance(grade, (int, float)):
            return False
        return 1.0 <= float(grade) <= 7.0

    def _is_valid_id(self, id_value):
        """Validate ID field."""
        if not isinstance(id_value, int):
            return False
        return id_value > 0

    def _is_valid_instance_number(self, instance):
        """Validate instance number."""
        if not isinstance(instance, int):
            return False
        return instance > 0

    def _is_valid_percentage_value(self, value):
        """Validate percentage value (0.0-100.0 for topic combination)."""
        if not isinstance(value, (int, float)):
            return False
        return 0.0 <= float(value) <= 100.0

    def _is_valid_activity_value(self, value):
        """Validate activity weight/percentage value (any positive number)."""
        if not isinstance(value, (int, float)):
            return False
        return float(value) > 0

    def _is_valid_evaluation_type(self, tipo):
        """Validate evaluation type."""
        if not isinstance(tipo, str):
            return False
        return tipo in ["peso", "porcentaje"]

    # ----- Structure Validations ---
    def _validate_alumnos_structure(self, data):
        """Validate alumnos JSON structure."""
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

    # ----- Logic Validations ---
    def _validate_unique_emails_across_types(self, data, file_type):
        """Validate that emails are unique across all users being imported."""
        if file_type in ['alumnos', 'profesores']:
            emails = []
            users_key = 'alumnos' if file_type == 'alumnos' else 'profesores'

            for user in data[users_key]:
                email = user.get('correo', '').lower()
                if email in emails:
                    self._validation_error(f"Duplicate email found: {email}")
                    return False
                emails.append(email)
        return True

    def _validate_unique_import_ids(self, data, file_type):
        """Validate that import_ids are unique within the file."""
        if file_type in ['alumnos', 'profesores']:
            import_ids = []
            users_key = 'alumnos' if file_type == 'alumnos' else 'profesores'

            for user in data[users_key]:
                import_id = user.get('id')
                if import_id in import_ids:
                    self._validation_error(f"Duplicate import_id found: "
                                          f"{import_id}")
                    return False
                import_ids.append(import_id)
        return True

    def _validate_admission_dates_logic(self, data):
        """Validate that admission dates are logical (not future, not old)."""
        current_year = datetime.now().year

        for index, alumno in enumerate(data['alumnos']):
            year = alumno.get('anio_ingreso')
            if year and (year > current_year or year < 1950):
                self._validation_error(f"Alumno {index}: Admission year "
                                      f"{year} is not logical")
                return False
        return True

    def _validate_percentage_sum_per_topic(self, data):
        """Validate that percentages sum to 100% for each topic."""
        for sec_index, seccion in enumerate(data['secciones']):
            topicos_dict = seccion['evaluacion']['topicos']

            for topic_id, topic_eval in topicos_dict.items():
                if topic_eval['tipo'] == 'porcentaje':
                    valores = topic_eval['valores']
                    total = sum(valores)

                    if abs(total - 100.0) > 0.1:
                        self._validation_error(
                            f"Section {sec_index}, Topic {topic_id}: "
                            f"Percentages sum to {total:.1f}%, must be 100%"
                        )
                        return False
        return True

    def _validate_topic_combination_percentages(self, data):
        """Validate that topic combination percentages sum to 100%."""
        for sec_index, seccion in enumerate(data['secciones']):
            if seccion['evaluacion']['tipo'] == 'porcentaje':
                combinacion = seccion['evaluacion']['combinacion_topicos']
                total_valor = sum(topic['valor'] for topic in combinacion)

                if abs(total_valor - 100.0) > 0.1:
                    self._validation_error(
                        f"Section {sec_index}: Topic combination sums to "
                        f"{total_valor:.1f}%, must be 100%"
                    )
                    return False
        return True

    def _validate_at_least_one_mandatory_activity(self, data):
        """Validate that each topic has at least one mandatory activity."""
        for sec_index, seccion in enumerate(data['secciones']):
            topicos_dict = seccion['evaluacion']['topicos']

            for topic_id, topic_eval in topicos_dict.items():
                obligatorias = topic_eval['obligatorias']

                if not any(obligatorias):
                    self._validation_error(
                        f"Section {sec_index}, Topic {topic_id}: "
                        "Must have at least one mandatory activity"
                    )
                    return False
        return True

    def _validate_weight_values_are_positive(self, data):
        """Validate that all weight values are positive."""
        for sec_index, seccion in enumerate(data['secciones']):
            topicos_dict = seccion['evaluacion']['topicos']

            for topic_id, topic_eval in topicos_dict.items():
                valores = topic_eval['valores']

                for i, valor in enumerate(valores):
                    if valor <= 0:
                        self._validation_error(
                            f"Section {sec_index}, Topic {topic_id}, "
                            f"Activity {i}: Weight/percentage value must be "
                            f"positive, got {valor}"
                        )
                        return False

                    if (topic_eval['tipo'] == 'porcentaje'
                            and valor > 100.0):
                        self._validation_error(
                            f"Section {sec_index}, Topic {topic_id}, "
                            f"Activity {i}: Percentage value cannot exceed "
                            f"100%, got {valor}"
                        )
                        return False
        return True

    def _validate_course_prerequisites_exist(self, data):
        """Validate that prerequisite courses exist in the same data."""
        course_codes = {curso['codigo'] for curso in data['cursos']}

        for index, curso in enumerate(data['cursos']):
            for prereq_code in curso['requisitos']:
                if prereq_code not in course_codes:
                    self._validation_error(
                        f"Curso {index}: Prerequisite '{prereq_code}' not "
                        "found in courses list"
                    )
                    return False
        return True

    def _validate_no_circular_prerequisites(self, data):
        """Validate that there are no circular dependencies in prerequisites."""
        def has_circular_dependency(course_code, prerequisites_map, visited,
                                    rec_stack):
            visited.add(course_code)
            rec_stack.add(course_code)

            for prereq in prerequisites_map.get(course_code, []):
                if prereq not in visited:
                    if has_circular_dependency(prereq, prerequisites_map,
                                               visited, rec_stack):
                        return True
                elif prereq in rec_stack:
                    return True

            rec_stack.remove(course_code)
            return False

        prereq_map = {}
        for curso in data['cursos']:
            prereq_map[curso['codigo']] = curso['requisitos']

        visited = set()
        for course_code in prereq_map:
            if course_code not in visited:
                rec_stack = set()
                if has_circular_dependency(course_code, prereq_map, visited,
                                           rec_stack):
                    self._validation_error(f"Circular dependency detected "
                                          f"involving course: {course_code}")
                    return False

        return True

    def _validate_self_prerequisites(self, data):
        """Validate that courses don't have themselves as prerequisites."""
        for index, curso in enumerate(data['cursos']):
            course_code = curso['codigo']
            if course_code in curso['requisitos']:
                self._validation_error(f"Curso {index}: Course cannot be "
                                      f"prerequisite of itself: {course_code}")
                return False
        return True

    def _validate_grades_within_valid_range(self, data):
        """Validate that all grades are within the valid range."""
        for index, entry in enumerate(data['notas']):
            nota = entry['nota']
            if not (1.0 <= nota <= 7.0):
                self._validation_error(f"Nota {index}: Grade {nota} is "
                                      "outside valid range (1.0-7.0)")
                return False
        return True

    def _validate_no_duplicate_enrollments(self, data):
        """Validate that students aren't enrolled multiple times in section."""
        enrollments = set()

        for index, entry in enumerate(data['alumnos_seccion']):
            key = (entry['alumno_id'], entry['seccion_id'])
            if key in enrollments:
                self._validation_error(
                    f"Enrollment {index}: Duplicate enrollment - "
                    f"Student {entry['alumno_id']} already enrolled in "
                    f"section {entry['seccion_id']}"
                )
                return False
            enrollments.add(key)
        return True

    def _validate_no_duplicate_grades(self, data):
        """Validate that there are no duplicate grades for student/activity."""
        grades = set()

        for index, entry in enumerate(data['notas']):
            key = (entry['alumno_id'], entry['topico_id'], entry['instancia'])
            if key in grades:
                self._validation_error(
                    f"Grade {index}: Duplicate grade - "
                    f"Student {entry['alumno_id']} already has grade for "
                    f"topic {entry['topico_id']} instance "
                    f"{entry['instancia']}"
                )
                return False
            grades.add(key)
        return True

    def _validate_room_capacity_logic(self, data):
        """Validate that room capacities are reasonable."""
        for index, sala in enumerate(data['salas']):
            capacity = sala['capacidad']
            if capacity > 1000:
                self._validation_error(f"Room {index}: Capacity {capacity} "
                                      "seems unreasonably high")
                return False
            if capacity < 5:
                self._validation_error(f"Room {index}: Capacity {capacity} "
                                      "seems too low for a classroom")
                return False
        return True

    def _validate_credits_range(self, data):
        """Validate that course credits are in reasonable range."""
        for index, curso in enumerate(data['cursos']):
            course_credits = curso['creditos']
            if course_credits > 20:
                self._validation_error(f"Course {index}: {course_credits} "
                                      "credits seems unreasonably high")
                return False
        return True

    # ----- Advanced Validation Methods ---
    def _validate_cursos_data_advanced(self, data):
        """Enhanced validation for cursos with advanced logic."""
        if not self._validate_cursos_data(data):
            return False

        validations = [
            self._validate_course_prerequisites_exist(data),
            self._validate_no_circular_prerequisites(data),
            self._validate_self_prerequisites(data),
            self._validate_credits_range(data)
        ]

        return all(validations)

    def _validate_alumnos_data_advanced(self, data):
        """Enhanced validation for alumnos with advanced logic."""
        if not self._validate_alumnos_data(data):
            return False

        validations = [
            self._validate_unique_emails_across_types(data, 'alumnos'),
            self._validate_unique_import_ids(data, 'alumnos'),
            self._validate_admission_dates_logic(data)
        ]

        return all(validations)

    def _validate_profesores_data_advanced(self, data):
        """Enhanced validation for profesores with advanced logic."""
        if not self._validate_profesores_data(data):
            return False

        validations = [
            self._validate_unique_emails_across_types(data, 'profesores'),
            self._validate_unique_import_ids(data, 'profesores')
        ]

        return all(validations)

    def _validate_secciones_data_advanced(self, data):
        """Enhanced validation for secciones with advanced logic."""
        if not self._validate_secciones_data(data):
            return False

        validations = [
            self._validate_percentage_sum_per_topic(data),
            self._validate_topic_combination_percentages(data),
            self._validate_at_least_one_mandatory_activity(data),
            self._validate_weight_values_are_positive(data)
        ]

        return all(validations)

    def _validate_alumnos_seccion_data_advanced(self, data):
        """Enhanced validation for alumnos_seccion with advanced logic."""
        if not self._validate_alumnos_seccion_data(data):
            return False

        validations = [
            self._validate_no_duplicate_enrollments(data)
        ]

        return all(validations)

    def _validate_notas_alumnos_data_advanced(self, data):
        """Enhanced validation for notas with advanced logic."""
        if not self._validate_notas_alumnos_data(data):
            return False

        validations = [
            self._validate_no_duplicate_grades(data),
            self._validate_grades_within_valid_range(data)
        ]

        return all(validations)

    def _validate_salas_data_advanced(self, data):
        """Enhanced validation for salas with advanced logic."""
        if not self._validate_salas_data(data):
            return False

        validations = [
            self._validate_room_capacity_logic(data)
        ]

        return all(validations)

    # ----- Structure and Field Validation Methods ---
    def _validate_instancias_cursos_data(self, data):
        """Validate complete instancias_cursos data."""
        if not self._validate_instancias_cursos_structure(data):
            return False

        if not self._validate_instancia_curso_fields(data):
            return False

        for index, instancia in enumerate(data['instancias']):
            if not self._validate_instancia_fields(instancia, index):
                return False

        return True

    def _validate_secciones_data(self, data):
        """Validate complete instancias_cursos_secciones data."""
        if not self._validate_secciones_structure(data):
            return False

        for index, seccion in enumerate(data['secciones']):
            if not self._validate_seccion_fields(seccion, index):
                return False

        return True

    def _validate_alumnos_seccion_data(self, data):
        """Validate complete alumnos_seccion data."""
        if not self._validate_alumnos_seccion_structure(data):
            return False

        for index, entry in enumerate(data['alumnos_seccion']):
            if not self._validate_alumno_seccion_fields(entry, index):
                return False

        return True

    def _validate_notas_alumnos_data(self, data):
        """Validate complete notas_alumnos data."""
        if not self._validate_notas_alumnos_structure(data):
            return False

        for index, entry in enumerate(data['notas']):
            if not self._validate_nota_fields(entry, index):
                return False

        return True

    def _validate_instancias_cursos_structure(self, data):
        """Validate instancias_cursos JSON structure."""
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
        """Validate instancias_cursos fields."""
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
        """Validate individual instancia fields."""
        errors = []

        required_fields = ['id', 'curso_id']
        for field in required_fields:
            if field not in instancia:
                errors.append(f"Missing required field '{field}'")

        if 'id' in instancia and not self._is_valid_id(instancia['id']):
            errors.append("'id' must be a positive integer")

        if ('curso_id' in instancia
                and not self._is_valid_id(instancia['curso_id'])):
            errors.append("'curso_id' must be a positive integer")

        if errors:
            for error in errors:
                self._validation_error(f"Instancia {index}: {error}")
            return False

        return True

    def _validate_secciones_structure(self, data):
        """Validate instancias_cursos_secciones JSON structure."""
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
        """Validate individual seccion fields."""
        errors = []

        required_fields = ['id', 'instancia_curso', 'profesor_id',
                           'evaluacion']
        for field in required_fields:
            if field not in seccion:
                errors.append(f"Missing required field '{field}'")

        if 'id' in seccion and not self._is_valid_id(seccion['id']):
            errors.append("'id' must be a positive integer")

        if ('instancia_curso' in seccion
                and not self._is_valid_id(seccion['instancia_curso'])):
            errors.append("'instancia_curso' must be a positive integer")

        if ('profesor_id' in seccion
                and not self._is_valid_id(seccion['profesor_id'])):
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
        """Validate evaluacion fields."""
        errors = []

        required_fields = ['tipo', 'combinacion_topicos', 'topicos']
        for field in required_fields:
            if field not in evaluacion:
                errors.append(f"evaluacion missing '{field}' field")

        if ('tipo' in evaluacion
                and not self._is_valid_evaluation_type(evaluacion['tipo'])):
            errors.append("evaluacion 'tipo' must be 'peso' or 'porcentaje'")

        if 'combinacion_topicos' in evaluacion:
            if not isinstance(evaluacion['combinacion_topicos'], list):
                errors.append("'combinacion_topicos' must be an array")
            else:
                for i, topic in enumerate(evaluacion['combinacion_topicos']):
                    topic_errors = self._validate_topic_combinacion_fields(
                        topic, i)
                    errors.extend(topic_errors)

        if ('topicos' in evaluacion
                and not isinstance(evaluacion['topicos'], dict)):
            errors.append("'topicos' must be an object")

        return errors

    def _validate_topic_combinacion_fields(self, topic, index):
        """Validate topic in combinacion_topicos."""
        errors = []

        required_fields = ['id', 'nombre', 'valor']
        for field in required_fields:
            if field not in topic:
                errors.append(f"combinacion_topicos[{index}] missing "
                             f"'{field}' field")

        if 'id' in topic and not self._is_valid_id(topic['id']):
            errors.append(f"combinacion_topicos[{index}] 'id' must be a "
                         "positive integer")

        if 'nombre' in topic and not self._is_valid_name(topic['nombre']):
            errors.append(f"combinacion_topicos[{index}] 'nombre' must be a "
                         "non-empty string")

        if ('valor' in topic
                and not self._is_valid_percentage_value(topic['valor'])):
            errors.append(f"combinacion_topicos[{index}] 'valor' must be "
                         "between 0.0 and 100.0")

        return errors

    def _validate_alumnos_seccion_structure(self, data):
        """Validate alumnos_seccion JSON structure."""
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
        """Validate individual alumno_seccion fields."""
        errors = []

        required_fields = ['seccion_id', 'alumno_id']
        for field in required_fields:
            if field not in entry:
                errors.append(f"Missing required field '{field}'")

        if ('seccion_id' in entry
                and not self._is_valid_id(entry['seccion_id'])):
            errors.append("'seccion_id' must be a positive integer")

        if ('alumno_id' in entry
                and not self._is_valid_id(entry['alumno_id'])):
            errors.append("'alumno_id' must be a positive integer")

        if errors:
            for error in errors:
                self._validation_error(f"Alumno_seccion {index}: {error}")
            return False

        return True

    def _validate_notas_alumnos_structure(self, data):
        """Validate notas_alumnos JSON structure."""
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
        """Validate individual nota fields."""
        errors = []

        required_fields = ['alumno_id', 'topico_id', 'instancia', 'nota']
        for field in required_fields:
            if field not in entry:
                errors.append(f"Missing required field '{field}'")

        if ('alumno_id' in entry
                and not self._is_valid_id(entry['alumno_id'])):
            errors.append("'alumno_id' must be a positive integer")

        if ('topico_id' in entry
                and not self._is_valid_id(entry['topico_id'])):
            errors.append("'topico_id' must be a positive integer")

        if ('instancia' in entry
                and not self._is_valid_instance_number(entry['instancia'])):
            errors.append("'instancia' must be a positive integer")

        if 'nota' in entry and not self._is_valid_grade(entry['nota']):
            errors.append("'nota' must be between 1.0 and 7.0")

        if errors:
            for error in errors:
                self._validation_error(f"Nota {index}: {error}")
            return False

        return True

    def _validate_alumno_fields(self, alumno, index):
        """Validate individual alumno fields."""
        errors = []

        required_fields = ['id', 'nombre', 'correo', 'anio_ingreso']
        for field in required_fields:
            if field not in alumno:
                errors.append(f"Missing required field '{field}'")

        if 'id' in alumno and not self._is_valid_id(alumno['id']):
            errors.append("'id' must be a positive integer")

        if 'nombre' in alumno and not self._is_valid_name(alumno['nombre']):
            errors.append("'nombre' must be a non-empty string (max 100 "
                         "chars)")

        if 'correo' in alumno and not self._is_valid_email(alumno['correo']):
            errors.append("'correo' must be a valid email address (max 100 "
                         "chars)")

        if ('anio_ingreso' in alumno
                and not self._is_valid_year(alumno['anio_ingreso'])):
            errors.append("'anio_ingreso' must be a valid year (1990-2050)")

        if errors:
            for error in errors:
                self._validation_error(f"Alumno {index}: {error}")
            return False

        return True

    def _validate_profesores_structure(self, data):
        """Validate profesores JSON structure."""
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
        """Validate individual profesor fields."""
        errors = []

        required_fields = ['id', 'nombre', 'correo']
        for field in required_fields:
            if field not in profesor:
                errors.append(f"Missing required field '{field}'")

        if 'id' in profesor and not self._is_valid_id(profesor['id']):
            errors.append("'id' must be a positive integer")

        if ('nombre' in profesor
                and not self._is_valid_name(profesor['nombre'])):
            errors.append("'nombre' must be a non-empty string (max 100 "
                         "chars)")

        if ('correo' in profesor
                and not self._is_valid_email(profesor['correo'])):
            errors.append("'correo' must be a valid email address (max 100 "
                         "chars)")

        if errors:
            for error in errors:
                self._validation_error(f"Profesor {index}: {error}")
            return False

        return True

    def _validate_cursos_structure(self, data):
        """Validate cursos JSON structure."""
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
        """Validate individual curso fields."""
        errors = []

        required_fields = ['id', 'codigo', 'descripcion', 'creditos',
                           'requisitos']
        for field in required_fields:
            if field not in curso:
                errors.append(f"Missing required field '{field}'")

        if 'id' in curso and not self._is_valid_id(curso['id']):
            errors.append("'id' must be a positive integer")

        if 'codigo' in curso and not self._is_valid_nrc(curso['codigo']):
            errors.append("'codigo' must be a non-empty string (max 50 "
                         "chars)")

        if ('descripcion' in curso
                and not self._is_valid_name(curso['descripcion'])):
            errors.append("'descripcion' must be a non-empty string (max "
                         "100 chars)")

        if ('creditos' in curso
                and not self._is_valid_credits(curso['creditos'])):
            errors.append("'creditos' must be an integer between 1 and 99")

        if ('requisitos' in curso
                and not isinstance(curso['requisitos'], list)):
            errors.append("'requisitos' must be an array")

        if errors:
            for error in errors:
                self._validation_error(f"Curso {index}: {error}")
            return False

        return True

    def _validate_salas_structure(self, data):
        """Validate salas JSON structure."""
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
        """Validate individual sala fields."""
        errors = []

        required_fields = ['id', 'nombre', 'capacidad']
        for field in required_fields:
            if field not in sala:
                errors.append(f"Missing required field '{field}'")

        if 'id' in sala and not self._is_valid_id(sala['id']):
            errors.append("'id' must be a positive integer")

        if 'nombre' in sala and not self._is_valid_name(sala['nombre']):
            errors.append("'nombre' must be a non-empty string (max 100 "
                         "chars)")

        if ('capacidad' in sala
                and not self._is_valid_capacity(sala['capacidad'])):
            errors.append("'capacidad' must be a positive integer")

        if errors:
            for error in errors:
                self._validation_error(f"Sala {index}: {error}")
            return False

        return True

    # ----- Validation Methods ---
    def _validate_alumnos_data(self, data):
        """Validate complete alumnos data."""
        if not self._validate_alumnos_structure(data):
            return False

        for index, alumno in enumerate(data['alumnos']):
            if not self._validate_alumno_fields(alumno, index):
                return False

        return True

    def _validate_profesores_data(self, data):
        """Validate complete profesores data."""
        if not self._validate_profesores_structure(data):
            return False

        for index, profesor in enumerate(data['profesores']):
            if not self._validate_profesor_fields(profesor, index):
                return False

        return True

    def _validate_cursos_data(self, data):
        """Validate complete cursos data."""
        if not self._validate_cursos_structure(data):
            return False

        for index, curso in enumerate(data['cursos']):
            if not self._validate_curso_fields(curso, index):
                return False

        return True

    def _validate_salas_data(self, data):
        """Validate complete salas data."""
        if not self._validate_salas_structure(data):
            return False

        for index, sala in enumerate(data['salas']):
            if not self._validate_sala_fields(sala, index):
                return False

        return True

    # ----- Import Methods ---
    def import_json(self, file, file_type):
        """Import JSON data based on file type with validation."""
        data = json.load(file)

        validation_methods = {
            'alumnos': self._validate_alumnos_data_advanced,
            'profesores': self._validate_profesores_data_advanced,
            'cursos': self._validate_cursos_data_advanced,
            'salas_clases': self._validate_salas_data_advanced,
            'instancias_cursos': self._validate_instancias_cursos_data,
            'instancias_cursos_secciones': (
                self._validate_secciones_data_advanced),
            'alumnos_seccion': self._validate_alumnos_seccion_data_advanced,
            'notas_alumnos': self._validate_notas_alumnos_data_advanced
        }

        if file_type in validation_methods:
            if not validation_methods[file_type](data):
                raise ValueError(f"Validation failed for {file_type}")

        match file_type:
            case 'alumnos':
                self._import_alumnos(data)
            case 'profesores':
                self._import_profesores(data)
            case 'cursos':
                self._import_cursos(data)
            case 'instancias_cursos':
                self._import_instancias_cursos(data)
            case 'instancias_cursos_secciones':
                self._import_instancias_cursos_secciones(data)
            case 'alumnos_seccion':
                self._import_alumnos_seccion(data)
            case 'notas_alumnos':
                self._import_notas_alumnos(data)
            case 'salas_clases':
                self._import_salas_clases(data)
            case _:
                raise ValueError(f"Tipo de archivo no soportado: {file_type}")

    def _import_alumnos(self, data):
        """Import student data."""
        cursor = self.db.connect()
        for alumno in data['alumnos']:
            import_id = alumno['id']
            name = alumno['nombre']
            email = alumno['correo']
            admission_date = f"{alumno['anio_ingreso']}-01-01"
            is_professor = False

            query = """
                INSERT INTO Users (import_id, name, email, admission_date,
                                   is_professor)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (import_id, name, email, admission_date, is_professor)

            try:
                cursor.execute(query, values)
                self._success(f"Imported alumno: {name} ({email})")
            except (ValueError, KeyError) as err:
                self._error(f"Inserting alumno {name} ({email}): {err}")

        self.db.commit()

    def _import_profesores(self, data):
        """Import professor data."""
        cursor = self.db.connect()
        for profesor in data['profesores']:
            import_id = profesor['id']
            name = profesor['nombre']
            email = profesor['correo']
            admission_date = None
            is_professor = True

            query = """
                INSERT INTO Users (import_id, name, email, admission_date,
                                   is_professor)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (import_id, name, email, admission_date, is_professor)

            try:
                cursor.execute(query, values)
                self._success(f"Imported profesor: {name} ({email})")
            except (ValueError, KeyError) as err:
                self._error(f"Inserting profesor {name} ({email}): {err}")

        self.db.commit()

    def _import_cursos(self, data):
        """Import course data."""
        cursor = self.db.connect()
        cursos = data['cursos']

        for curso in cursos:
            curso_id = curso['id']
            codigo = curso['codigo']
            descripcion = curso['descripcion']
            course_credits = curso['creditos']

            try:
                cursor.execute("""
                    INSERT INTO Courses (id, nrc, name, credits)
                    VALUES (%s, %s, %s, %s)
                """, (curso_id, codigo, descripcion, course_credits))
                self._success(f"Inserted course: {codigo} - {descripcion}")
            except (ValueError, KeyError) as e:
                self._error(f"Inserting course {codigo}: {e}")

        for curso in cursos:
            curso_id = curso['id']
            requisitos = curso['requisitos']

            for cod_requisito in requisitos:
                try:
                    cursor.execute("SELECT id FROM Courses WHERE nrc = %s",
                                   (cod_requisito,))
                    result = cursor.fetchone()
                    if result:
                        prereq_id = result['id']
                        cursor.execute("""
                            INSERT INTO CoursePrerequisites (course_id,
                                                              prerequisite_id)
                            VALUES (%s, %s)
                        """, (curso_id, prereq_id))
                        self._success(f"Added prerequisite {cod_requisito} "
                                     f"for course {curso_id}")
                    else:
                        self._error(f"Prerequisite course with code "
                                   f"{cod_requisito} not found")
                except (ValueError, KeyError) as e:
                    self._error(f"Adding prerequisite {cod_requisito} for "
                               f"course {curso_id}: {e}")

        self.db.commit()

    def _import_instancias_cursos(self, data):
        """Import course instance data."""
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
                self._success(f"Inserted instance {instancia_id} for course "
                             f"{curso_id} in period {period}")
            except (ValueError, KeyError) as e:
                self._error(f"Inserting instance {instancia_id}: {e}")

        self.db.commit()

    def _get_professor_id_by_import_id(self, cursor, profesor_import_id):
        """Query: Get professor ID by import_id."""
        cursor.execute("""
            SELECT id FROM Users WHERE import_id = %s AND is_professor = TRUE
        """, (profesor_import_id,))
        result = cursor.fetchone()
        return result["id"] if result else None

    def _get_next_section_number(self, cursor, instancia_id):
        """Query: Get the next available section number for an instance."""
        cursor.execute("""
            SELECT COUNT(*) FROM Sections WHERE instance_id = %s
        """, (instancia_id,))
        current_count = cursor.fetchone()['COUNT(*)']
        return current_count + 1

    def _insert_section(self, cursor, **section_data):
        """Command: Insert a new section into the database."""
        cursor.execute("""
            INSERT INTO Sections (id, instance_id, number, professor_id,
                                  weight_or_percentage)
            VALUES (%s, %s, %s, %s, %s)
        """, (section_data['seccion_id'], section_data['instancia_id'],
              section_data['number'], section_data['profesor_id'],
              section_data['weight_or_percentage']))

    def _insert_topic(self, cursor, **topic_data):
        """Command: Insert a new topic into the database."""
        cursor.execute("""
            INSERT INTO Topics (id, section_id, name, weight,
                                weight_or_percentage)
            VALUES (%s, %s, %s, %s, %s)
        """, (topic_data['topic_id'], topic_data['seccion_id'],
              topic_data['topic_name'], topic_data['topic_valor'],
              topic_data['topic_weight_or_percentage']))

    def _insert_activity(self, cursor, **activity_data):
        """Command: Insert a new activity into the database."""
        cursor.execute("""
            INSERT INTO Activities (topic_id, weight, optional_flag, instance)
            VALUES (%s, %s, %s, %s)
        """, (activity_data['topic_id'], activity_data['activity_weight'],
              activity_data['optional_flag'],
              activity_data['instance_number']))

    def _process_topic_activities(self, cursor, topic_id, topic_eval):
        """Process and insert all activities for a topic."""
        valores = topic_eval["valores"]
        obligatorias = topic_eval["obligatorias"]

        for i, (valor, obligatorio) in enumerate(zip(valores, obligatorias)):
            activity_weight = valor * 10
            optional_flag = not obligatorio
            instance_number = i + 1

            try:
                self._insert_activity(cursor,
                                      topic_id=topic_id,
                                      activity_weight=activity_weight,
                                      optional_flag=optional_flag,
                                      instance_number=instance_number)
                self._success(f"Inserted Activity {i} for Topic ID "
                             f"{topic_id}")
            except (ValueError, KeyError) as e:
                self._error(f"Inserting Activity {i} for Topic ID "
                           f"{topic_id}: {e}")

    def _process_section_topics(self, cursor, seccion_id, combinacion_topicos,
                                topicos_dict):
        """Process and insert all topics for a section."""
        for topic in combinacion_topicos:
            topic_id = topic["id"]
            topic_name = topic["nombre"]
            topic_valor = topic["valor"] * 10

            topic_eval = topicos_dict[str(topic_id)]
            topic_eval_tipo = topic_eval["tipo"]
            topic_weight_or_percentage = topic_eval_tipo == "porcentaje"

            try:
                self._insert_topic(cursor,
                                   topic_id=topic_id,
                                   seccion_id=seccion_id,
                                   topic_name=topic_name,
                                   topic_valor=topic_valor,
                                   topic_weight_or_percentage=topic_weight_or_percentage)
                self._success(f"Inserted Topic ID {topic_id} for Section ID "
                             f"{seccion_id}")

                self._process_topic_activities(cursor, topic_id, topic_eval)

            except (ValueError, KeyError) as e:
                self._error(f"Inserting Topic ID {topic_id} in Section ID "
                           f"{seccion_id}: {e}")

    def _process_single_section(self, cursor, seccion):
        """Process and insert a single section with topics and activities."""
        seccion_id = seccion["id"]
        instancia_id = seccion["instancia_curso"]
        profesor_import_id = seccion["profesor_id"]
        tipo_evaluacion = seccion["evaluacion"]["tipo"]
        combinacion_topicos = seccion["evaluacion"]["combinacion_topicos"]
        topicos_dict = seccion["evaluacion"]["topicos"]

        profesor_id = self._get_professor_id_by_import_id(cursor,
                                                          profesor_import_id)
        if not profesor_id:
            self._error(f"No professor found with import_id "
                       f"{profesor_import_id}")
            return

        try:
            number = self._get_next_section_number(cursor, instancia_id)
        except (ValueError, KeyError) as e:
            self._error(f"Counting sections for instance_id "
                       f"{instancia_id}: {e}")
            return

        weight_or_percentage = tipo_evaluacion == "porcentaje"

        try:
            self._insert_section(cursor,
                                 seccion_id=seccion_id,
                                 instancia_id=instancia_id,
                                 number=number,
                                 profesor_id=profesor_id,
                                 weight_or_percentage=weight_or_percentage)
            self._success(f"Inserted Section ID {seccion_id}")

            self._process_section_topics(cursor, seccion_id,
                                         combinacion_topicos, topicos_dict)

        except (ValueError, KeyError) as e:
            self._error(f"Inserting Section ID {seccion_id}: {e}")

    def _import_instancias_cursos_secciones(self, data):
        """Import course instance sections with their topics and activities."""
        cursor = self.db.connect()
        secciones = data["secciones"]

        for seccion in secciones:
            self._process_single_section(cursor, seccion)

        self.db.commit()

    def _import_alumnos_seccion(self, data):
        """Import student-section enrollment data."""
        cursor = self.db.connect()
        alumnos_seccion = data["alumnos_seccion"]

        for entry in alumnos_seccion:
            seccion_id = entry["seccion_id"]
            alumno_import_id = entry["alumno_id"]

            try:
                cursor.execute("""
                    SELECT id FROM Users WHERE import_id = %s AND
                           is_professor = FALSE
                """, (alumno_import_id,))
                user_row = cursor.fetchone()

                if not user_row:
                    self._error(f"No user found for alumno_import_id "
                               f"{alumno_import_id}")
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
                    self._error(f"No course found for seccion_id "
                               f"{seccion_id}")
                    continue

                course_id = result['course_id']

                cursor.execute("""
                    INSERT INTO Courses_Taken (user_id, section_id, course_id,
                                               final_grade)
                    VALUES (%s, %s, %s, %s)
                """, (alumno_id, seccion_id, course_id, 0))

                self._success(f"Enrolled alumno_id {alumno_id} in "
                             f"section_id {seccion_id} (course_id "
                             f"{course_id})")

            except (ValueError, KeyError) as e:
                self._error(f"Failed to enroll alumno_import_id "
                           f"{alumno_import_id} in section_id {seccion_id}: "
                           f"{e}")

        self.db.commit()

    def _import_notas_alumnos(self, data):
        """Import student grade data."""
        cursor = self.db.connect()
        for entry in data["notas"]:
            alumno_import_id = entry["alumno_id"]
            topico_id = entry["topico_id"]
            instancia = entry["instancia"]
            nota = entry["nota"]

            try:
                cursor.execute("""
                    SELECT id FROM Users WHERE import_id = %s AND
                           is_professor = FALSE
                """, (alumno_import_id,))
                user_row = cursor.fetchone()

                if not user_row:
                    self._error(f"No user found for alumno_import_id "
                               f"{alumno_import_id}")
                    continue

                alumno_id = user_row["id"]

                cursor.execute("""
                    SELECT id FROM Activities
                    WHERE topic_id = %s AND instance = %s
                """, (topico_id, instancia))
                result = cursor.fetchone()

                if not result:
                    self._error(f"No activity found for topico_id "
                               f"{topico_id} and instancia {instancia}")
                    continue

                activity_id = result["id"]

                cursor.execute("""
                    INSERT INTO Grades (activity_id, user_id, grade)
                    VALUES (%s, %s, %s)
                """, (activity_id, alumno_id, nota))
                self._success(f"Inserted grade for alumno_id {alumno_id}, "
                             f"activity_id {activity_id}: {nota}")
            except (ValueError, KeyError) as e:
                self._error(f"Inserting grade for alumno_id {alumno_id}, "
                           f"topico_id {topico_id}, instancia {instancia}: "
                           f"{e}")

        self.db.commit()

    def _import_salas_clases(self, data):
        """Import classroom data."""
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

                self._success(f"Room inserted: id={room_id}, "
                             f"name='{nombre}', capacidad={capacidad}")

            except (ValueError, KeyError) as e:
                self._error(f"Failed to insert room id={room_id}, "
                           f"name='{nombre}': {e}")

        self.db.commit()
