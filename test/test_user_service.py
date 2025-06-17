"""Unit tests for UserService module.

This module contains comprehensive tests for the UserService class,
including CRUD operations for students and professors, import ID management,
and relationship handling with courses and sections.
"""

import pytest
from unittest.mock import Mock, patch
from Service.user_service import UserService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def user_service(mock_db):
    """Create UserService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.user_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return UserService()


def test_init_creates_database_connection():
    """Test that UserService initializes with database connection."""
    with patch('Service.user_service.DatabaseConnection') as mock_db_class:
        service = UserService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_get_all_returns_all_users(user_service, mock_db):
    """Test getting all users without filtering."""
    _, mock_cursor = mock_db
    expected_users = [
        {'id': 1, 'name': 'Juan Pérez', 'email': 'juan@test.com', 'is_professor': False},
        {'id': 2, 'name': 'Dr. García', 'email': 'garcia@test.com', 'is_professor': True},
        {'id': 3, 'name': 'María López', 'email': 'maria@test.com', 'is_professor': False}
    ]
    mock_cursor.fetchall.return_value = expected_users

    result = user_service.get_all()

    mock_cursor.execute.assert_called_once_with("SELECT * FROM Users")
    assert result == expected_users


def test_get_all_with_professor_filter_true(user_service, mock_db):
    """Test getting all users filtered by professor status (professors only)."""
    _, mock_cursor = mock_db
    expected_professors = [
        {'id': 2, 'name': 'Dr. García', 'email': 'garcia@test.com', 'is_professor': True}
    ]
    mock_cursor.fetchall.return_value = expected_professors

    result = user_service.get_all(is_professor=True)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Users WHERE is_professor = %s", (True,)
    )
    assert result == expected_professors


def test_get_all_with_professor_filter_false(user_service, mock_db):
    """Test getting all users filtered by professor status (students only)."""
    _, mock_cursor = mock_db
    expected_students = [
        {'id': 1, 'name': 'Juan Pérez', 'email': 'juan@test.com', 'is_professor': False},
        {'id': 3, 'name': 'María López', 'email': 'maria@test.com', 'is_professor': False}
    ]
    mock_cursor.fetchall.return_value = expected_students

    result = user_service.get_all(is_professor=False)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Users WHERE is_professor = %s", (False,)
    )
    assert result == expected_students


def test_get_all_returns_empty_when_no_users(user_service, mock_db):
    """Test getting all users when none exist."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    result = user_service.get_all()

    assert result == []


def test_get_by_id_returns_specific_user(user_service, mock_db):
    """Test getting a specific user by their ID."""
    _, mock_cursor = mock_db
    user_id = 1
    expected_user = {
        'id': 1, 'name': 'Juan Pérez', 'email': 'juan@test.com', 
        'is_professor': False, 'admission_date': '2020-01-01'
    }
    mock_cursor.fetchone.return_value = expected_user

    result = user_service.get_by_id(user_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Users WHERE id = %s", (user_id,)
    )
    assert result == expected_user


def test_get_by_id_returns_none_when_not_found(user_service, mock_db):
    """Test getting user by ID when user doesn't exist."""
    _, mock_cursor = mock_db
    user_id = 999
    mock_cursor.fetchone.return_value = None

    result = user_service.get_by_id(user_id)

    assert result is None


def test_get_by_email_returns_specific_user(user_service, mock_db):
    """Test getting a specific user by their email address."""
    _, mock_cursor = mock_db
    email = 'juan@test.com'
    expected_user = {
        'id': 1, 'name': 'Juan Pérez', 'email': 'juan@test.com', 'is_professor': False
    }
    mock_cursor.fetchone.return_value = expected_user

    result = user_service.get_by_email(email)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Users WHERE email = %s", (email,)
    )
    assert result == expected_user


def test_get_by_email_returns_none_when_not_found(user_service, mock_db):
    """Test getting user by email when user doesn't exist."""
    _, mock_cursor = mock_db
    email = 'nonexistent@test.com'
    mock_cursor.fetchone.return_value = None

    result = user_service.get_by_email(email)

    assert result is None


