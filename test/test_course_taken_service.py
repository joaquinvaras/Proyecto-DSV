"""Unit tests for CourseTakenService module.

This module contains comprehensive tests for the CourseTakenService class,
including enrollment management, grade tracking, and academic history operations.
"""

import pytest
from unittest.mock import Mock, patch
from Service.course_taken_service import CourseTakenService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def course_taken_service(mock_db):
    """Create CourseTakenService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.course_taken_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return CourseTakenService()


def test_init_creates_database_connection():
    """Test that CourseTakenService initializes with database connection."""
    with patch('Service.course_taken_service.DatabaseConnection') as mock_db_class:
        service = CourseTakenService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_enroll_student_success(course_taken_service, mock_db):
    """Test successful enrollment of student in course section."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 1
    course_id = 1
    section_id = 1

    course_taken_service.enroll_student(user_id, course_id, section_id)

    expected_query = (
        "INSERT INTO Courses_Taken (user_id, course_id, section_id, "
        "final_grade) VALUES (%s, %s, %s, %s)"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (user_id, course_id, section_id, 1)
    )
    mock_db_instance.commit.assert_called_once()


def test_enroll_student_with_default_grade(course_taken_service, mock_db):
    """Test that enrollment sets default final grade to 1."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 5
    course_id = 3
    section_id = 2

    course_taken_service.enroll_student(user_id, course_id, section_id)

    args = mock_cursor.execute.call_args[0][1]
    assert args[3] == 1


def test_unenroll_student_success(course_taken_service, mock_db):
    """Test successful unenrollment of student from course section."""
    mock_db_instance, mock_cursor = mock_db
    course_id = 1
    section_id = 1
    user_id = 1

    course_taken_service.unenroll_student(course_id, section_id, user_id)

    expected_query = (
        "DELETE FROM Courses_Taken WHERE course_id = %s AND "
        "section_id = %s AND user_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (course_id, section_id, user_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_get_students_by_section_returns_enrolled_students(course_taken_service, mock_db):
    """Test getting all students enrolled in a specific section."""
    _, mock_cursor = mock_db
    section_id = 1
    expected_students = [
        {
            'user_id': 1, 'user_name': 'Juan Pérez', 
            'user_email': 'juan@email.com', 'final_grade': 5.5
        },
        {
            'user_id': 2, 'user_name': 'María García', 
            'user_email': 'maria@email.com', 'final_grade': 6.2
        }
    ]
    mock_cursor.fetchall.return_value = expected_students

    result = course_taken_service.get_students_by_section(section_id)

    expected_query = (
        "SELECT u.id AS user_id, u.name AS user_name, "
        "u.email AS user_email, ct.final_grade "
        "FROM Courses_Taken ct "
        "JOIN Users u ON ct.user_id = u.id "
        "WHERE ct.section_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (section_id,))
    assert result == expected_students


def test_get_students_by_section_returns_empty_when_none(course_taken_service, mock_db):
    """Test getting students when section has no enrollments."""
    _, mock_cursor = mock_db
    section_id = 999
    mock_cursor.fetchall.return_value = []

    result = course_taken_service.get_students_by_section(section_id)

    assert result == []


def test_get_courses_taken_by_user_returns_user_courses(course_taken_service, mock_db):
    """Test getting all courses taken by a specific user."""
    _, mock_cursor = mock_db
    user_id = 1
    expected_courses = [
        {'name': 'Diseño de Software', 'period': '2025-1', 'final_grade': 5.5},
        {'name': 'Programación', 'period': '2024-2', 'final_grade': 6.0}
    ]
    mock_cursor.fetchall.return_value = expected_courses

    result = course_taken_service.get_courses_taken_by_user(user_id)

    expected_query = (
        "SELECT c.name, i.period, ct.final_grade "
        "FROM Courses_Taken ct "
        "JOIN Courses c ON ct.course_id = c.id "
        "JOIN Sections s ON ct.section_id = s.id "
        "JOIN Instances i ON s.instance_id = i.id "
        "WHERE ct.user_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (user_id,))
    assert result == expected_courses


def test_get_courses_taken_by_user_returns_empty_when_none(course_taken_service, mock_db):
    """Test getting courses when user has taken none."""
    _, mock_cursor = mock_db
    user_id = 999
    mock_cursor.fetchall.return_value = []

    result = course_taken_service.get_courses_taken_by_user(user_id)

    assert result == []


def test_get_closed_courses_by_student_returns_closed_courses(course_taken_service, mock_db):
    """Test getting closed courses taken by a specific student."""
    _, mock_cursor = mock_db
    student_id = 1
    expected_courses = [
        {
            'final_grade': 5.5, 'course_name': 'Diseño de Software',
            'period': '2025-1', 'section_number': 1
        },
        {
            'final_grade': 6.0, 'course_name': 'Programación',
            'period': '2024-2', 'section_number': 2
        }
    ]
    mock_cursor.fetchall.return_value = expected_courses

    result = course_taken_service.get_closed_courses_by_student(student_id)

    expected_query = """
            SELECT ct.final_grade,
                   c.name as course_name,
                   i.period,
                   s.number as section_number
            FROM Courses_Taken ct
            JOIN Sections s ON ct.section_id = s.id
            JOIN Instances i ON s.instance_id = i.id
            JOIN Courses c ON i.course_id = c.id
            WHERE ct.user_id = %s AND s.is_closed = 1
            ORDER BY i.period DESC, c.name
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (student_id,))
    assert result == expected_courses


