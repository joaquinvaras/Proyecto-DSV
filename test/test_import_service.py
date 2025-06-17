"""Unit tests for ImportService module.

This module contains comprehensive tests for the ImportService class,
including JSON validation, data import operations, and error handling.
"""

import pytest
import json
from io import StringIO
from unittest.mock import Mock, patch, mock_open
from Service.import_service import ImportService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def import_service(mock_db):
    """Create ImportService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.import_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return ImportService()


def test_init_creates_database_connection():
    """Test that ImportService initializes with database connection."""
    with patch('Service.import_service.DatabaseConnection') as mock_db_class:
        service = ImportService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_is_valid_email_with_valid_emails(import_service):
    """Test email validation with valid email addresses."""
    valid_emails = [
        "test@example.com",
        "user.name@domain.co.uk",
        "student123@university.edu",
        "professor+research@institution.org"
    ]
    
    for email in valid_emails:
        assert import_service._is_valid_email(email) is True


def test_is_valid_email_with_invalid_emails(import_service):
    """Test email validation with invalid email addresses."""
    invalid_emails = [
        "",
        None,
        "invalid-email",
        "@domain.com",
        "user@",
        "user@@domain.com",
        123,
        "user name@domain.com"
    ]
    
    for email in invalid_emails:
        assert import_service._is_valid_email(email) is False


def test_is_valid_name_with_valid_names(import_service):
    """Test name validation with valid names."""
    valid_names = [
        "Juan Pérez",
        "María García-López",
        "José",
        "Ana María de los Santos"
    ]
    
    for name in valid_names:
        assert import_service._is_valid_name(name) is True


def test_is_valid_name_with_invalid_names(import_service):
    """Test name validation with invalid names."""
    invalid_names = [
        "",
        None,
        "   ",
        123,
        "a" * 101,
    ]
    
    for name in invalid_names:
        assert import_service._is_valid_name(name) is False


def test_is_valid_year_with_valid_years(import_service):
    """Test year validation with valid years."""
    valid_years = [1990, 2000, 2025, 2050]
    
    for year in valid_years:
        assert import_service._is_valid_year(year) is True


def test_is_valid_year_with_invalid_years(import_service):
    """Test year validation with invalid years."""
    invalid_years = [1989, 2051, "2025", None, 0]
    
    for year in invalid_years:
        assert import_service._is_valid_year(year) is False


def test_is_valid_semester_with_valid_semesters(import_service):
    """Test semester validation with valid semesters."""
    valid_semesters = [1, 2]
    
    for semester in valid_semesters:
        assert import_service._is_valid_semester(semester) is True


def test_is_valid_semester_with_invalid_semesters(import_service):
    """Test semester validation with invalid semesters."""
    invalid_semesters = [0, 3, "1", None, 1.5]
    
    for semester in invalid_semesters:
        assert import_service._is_valid_semester(semester) is False


def test_is_valid_credits_with_valid_credits(import_service):
    """Test credits validation with valid credit values."""
    valid_credits = [1, 5, 10, 99]
    
    for credits in valid_credits:
        assert import_service._is_valid_credits(credits) is True


def test_is_valid_credits_with_invalid_credits(import_service):
    """Test credits validation with invalid credit values."""
    invalid_credits = [0, 100, "5", None, -1, 1.5]
    
    for credits in invalid_credits:
        assert import_service._is_valid_credits(credits) is False


def test_is_valid_grade_with_valid_grades(import_service):
    """Test grade validation with valid grade values."""
    valid_grades = [1.0, 4.5, 5.8, 7.0, 6]
    
    for grade in valid_grades:
        assert import_service._is_valid_grade(grade) is True


def test_is_valid_grade_with_invalid_grades(import_service):
    """Test grade validation with invalid grade values."""
    invalid_grades = [0.9, 7.1, "5.5", None, -1]
    
    for grade in invalid_grades:
        assert import_service._is_valid_grade(grade) is False


def test_validate_alumnos_structure_valid(import_service):
    """Test validation of valid alumnos structure."""
    valid_data = {
        "alumnos": [
            {"id": 1, "nombre": "Juan", "correo": "juan@test.com", "anio_ingreso": 2020}
        ]
    }
    
    result = import_service._validate_alumnos_structure(valid_data)
    assert result is True


def test_validate_alumnos_structure_invalid(import_service):
    """Test validation of invalid alumnos structure."""
    invalid_data1 = {"students": []}
    result1 = import_service._validate_alumnos_structure(invalid_data1)
    assert result1 is False

    invalid_data2 = {"alumnos": "not a list"}
    result2 = import_service._validate_alumnos_structure(invalid_data2)
    assert result2 is False

    invalid_data3 = "not a dict"
    result3 = import_service._validate_alumnos_structure(invalid_data3)
    assert result3 is False


def test_validate_alumno_fields_valid(import_service):
    """Test validation of valid alumno fields."""
    valid_alumno = {
        "id": 1,
        "nombre": "Juan Pérez",
        "correo": "juan@test.com",
        "anio_ingreso": 2020
    }
    
    result = import_service._validate_alumno_fields(valid_alumno, 0)
    assert result is True


def test_validate_alumno_fields_invalid(import_service):
    """Test validation of invalid alumno fields."""
    invalid_alumno1 = {
        "nombre": "Juan Pérez",
        "correo": "juan@test.com",
        "anio_ingreso": 2020
    }
    result1 = import_service._validate_alumno_fields(invalid_alumno1, 0)
    assert result1 is False

    invalid_alumno2 = {
        "id": 1,
        "nombre": "Juan Pérez",
        "correo": "invalid-email",
        "anio_ingreso": 2020
    }
    result2 = import_service._validate_alumno_fields(invalid_alumno2, 0)
    assert result2 is False


def test_validate_unique_emails_across_types_valid(import_service):
    """Test validation of unique emails in alumnos data."""
    valid_data = {
        "alumnos": [
            {"correo": "juan@test.com"},
            {"correo": "maria@test.com"}
        ]
    }
    
    result = import_service._validate_unique_emails_across_types(valid_data, 'alumnos')
    assert result is True


def test_validate_unique_emails_across_types_invalid(import_service):
    """Test validation when duplicate emails exist."""
    invalid_data = {
        "alumnos": [
            {"correo": "juan@test.com"},
            {"correo": "juan@test.com"}
        ]
    }
    
    result = import_service._validate_unique_emails_across_types(invalid_data, 'alumnos')
    assert result is False


def test_validate_percentage_sum_per_topic_valid(import_service):
    """Test validation when percentages sum to 100%."""
    valid_data = {
        "secciones": [
            {
                "evaluacion": {
                    "topicos": {
                        "1": {
                            "tipo": "porcentaje",
                            "valores": [30.0, 70.0]
                        }
                    }
                }
            }
        ]
    }
    
    result = import_service._validate_percentage_sum_per_topic(valid_data)
    assert result is True


def test_validate_percentage_sum_per_topic_invalid(import_service):
    """Test validation when percentages don't sum to 100%."""
    invalid_data = {
        "secciones": [
            {
                "evaluacion": {
                    "topicos": {
                        "1": {
                            "tipo": "porcentaje",
                            "valores": [30.0, 60.0]
                        }
                    }
                }
            }
        ]
    }
    
    result = import_service._validate_percentage_sum_per_topic(invalid_data)
    assert result is False