def test_get_next_import_id_returns_one_when_no_users(user_service, mock_db):
    """Test getting next import ID when no users of that type exist."""
    _, mock_cursor = mock_db
    is_professor = False
    mock_cursor.fetchone.return_value = {'max_import_id': None}

    result = user_service.get_next_import_id(is_professor)

    expected_query = (
        "SELECT MAX(import_id) as max_import_id FROM Users "
        "WHERE is_professor = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (is_professor,))
    assert result == 1


def test_get_next_import_id_increments_existing_max(user_service, mock_db):
    """Test getting next import ID when users exist."""
    _, mock_cursor = mock_db
    is_professor = True
    mock_cursor.fetchone.return_value = {'max_import_id': 5}

    result = user_service.get_next_import_id(is_professor)

    assert result == 6


def test_get_next_import_id_handles_none_result(user_service, mock_db):
    """Test getting next import ID when query result is None."""
    _, mock_cursor = mock_db
    is_professor = False
    mock_cursor.fetchone.return_value = None

    result = user_service.get_next_import_id(is_professor)

    assert result == 1


def test_create_user_with_minimal_data(user_service, mock_db):
    """Test creating user with minimal required data."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    name = 'Juan Pérez'
    email = 'juan@test.com'
    is_professor = False

    with patch.object(user_service, 'get_next_import_id', return_value=1):
        result = user_service.create(name, email, is_professor)

    expected_query = (
        "INSERT INTO Users (name, email, admission_date, is_professor, "
        "import_id) VALUES (%s, %s, %s, %s, %s)"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (name, email, None, is_professor, 1)
    )
    mock_db_instance.commit.assert_called_once()
    assert result == 1


def test_create_user_with_admission_date(user_service, mock_db):
    """Test creating user with admission date."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 2
    name = 'María López'
    email = 'maria@test.com'
    is_professor = False
    admission_date = '2020-01-01'

    with patch.object(user_service, 'get_next_import_id', return_value=2):
        result = user_service.create(name, email, is_professor, admission_date=admission_date)

    args = mock_cursor.execute.call_args[0][1]
    assert args[2] == admission_date


def test_create_user_with_custom_import_id(user_service, mock_db):
    """Test creating user with custom import ID."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 3
    name = 'Dr. García'
    email = 'garcia@test.com'
    is_professor = True
    custom_import_id = 100

    result = user_service.create(name, email, is_professor, import_id=custom_import_id)

    args = mock_cursor.execute.call_args[0][1]
    assert args[4] == custom_import_id


def test_create_professor_without_admission_date(user_service, mock_db):
    """Test creating professor (admission_date should be None)."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 4
    name = 'Dr. Smith'
    email = 'smith@test.com'
    is_professor = True

    with patch.object(user_service, 'get_next_import_id', return_value=1):
        result = user_service.create(name, email, is_professor)

    args = mock_cursor.execute.call_args[0][1]
    assert args[2] is None
    assert args[3] is True


def test_update_user_with_minimal_data(user_service, mock_db):
    """Test updating user with minimal data."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 1
    name = 'Juan Pérez Updated'
    email = 'juan.updated@test.com'
    is_professor = False

    user_service.update(user_id, name, email, is_professor)

    expected_query = (
        "UPDATE Users SET name = %s, email = %s, "
        "admission_date = %s, is_professor = %s WHERE id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (name, email, None, is_professor, user_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_update_user_with_admission_date(user_service, mock_db):
    """Test updating user with admission date."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 1
    name = 'Juan Pérez'
    email = 'juan@test.com'
    is_professor = False
    admission_date = '2021-01-01'

    user_service.update(user_id, name, email, is_professor, admission_date=admission_date)

    args = mock_cursor.execute.call_args[0][1]
    assert args[2] == admission_date


def test_update_user_with_import_id(user_service, mock_db):
    """Test updating user with import ID."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 1
    name = 'Juan Pérez'
    email = 'juan@test.com'
    is_professor = False
    import_id = 50

    user_service.update(user_id, name, email, is_professor, import_id=import_id)

    expected_query = (
        "UPDATE Users SET name = %s, email = %s, "
        "admission_date = %s, is_professor = %s, import_id = %s "
        "WHERE id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (name, email, None, is_professor, import_id, user_id)
    )


def test_update_user_without_import_id(user_service, mock_db):
    """Test updating user without import ID (uses different query)."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 1
    name = 'Juan Pérez'
    email = 'juan@test.com'
    is_professor = False

    user_service.update(user_id, name, email, is_professor)

    query = mock_cursor.execute.call_args[0][0]
    assert "import_id" not in query


def test_delete_student_removes_related_data(user_service, mock_db):
    """Test deleting a student removes their grades and course enrollments."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 1

    with patch.object(user_service, 'is_professor_with_sections', return_value=False):
        user_service.delete(user_id)

    mock_cursor.execute.assert_any_call(
        "DELETE FROM Grades WHERE user_id = %s", (user_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Courses_Taken WHERE user_id = %s", (user_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Users WHERE id = %s", (user_id,)
    )
    
    mock_db_instance.commit.assert_called_once()


def test_delete_professor_with_sections_sets_professor_id_to_null(user_service, mock_db):
    """Test deleting professor with sections sets professor_id to NULL in sections."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 2

    with patch.object(user_service, 'is_professor_with_sections', return_value=True):
        user_service.delete(user_id)

    mock_cursor.execute.assert_any_call(
        "UPDATE Sections SET professor_id = NULL "
        "WHERE professor_id = %s", (user_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Users WHERE id = %s", (user_id,)
    )


def test_delete_professor_without_sections_no_section_update(user_service, mock_db):
    """Test deleting professor without sections doesn't update sections."""
    mock_db_instance, mock_cursor = mock_db
    user_id = 3

    with patch.object(user_service, 'is_professor_with_sections', return_value=False):
        user_service.delete(user_id)

    calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
    update_sections_called = any("UPDATE Sections" in call for call in calls)
    assert not update_sections_called


def test_is_professor_with_sections_returns_true_when_has_sections(user_service, mock_db):
    """Test checking if professor has sections when they do."""
    _, mock_cursor = mock_db
    user_id = 1
    mock_cursor.fetchone.return_value = {'count': 3}

    result = user_service.is_professor_with_sections(user_id)

    expected_query = (
        "SELECT COUNT(*) as count FROM Sections WHERE professor_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (user_id,))
    assert result is True


def test_is_professor_with_sections_returns_false_when_no_sections(user_service, mock_db):
    """Test checking if professor has sections when they don't."""
    _, mock_cursor = mock_db
    user_id = 2
    mock_cursor.fetchone.return_value = {'count': 0}

    result = user_service.is_professor_with_sections(user_id)

    assert result is False


def test_get_courses_taken_returns_student_courses(user_service, mock_db):
    """Test getting all courses taken by a specific user."""
    _, mock_cursor = mock_db
    user_id = 1
    expected_courses = [
        {
            'id': 1, 'course_name': 'Diseño de Software', 'period': '2025-1',
            'section_number': 1, 'final_grade': 5.5
        },
        {
            'id': 2, 'course_name': 'Programación', 'period': '2024-2',
            'section_number': 1, 'final_grade': 6.0
        }
    ]
    mock_cursor.fetchall.return_value = expected_courses

    result = user_service.get_courses_taken(user_id)

    expected_query = (
        "SELECT ct.*, c.name as course_name, i.period, "
        "s.number as section_number "
        "FROM Courses_Taken ct "
        "JOIN Courses c ON ct.course_id = c.id "
        "JOIN Sections s ON ct.section_id = s.id "
        "JOIN Instances i ON s.instance_id = i.id "
        "WHERE ct.user_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (user_id,))
    assert result == expected_courses


def test_get_courses_taken_returns_empty_when_no_courses(user_service, mock_db):
    """Test getting courses taken when student has taken none."""
    _, mock_cursor = mock_db
    user_id = 999
    mock_cursor.fetchall.return_value = []

    result = user_service.get_courses_taken(user_id)

    assert result == []


def test_get_sections_taught_returns_professor_sections(user_service, mock_db):
    """Test getting all sections taught by a specific professor."""
    _, mock_cursor = mock_db
    user_id = 2
    expected_sections = [
        {
            'id': 1, 'period': '2025-1', 'course_name': 'Diseño de Software', 'nrc': 'ICC5130'
        },
        {
            'id': 2, 'period': '2025-1', 'course_name': 'Programación', 'nrc': 'ICC1102'
        }
    ]
    mock_cursor.fetchall.return_value = expected_sections

    result = user_service.get_sections_taught(user_id)

    expected_query = (
        "SELECT s.*, i.period, c.name as course_name, c.nrc "
        "FROM Sections s "
        "JOIN Instances i ON s.instance_id = i.id "
        "JOIN Courses c ON i.course_id = c.id "
        "WHERE s.professor_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (user_id,))
    assert result == expected_sections


def test_get_sections_taught_returns_empty_when_no_sections(user_service, mock_db):
    """Test getting sections taught when professor teaches none."""
    _, mock_cursor = mock_db
    user_id = 999
    mock_cursor.fetchall.return_value = []

    result = user_service.get_sections_taught(user_id)

    assert result == []


@pytest.mark.parametrize("name,email,is_professor", [
    ('Juan Pérez', 'juan@test.com', False),
    ('Dr. García', 'garcia@test.com', True),
    ('María López', 'maria@test.com', False),
])
def test_create_user_with_various_parameters(user_service, mock_db,
                                           name, email, is_professor):
    """Test user creation with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    with patch.object(user_service, 'get_next_import_id', return_value=1):
        result = user_service.create(name, email, is_professor)

    args = mock_cursor.execute.call_args[0][1]
    assert args[0] == name
    assert args[1] == email
    assert args[3] == is_professor
    mock_db_instance.commit.assert_called_once()
    assert result == 1


@pytest.mark.parametrize("is_professor,expected_import_id", [
    (True, 1),
    (False, 1),
    (True, 5),
    (False, 10),
])
def test_get_next_import_id_with_various_user_types(user_service, mock_db,
                                                   is_professor, expected_import_id):
    """Test getting next import ID for different user types."""
    _, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = {'max_import_id': expected_import_id - 1}

    result = user_service.get_next_import_id(is_professor)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (is_professor,)
    assert result == expected_import_id


def test_user_operations_sequence(user_service, mock_db):
    """Test sequence of user operations."""
    mock_db_instance, mock_cursor = mock_db

    mock_cursor.lastrowid = 1
    with patch.object(user_service, 'get_next_import_id', return_value=1):
        user_id = user_service.create('Test User', 'test@test.com', False)

    mock_cursor.reset_mock()
    mock_db_instance.reset_mock()

    user_service.update(user_id, 'Updated User', 'updated@test.com', False)

    mock_cursor.reset_mock()
    mock_db_instance.reset_mock()

    with patch.object(user_service, 'is_professor_with_sections', return_value=False):
        user_service.delete(user_id)

    mock_cursor.execute.assert_any_call(
        "DELETE FROM Users WHERE id = %s", (user_id,)
    )


def test_create_user_auto_generates_import_id_when_not_provided(user_service, mock_db):
    """Test that create automatically generates import_id when not provided."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    with patch.object(user_service, 'get_next_import_id', return_value=5) as mock_get_next:
        user_service.create('Test User', 'test@test.com', False)
    
    mock_get_next.assert_called_once_with(False)
    
    args = mock_cursor.execute.call_args[0][1]
    assert args[4] == 5


def test_create_user_does_not_generate_import_id_when_provided(user_service, mock_db):
    """Test that create doesn't generate import_id when it's provided."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    with patch.object(user_service, 'get_next_import_id') as mock_get_next:
        user_service.create('Test User', 'test@test.com', False, import_id=100)
    
    mock_get_next.assert_not_called()
    
    args = mock_cursor.execute.call_args[0][1]
    assert args[4] == 100


def test_database_error_handling_on_create(user_service, mock_db):
    """Test that database errors during create are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with patch.object(user_service, 'get_next_import_id', return_value=1):
        with pytest.raises(Exception, match="Database error"):
            user_service.create('Test User', 'test@test.com', False)


def test_database_error_handling_on_update(user_service, mock_db):
    """Test that database errors during update are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        user_service.update(1, 'Test User', 'test@test.com', False)


def test_database_error_handling_on_delete(user_service, mock_db):
    """Test that database errors during delete are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    
    with patch.object(user_service, 'is_professor_with_sections', return_value=False):
        mock_cursor.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            user_service.delete(1)


def test_database_error_handling_on_get_courses_taken(user_service, mock_db):
    """Test that database errors during get_courses_taken are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        user_service.get_courses_taken(1)


def test_database_error_handling_on_get_sections_taught(user_service, mock_db):
    """Test that database errors during get_sections_taught are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        user_service.get_sections_taught(1)


def test_database_error_handling_on_is_professor_with_sections(user_service, mock_db):
    """Test that database errors during is_professor_with_sections are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        user_service.is_professor_with_sections(1)


def test_complex_professor_deletion_workflow(user_service, mock_db):
    """Test complex professor deletion with section assignments."""
    mock_db_instance, mock_cursor = mock_db
    professor_id = 5

    with patch.object(user_service, 'is_professor_with_sections', return_value=True):
        user_service.delete(professor_id)

    delete_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
    
    assert any("DELETE FROM Grades" in call for call in delete_calls)
    assert any("DELETE FROM Courses_Taken" in call for call in delete_calls)
    assert any("UPDATE Sections SET professor_id = NULL" in call for call in delete_calls)
    assert any("DELETE FROM Users" in call for call in delete_calls)


def test_student_vs_professor_creation_differences(user_service, mock_db):
    """Test differences between creating students and professors."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    
    with patch.object(user_service, 'get_next_import_id', return_value=1):
        user_service.create('Student', 'student@test.com', False, admission_date='2020-01-01')
    
    student_args = mock_cursor.execute.call_args[0][1]
    
    mock_cursor.reset_mock()

    with patch.object(user_service, 'get_next_import_id', return_value=1):
        user_service.create('Professor', 'prof@test.com', True)
    
    professor_args = mock_cursor.execute.call_args[0][1]

    assert student_args[2] == '2020-01-01'
    assert student_args[3] is False
    
    assert professor_args[2] is None
    assert professor_args[3] is True