def test_get_closed_courses_by_student_returns_empty_when_none(course_taken_service, mock_db):
    """Test getting closed courses when student has none."""
    _, mock_cursor = mock_db
    student_id = 999
    mock_cursor.fetchall.return_value = []

    result = course_taken_service.get_closed_courses_by_student(student_id)

    assert result == []


def test_get_closed_courses_ordered_correctly(course_taken_service, mock_db):
    """Test that closed courses are ordered by period DESC and course name."""
    _, mock_cursor = mock_db
    student_id = 1
    
    course_taken_service.get_closed_courses_by_student(student_id)

    query = mock_cursor.execute.call_args[0][0]
    assert "ORDER BY i.period DESC, c.name" in query


def test_update_final_grade_success(course_taken_service, mock_db):
    """Test successful update of final grade for student in section."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 1
    section_id = 1
    final_grade = 6.5

    course_taken_service.update_final_grade(user_id, section_id, final_grade)

    expected_query = (
        "UPDATE Courses_Taken SET final_grade = %s "
        "WHERE user_id = %s AND section_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (final_grade, user_id, section_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_is_student_enrolled_returns_true_when_enrolled(course_taken_service, mock_db):
    """Test checking enrollment when student is enrolled."""
    _, mock_cursor = mock_db
    user_id = 1
    section_id = 1
    mock_cursor.fetchone.return_value = {'count': 1}

    result = course_taken_service.is_student_enrolled(user_id, section_id)

    expected_query = (
        "SELECT COUNT(*) as count FROM Courses_Taken "
        "WHERE user_id = %s AND section_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (user_id, section_id)
    )
    assert result is True


def test_is_student_enrolled_returns_false_when_not_enrolled(course_taken_service, mock_db):
    """Test checking enrollment when student is not enrolled."""
    _, mock_cursor = mock_db
    user_id = 1
    section_id = 1
    mock_cursor.fetchone.return_value = {'count': 0}

    result = course_taken_service.is_student_enrolled(user_id, section_id)

    assert result is False


def test_is_student_enrolled_handles_none_result(course_taken_service, mock_db):
    """Test checking enrollment when query returns None (should raise TypeError)."""
    _, mock_cursor = mock_db
    user_id = 1
    section_id = 1
    mock_cursor.fetchone.return_value = None

    with pytest.raises(TypeError, match="'NoneType' object is not subscriptable"):
        course_taken_service.is_student_enrolled(user_id, section_id)


@pytest.mark.parametrize("user_id,course_id,section_id", [
    (1, 1, 1),
    (5, 3, 2),
    (10, 7, 5),
])
def test_enroll_student_with_various_parameters(course_taken_service, mock_db,
                                               user_id, course_id, section_id):
    """Test enrollment with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db

    course_taken_service.enroll_student(user_id, course_id, section_id)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (user_id, course_id, section_id, 1)
    mock_db_instance.commit.assert_called_once()


@pytest.mark.parametrize("final_grade", [
    1.0, 4.5, 5.8, 6.9, 7.0
])
def test_update_final_grade_with_various_grades(course_taken_service, mock_db, final_grade):
    """Test updating final grade with various grade values."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 1
    section_id = 1

    course_taken_service.update_final_grade(user_id, section_id, final_grade)

    args = mock_cursor.execute.call_args[0][1]
    assert args[0] == final_grade
    assert args[1] == user_id
    assert args[2] == section_id


@pytest.mark.parametrize("count,expected_result", [
    (0, False),
    (1, True),
    (2, True),
])
def test_is_student_enrolled_with_various_counts(course_taken_service, mock_db,
                                                count, expected_result):
    """Test enrollment check with various count values."""
    _, mock_cursor = mock_db
    user_id = 1
    section_id = 1
    mock_cursor.fetchone.return_value = {'count': count}

    result = course_taken_service.is_student_enrolled(user_id, section_id)

    assert result == expected_result


def test_enrollment_and_unenrollment_sequence(course_taken_service, mock_db):
    """Test sequence of enrollment followed by unenrollment."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 1
    course_id = 1
    section_id = 1

    course_taken_service.enroll_student(user_id, course_id, section_id)
    
    mock_cursor.reset_mock()
    mock_db_instance.reset_mock()

    course_taken_service.unenroll_student(course_id, section_id, user_id)

    expected_query = (
        "DELETE FROM Courses_Taken WHERE course_id = %s AND "
        "section_id = %s AND user_id = %s"
    )
    mock_cursor.execute.assert_called_with(
        expected_query, (course_id, section_id, user_id)
    )


def test_database_error_handling_on_enroll(course_taken_service, mock_db):
    """Test that database errors during enrollment are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_taken_service.enroll_student(1, 1, 1)


def test_database_error_handling_on_unenroll(course_taken_service, mock_db):
    """Test that database errors during unenrollment are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_taken_service.unenroll_student(1, 1, 1)


def test_database_error_handling_on_update_grade(course_taken_service, mock_db):
    """Test that database errors during grade update are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_taken_service.update_final_grade(1, 1, 5.5)


def test_database_error_handling_on_get_students(course_taken_service, mock_db):
    """Test that database errors during get students are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_taken_service.get_students_by_section(1)


def test_database_error_handling_on_get_courses(course_taken_service, mock_db):
    """Test that database errors during get courses are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_taken_service.get_courses_taken_by_user(1)


def test_database_error_handling_on_get_closed_courses(course_taken_service, mock_db):
    """Test that database errors during get closed courses are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_taken_service.get_closed_courses_by_student(1)


def test_database_error_handling_on_is_enrolled(course_taken_service, mock_db):
    """Test that database errors during enrollment check are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        course_taken_service.is_student_enrolled(1, 1)