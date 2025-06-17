"""Unit tests for CourseService module.

This module contains comprehensive tests for the CourseService class,
including CRUD operations, prerequisites management, enrollments, and cascading deletions.
"""

import pytest
from unittest.mock import Mock, patch
from Service.course_service import CourseService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def course_service(mock_db):
    """Create CourseService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.course_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return CourseService()


def test_init_creates_database_connection():
    """Test that CourseService initializes with database connection."""
    with patch('Service.course_service.DatabaseConnection') as mock_db_class:
        service = CourseService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_get_all_returns_all_courses(course_service, mock_db):
    """Test getting all courses from database."""
    _, mock_cursor = mock_db
    expected_courses = [
        {'id': 1, 'name': 'Diseño de Software', 'nrc': 'ICC5130', 'credits': 3},
        {'id': 2, 'name': 'Programación', 'nrc': 'ICC1102', 'credits': 4}
    ]
    mock_cursor.fetchall.return_value = expected_courses

    result = course_service.get_all()

    mock_cursor.execute.assert_called_once_with("SELECT * FROM Courses")
    assert result == expected_courses


def test_get_by_id_returns_specific_course(course_service, mock_db):
    """Test getting a specific course by ID."""
    _, mock_cursor = mock_db
    course_id = 1
    expected_course = {
        'id': 1, 'name': 'Diseño de Software', 'nrc': 'ICC5130', 'credits': 3
    }
    mock_cursor.fetchone.return_value = expected_course

    result = course_service.get_by_id(course_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Courses WHERE id = %s", (course_id,)
    )
    assert result == expected_course


def test_get_by_id_returns_none_when_not_found(course_service, mock_db):
    """Test getting course by ID when course doesn't exist."""
    _, mock_cursor = mock_db
    course_id = 999
    mock_cursor.fetchone.return_value = None

    result = course_service.get_by_id(course_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Courses WHERE id = %s", (course_id,)
    )
    assert result is None


def test_get_prerequisites_returns_prerequisite_courses(course_service, mock_db):
    """Test getting prerequisites for a specific course."""
    _, mock_cursor = mock_db
    course_id = 1
    expected_prerequisites = [
        {'id': 2, 'name': 'Programación', 'nrc': 'ICC1102', 'credits': 4},
        {'id': 3, 'name': 'Matemáticas', 'nrc': 'MAT1100', 'credits': 3}
    ]
    mock_cursor.fetchall.return_value = expected_prerequisites

    result = course_service.get_prerequisites(course_id)

    expected_query = """
        SELECT c.* FROM Courses c
        JOIN CoursePrerequisites cp ON c.id = cp.prerequisite_id
        WHERE cp.course_id = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (course_id,))
    assert result == expected_prerequisites


def test_get_prerequisites_returns_empty_list_when_none(course_service, mock_db):
    """Test getting prerequisites when course has none."""
    _, mock_cursor = mock_db
    course_id = 1
    mock_cursor.fetchall.return_value = []

    result = course_service.get_prerequisites(course_id)

    assert result == []


def test_get_enrollments_in_section_returns_students(course_service, mock_db):
    """Test getting student enrollments for a specific section."""
    _, mock_cursor = mock_db
    section_id = 1
    expected_enrollments = [
        {'user_id': 1, 'user_name': 'Juan Pérez', 'user_email': 'juan@email.com'},
        {'user_id': 2, 'user_name': 'María García', 'user_email': 'maria@email.com'}
    ]
    mock_cursor.fetchall.return_value = expected_enrollments

    result = course_service.get_enrollments_in_section(section_id)

    expected_query = """
        SELECT u.id AS user_id, u.name AS user_name, u.email AS user_email
        FROM Users u
        JOIN Courses_Taken ct ON u.id = ct.user_id
        WHERE ct.section_id = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (section_id,))
    assert result == expected_enrollments


def test_get_enrollments_in_section_returns_empty_when_none(course_service, mock_db):
    """Test getting enrollments when section has no students."""
    _, mock_cursor = mock_db
    section_id = 1
    mock_cursor.fetchall.return_value = []

    result = course_service.get_enrollments_in_section(section_id)

    assert result == []