# Test import methods
def test_import_alumnos_success(import_service, mock_db):
    """Test successful import of alumnos data."""
    mock_db_instance, mock_cursor = mock_db
    
    data = {
        "alumnos": [
            {
                "id": 1,
                "nombre": "Juan Pérez",
                "correo": "juan@test.com",
                "anio_ingreso": 2020
            }
        ]
    }
    
    import_service._import_alumnos(data)
    
    expected_query = """
                INSERT INTO Users (import_id, name, email, admission_date,
                                   is_professor)
                VALUES (%s, %s, %s, %s, %s)
            """
    mock_cursor.execute.assert_called_with(
        expected_query,
        (1, "Juan Pérez", "juan@test.com", "2020-01-01", False)
    )
    mock_db_instance.commit.assert_called_once()


def test_import_profesores_success(import_service, mock_db):
    """Test successful import of profesores data."""
    mock_db_instance, mock_cursor = mock_db
    
    data = {
        "profesores": [
            {
                "id": 1,
                "nombre": "Dr. García",
                "correo": "garcia@test.com"
            }
        ]
    }
    
    import_service._import_profesores(data)
    
    expected_query = """
                INSERT INTO Users (import_id, name, email, admission_date,
                                   is_professor)
                VALUES (%s, %s, %s, %s, %s)
            """
    mock_cursor.execute.assert_called_with(
        expected_query,
        (1, "Dr. García", "garcia@test.com", None, True)
    )
    mock_db_instance.commit.assert_called_once()