def test_unenroll_student_from_section_success(course_service, mock_db):
    """Test successful unenrollment of student from section."""
    mock_db_instance, mock_cursor = mock_db
    course_id = 1
    section_id = 1
    user_id = 1

    course_service.unenroll_student_from_section(course_id, section_id, user_id)

    expected_query = (
        "DELETE FROM Courses_Taken WHERE course_id = %s AND "
        "section_id = %s AND user_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (course_id, section_id, user_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_create_course_without_prerequisites(course_service, mock_db):
    """Test creating a course without prerequisites."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    name = "Diseño de Software"
    nrc = "ICC5130"
    course_credits = 3

    result = course_service.create(name, nrc, course_credits)

    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO Courses (name, nrc, credits) VALUES (%s, %s, %s)",
        (name, nrc, course_credits)
    )
    mock_db_instance.commit.assert_called_once()
    assert result == 1


def test_create_course_with_prerequisites(course_service, mock_db):
    """Test creating a course with prerequisites."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    name = "Diseño de Software"
    nrc = "ICC5130"
    course_credits = 3
    prerequisites = [2, 3]

    result = course_service.create(name, nrc, course_credits, prerequisites)

    mock_cursor.execute.assert_any_call(
        "INSERT INTO Courses (name, nrc, credits) VALUES (%s, %s, %s)",
        (name, nrc, course_credits)
    )
    
    for prereq_id in prerequisites:
        mock_cursor.execute.assert_any_call(
            "INSERT INTO CoursePrerequisites (course_id, "
            "prerequisite_id) VALUES (%s, %s)",
            (1, prereq_id)
        )
    
    mock_db_instance.commit.assert_called_once()
    assert result == 1


def test_create_course_with_empty_prerequisites_list(course_service, mock_db):
    """Test creating a course with empty prerequisites list."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    name = "Diseño de Software"
    nrc = "ICC5130"
    course_credits = 3
    prerequisites = []

    result = course_service.create(name, nrc, course_credits, prerequisites)

    assert mock_cursor.execute.call_count == 1
    mock_cursor.execute.assert_called_with(
        "INSERT INTO Courses (name, nrc, credits) VALUES (%s, %s, %s)",
        (name, nrc, course_credits)
    )


def test_update_course_with_keyword_args(course_service, mock_db):
    """Test updating a course using keyword arguments."""
    mock_db_instance, mock_cursor = mock_db
    course_id = 1
    course_data = {
        'name': 'Updated Course',
        'nrc': 'NEW123',
        'credits': 4,
        'prerequisites': [2, 3]
    }

    course_service.update(course_id, **course_data)

    mock_cursor.execute.assert_any_call(
        "UPDATE Courses SET name = %s, nrc = %s, credits = %s "
        "WHERE id = %s",
        ('Updated Course', 'NEW123', 4, course_id)
    )
    
    mock_cursor.execute.assert_any_call(
        "DELETE FROM CoursePrerequisites WHERE course_id = %s",
        (course_id,)
    )
    
    for prereq_id in [2, 3]:
        mock_cursor.execute.assert_any_call(
            "INSERT INTO CoursePrerequisites (course_id, "
            "prerequisite_id) VALUES (%s, %s)",
            (course_id, prereq_id)
        )
    
    mock_db_instance.commit.assert_called_once()


def test_update_course_without_prerequisites(course_service, mock_db):
    """Test updating a course without specifying prerequisites."""
    mock_db_instance, mock_cursor = mock_db
    course_id = 1
    course_data = {
        'name': 'Updated Course',
        'nrc': 'NEW123',
        'credits': 4
    }

    course_service.update(course_id, **course_data)

    mock_cursor.execute.assert_any_call(
        "DELETE FROM CoursePrerequisites WHERE course_id = %s",
        (course_id,)
    )


def test_delete_course_with_cascading_relations(course_service, mock_db):
    """Test deleting a course with all its cascading relations."""
    mock_db_instance, mock_cursor = mock_db
    course_id = 1
    
    instances = [{'id': 1}]
    sections = [{'id': 1}]
    topics = [{'id': 1}]
    activities = [{'id': 1}]

    mock_cursor.fetchall.side_effect = [
        instances,
        sections,
        topics,
        activities,
    ]

    course_service.delete(course_id)

    mock_cursor.execute.assert_any_call(
        "SELECT id FROM Instances WHERE course_id = %s", (course_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM CoursePrerequisites WHERE "
        "course_id = %s OR prerequisite_id = %s",
        (course_id, course_id)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Courses WHERE id = %s", (course_id,)
    )
    
    mock_db_instance.commit.assert_called_once()

def test_delete_course_handles_empty_instances(course_service, mock_db):
    """Test deleting a course with no instances."""
    mock_db_instance, mock_cursor = mock_db
    course_id = 1
    
    mock_cursor.fetchall.return_value = []

    course_service.delete(course_id)

    mock_cursor.execute.assert_any_call(
        "DELETE FROM CoursePrerequisites WHERE "
        "course_id = %s OR prerequisite_id = %s",
        (course_id, course_id)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Courses WHERE id = %s", (course_id,)
    )


def test_get_instances_returns_course_instances(course_service, mock_db):
    """Test getting all instances for a specific course."""
    _, mock_cursor = mock_db
    course_id = 1
    expected_instances = [
        {'id': 1, 'course_id': 1, 'period': '2025-1'},
        {'id': 2, 'course_id': 1, 'period': '2025-2'}
    ]
    mock_cursor.fetchall.return_value = expected_instances

    result = course_service.get_instances(course_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Instances WHERE course_id = %s", (course_id,)
    )
    assert result == expected_instances


def test_get_instances_returns_empty_when_none(course_service, mock_db):
    """Test getting instances when course has none."""
    _, mock_cursor = mock_db
    course_id = 1
    mock_cursor.fetchall.return_value = []

    result = course_service.get_instances(course_id)

    assert result == []


def test_create_instance_success(course_service, mock_db):
    """Test successful creation of a course instance."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    course_id = 1
    period = "2025-1"

    result = course_service.create_instance(course_id, period)

    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO Instances (course_id, period) VALUES (%s, %s)",
        (course_id, period)
    )
    mock_db_instance.commit.assert_called_once()
    assert result == 1