def test_import_cursos_success(import_service, mock_db):
    """Test successful import of cursos data."""
    mock_db_instance, mock_cursor = mock_db
    
    data = {
        "cursos": [
            {
                "id": 1,
                "codigo": "ICC5130",
                "descripcion": "Diseño de Software",
                "creditos": 3,
                "requisitos": []
            }
        ]
    }
    
    import_service._import_cursos(data)
    
    expected_query = """
                    INSERT INTO Courses (id, nrc, name, credits)
                    VALUES (%s, %s, %s, %s)
                """
    mock_cursor.execute.assert_any_call(
        expected_query,
        (1, "ICC5130", "Diseño de Software", 3)
    )
    mock_db_instance.commit.assert_called_once()


def test_import_instancias_cursos_success(import_service, mock_db):
    """Test successful import of instancias cursos data."""
    mock_db_instance, mock_cursor = mock_db
    
    data = {
        "año": 2025,
        "semestre": 1,
        "instancias": [
            {
                "id": 1,
                "curso_id": 1
            }
        ]
    }
    
    import_service._import_instancias_cursos(data)
    
    expected_query = """
                    INSERT INTO Instances (id, period, course_id)
                    VALUES (%s, %s, %s)
                """
    mock_cursor.execute.assert_called_with(
        expected_query,
        (1, "2025-1", 1)
    )
    mock_db_instance.commit.assert_called_once()


def test_import_json_with_valid_alumnos_file(import_service):
    """Test importing JSON file with valid alumnos data."""
    valid_data = {
        "alumnos": [
            {
                "id": 1,
                "nombre": "Juan Pérez",
                "correo": "juan@test.com",
                "anio_ingreso": 2020
            }
        ]
    }
    
    mock_file = StringIO(json.dumps(valid_data))
    
    with patch.object(import_service, '_import_alumnos') as mock_import:
        import_service.import_json(mock_file, 'alumnos')
        mock_import.assert_called_once_with(valid_data)


def test_import_json_with_invalid_file_type(import_service):
    """Test importing JSON file with unsupported file type."""
    mock_file = StringIO('{"data": []}')
    
    with pytest.raises(ValueError, match="Tipo de archivo no soportado"):
        import_service.import_json(mock_file, 'unsupported_type')


def test_import_json_with_validation_failure(import_service):
    """Test importing JSON file that fails validation."""
    invalid_data = {
        "alumnos": "not a list"
    }
    
    mock_file = StringIO(json.dumps(invalid_data))
    
    with pytest.raises(ValueError, match="Validation failed"):
        import_service.import_json(mock_file, 'alumnos')


def test_get_professor_id_by_import_id_found(import_service, mock_db):
    """Test getting professor ID when professor exists."""
    _, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = {"id": 5}
    
    result = import_service._get_professor_id_by_import_id(mock_cursor, 123)
    
    expected_query = """
            SELECT id FROM Users WHERE import_id = %s AND is_professor = TRUE
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (123,))
    assert result == 5


def test_get_professor_id_by_import_id_not_found(import_service, mock_db):
    """Test getting professor ID when professor doesn't exist."""
    _, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = None
    
    result = import_service._get_professor_id_by_import_id(mock_cursor, 999)
    
    assert result is None