@pytest.mark.parametrize("name,nrc,credits", [
    ("Diseño de Software", "ICC5130", 3),
    ("Programación", "ICC1102", 4),
    ("Matemáticas", "MAT1100", 5),
])
def test_create_course_with_various_parameters(course_service, mock_db, 
                                              name, nrc, credits):
    """Test course creation with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    result = course_service.create(name, nrc, credits)

    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO Courses (name, nrc, credits) VALUES (%s, %s, %s)",
        (name, nrc, credits)
    )
    assert result == 1


@pytest.mark.parametrize("prerequisites", [
    None,
    [],
    [1],
    [1, 2, 3],
])
def test_create_course_with_different_prerequisites(course_service, mock_db, 
                                                   prerequisites):
    """Test course creation with different prerequisite configurations."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    name = "Test Course"
    nrc = "TEST123"
    credits = 3

    course_service.create(name, nrc, credits, prerequisites)

    mock_cursor.execute.assert_any_call(
        "INSERT INTO Courses (name, nrc, credits) VALUES (%s, %s, %s)",
        (name, nrc, credits)
    )
    
    if prerequisites:
        for prereq_id in prerequisites:
            mock_cursor.execute.assert_any_call(
                "INSERT INTO CoursePrerequisites (course_id, "
                "prerequisite_id) VALUES (%s, %s)",
                (1, prereq_id)
            )


def test_database_error_handling_on_create(course_service, mock_db):
    """Test that database errors during create are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_service.create("Test", "TEST123", 3)


def test_database_error_handling_on_update(course_service, mock_db):
    """Test that database errors during update are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_service.update(1, name="Test", nrc="TEST123", credits=3)


def test_database_error_handling_on_delete(course_service, mock_db):
    """Test that database errors during delete are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_service.delete(1)


def test_database_error_handling_on_unenroll(course_service, mock_db):
    """Test that database errors during unenroll are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_service.unenroll_student_from_section(1, 1, 1)


def test_database_error_handling_on_create_instance(course_service, mock_db):
    """Test that database errors during create_instance are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_service.create_instance(1, "2025-1")