def test_get_next_section_number(import_service, mock_db):
    """Test getting next section number for an instance."""
    _, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = {'COUNT(*)': 2}
    
    result = import_service._get_next_section_number(mock_cursor, 1)
    
    expected_query = """
            SELECT COUNT(*) FROM Sections WHERE instance_id = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (1,))
    assert result == 3


@pytest.mark.parametrize("file_type,expected_method", [
    ('alumnos', '_import_alumnos'),
    ('profesores', '_import_profesores'),
    ('cursos', '_import_cursos'),
])
def test_import_json_calls_correct_method_simple(import_service, file_type, expected_method):
    """Test that import_json calls the correct import method for simple cases."""
    valid_data = {"test": "data"}
    mock_file = StringIO(json.dumps(valid_data))
    
    validation_method = f'_validate_{file_type}_data_advanced'
    
    with patch.object(import_service, expected_method) as mock_method, \
         patch.object(import_service, validation_method, return_value=True):
        import_service.import_json(mock_file, file_type)
        mock_method.assert_called_once_with(valid_data)


def test_insert_section_command(import_service, mock_db):
    """Test the command method for inserting sections."""
    _, mock_cursor = mock_db
    section_data = {
        'seccion_id': 1,
        'instancia_id': 1,
        'number': 1,
        'profesor_id': 1,
        'weight_or_percentage': True
    }
    
    import_service._insert_section(mock_cursor, **section_data)
    
    expected_query = """
            INSERT INTO Sections (id, instance_id, number, professor_id,
                                  weight_or_percentage)
            VALUES (%s, %s, %s, %s, %s)
        """
    mock_cursor.execute.assert_called_once_with(
        expected_query,
        (1, 1, 1, 1, True)
    )


def test_insert_topic_command(import_service, mock_db):
    """Test the command method for inserting topics."""
    _, mock_cursor = mock_db
    topic_data = {
        'topic_id': 1,
        'seccion_id': 1,
        'topic_name': 'Controles',
        'topic_valor': 300,
        'topic_weight_or_percentage': True
    }
    
    import_service._insert_topic(mock_cursor, **topic_data)
    
    expected_query = """
            INSERT INTO Topics (id, section_id, name, weight,
                                weight_or_percentage)
            VALUES (%s, %s, %s, %s, %s)
        """
    mock_cursor.execute.assert_called_once_with(
        expected_query,
        (1, 1, 'Controles', 300, True)
    )


def test_insert_activity_command(import_service, mock_db):
    """Test the command method for inserting activities."""
    _, mock_cursor = mock_db
    activity_data = {
        'topic_id': 1,
        'activity_weight': 100,
        'optional_flag': False,
        'instance_number': 1
    }
    
    import_service._insert_activity(mock_cursor, **activity_data)
    
    expected_query = """
            INSERT INTO Activities (topic_id, weight, optional_flag, instance)
            VALUES (%s, %s, %s, %s)
        """
    mock_cursor.execute.assert_called_once_with(
        expected_query,
        (1, 100, False, 1)
    )

def test_success_message_printing(import_service, capsys):
    """Test that success messages are printed correctly."""
    import_service._success("Test message")
    captured = capsys.readouterr()
    assert "[SUCCESS] Test message" in captured.out


def test_error_message_printing(import_service, capsys):
    """Test that error messages are printed correctly."""
    import_service._error("Test error")
    captured = capsys.readouterr()
    assert "[ERROR] Test error" in captured.out


def test_validation_error_message_printing(import_service, capsys):
    """Test that validation error messages are printed correctly."""
    import_service._validation_error("Test validation error")
    captured = capsys.readouterr()
    assert "[VALIDATION ERROR] Test validation error" in captured.out