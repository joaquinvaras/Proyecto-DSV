"""Unit tests for SectionService module.

This module contains comprehensive tests for the SectionService class,
including CRUD operations, professor assignment, enrollment management, 
section state tracking, and cascading deletions.
"""

import pytest
from unittest.mock import Mock, patch
from Service.section_service import SectionService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def section_service(mock_db):
    """Create SectionService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.section_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return SectionService()


def test_init_creates_database_connection():
    """Test that SectionService initializes with database connection."""
    with patch('Service.section_service.DatabaseConnection') as mock_db_class:
        service = SectionService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_get_all_returns_sections_with_professor_and_instance_info(section_service, mock_db):
    """Test getting all sections with professor and instance information."""
    _, mock_cursor = mock_db
    expected_sections = [
        {
            'id': 1, 'instance_id': 1, 'number': 1, 'weight_or_percentage': True,
            'is_closed': False, 'professor_name': 'Dr. García', 'period': '2025-1', 'course_id': 1
        },
        {
            'id': 2, 'instance_id': 1, 'number': 2, 'weight_or_percentage': False,
            'is_closed': True, 'professor_name': 'Dra. López', 'period': '2025-1', 'course_id': 1
        }
    ]
    mock_cursor.fetchall.return_value = expected_sections

    result = section_service.get_all()

    expected_query = """
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        """
    mock_cursor.execute.assert_called_once_with(expected_query)
    assert result == expected_sections


def test_get_all_returns_empty_when_no_sections(section_service, mock_db):
    """Test getting all sections when none exist."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    result = section_service.get_all()

    assert result == []


def test_get_by_id_returns_specific_section_with_details(section_service, mock_db):
    """Test getting a specific section by ID with related information."""
    _, mock_cursor = mock_db
    section_id = 1
    expected_section = {
        'id': 1, 'instance_id': 1, 'number': 1, 'weight_or_percentage': True,
        'professor_id': 1, 'is_closed': False, 'professor_name': 'Dr. García', 
        'period': '2025-1', 'course_id': 1
    }
    mock_cursor.fetchone.return_value = expected_section

    result = section_service.get_by_id(section_id)

    expected_query = """
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.professor_id, s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE s.id = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (section_id,))
    assert result == expected_section


def test_get_by_id_returns_none_when_not_found(section_service, mock_db):
    """Test getting section by ID when section doesn't exist."""
    _, mock_cursor = mock_db
    section_id = 999
    mock_cursor.fetchone.return_value = None

    result = section_service.get_by_id(section_id)

    assert result is None


def test_get_by_instance_id_returns_instance_sections(section_service, mock_db):
    """Test getting all sections for a specific instance."""
    _, mock_cursor = mock_db
    instance_id = 1
    expected_sections = [
        {
            'id': 1, 'instance_id': 1, 'number': 1, 'weight_or_percentage': True,
            'is_closed': False, 'professor_name': 'Dr. García', 'period': '2025-1', 'course_id': 1
        },
        {
            'id': 2, 'instance_id': 1, 'number': 2, 'weight_or_percentage': False,
            'is_closed': False, 'professor_name': 'Dra. López', 'period': '2025-1', 'course_id': 1
        }
    ]
    mock_cursor.fetchall.return_value = expected_sections

    result = section_service.get_by_instance_id(instance_id)

    expected_query = """
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE s.instance_id = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (instance_id,))
    assert result == expected_sections


def test_get_by_course_id_returns_course_sections(section_service, mock_db):
    """Test getting all sections for a specific course."""
    _, mock_cursor = mock_db
    course_id = 1
    expected_sections = [
        {
            'id': 1, 'instance_id': 1, 'number': 1, 'weight_or_percentage': True,
            'is_closed': False, 'professor_name': 'Dr. García', 'period': '2025-1', 'course_id': 1
        }
    ]
    mock_cursor.fetchall.return_value = expected_sections

    result = section_service.get_by_course_id(course_id)

    expected_query = """
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE i.course_id = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (course_id,))
    assert result == expected_sections


def test_get_by_course_and_period_returns_specific_sections(section_service, mock_db):
    """Test getting all sections for a specific course and period."""
    _, mock_cursor = mock_db
    course_id = 1
    period = '2025-1'
    expected_sections = [
        {
            'id': 1, 'instance_id': 1, 'number': 1, 'weight_or_percentage': True,
            'is_closed': False, 'professor_name': 'Dr. García', 'period': '2025-1', 'course_id': 1
        }
    ]
    mock_cursor.fetchall.return_value = expected_sections

    result = section_service.get_by_course_and_period(course_id, period)

    expected_query = """
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE i.course_id = %s AND i.period = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (course_id, period))
    assert result == expected_sections


def test_get_closed_sections_returns_only_closed_sections(section_service, mock_db):
    """Test getting all closed sections with course and period information."""
    _, mock_cursor = mock_db
    expected_sections = [
        {
            'id': 1, 'number': 1, 'is_closed': True,
            'course_name': 'Diseño de Software', 'period': '2025-1'
        },
        {
            'id': 3, 'number': 2, 'is_closed': True,
            'course_name': 'Programación', 'period': '2024-2'
        }
    ]
    mock_cursor.fetchall.return_value = expected_sections

    result = section_service.get_closed_sections()

    expected_query = """
            SELECT s.id, s.number, s.is_closed,
                   c.name as course_name, i.period
            FROM Sections s
            JOIN Instances i ON s.instance_id = i.id
            JOIN Courses c ON i.course_id = c.id
            WHERE s.is_closed = 1
            ORDER BY c.name, i.period, s.number
        """
    mock_cursor.execute.assert_called_once_with(expected_query)
    assert result == expected_sections


def test_get_closed_sections_returns_empty_when_none_closed(section_service, mock_db):
    """Test getting closed sections when none are closed."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    result = section_service.get_closed_sections()

    assert result == []


def test_get_closed_sections_ordered_correctly(section_service, mock_db):
    """Test that closed sections are properly ordered."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    section_service.get_closed_sections()

    query = mock_cursor.execute.call_args[0][0]
    assert "ORDER BY c.name, i.period, s.number" in query


def test_section_number_exists_returns_true_when_exists(section_service, mock_db):
    """Test checking if section number exists for an instance."""
    _, mock_cursor = mock_db
    instance_id = 1
    number = 1
    mock_cursor.fetchone.return_value = {'count': 1}

    result = section_service.section_number_exists(instance_id, number)

    expected_query = (
        "SELECT COUNT(*) as count FROM Sections "
        "WHERE instance_id = %s AND number = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (instance_id, number))
    assert result is True


def test_section_number_exists_returns_false_when_not_exists(section_service, mock_db):
    """Test checking section number when it doesn't exist."""
    _, mock_cursor = mock_db
    instance_id = 1
    number = 999
    mock_cursor.fetchone.return_value = {'count': 0}

    result = section_service.section_number_exists(instance_id, number)

    assert result is False


def test_section_number_exists_with_exclude_section_id(section_service, mock_db):
    """Test checking section number existence excluding a specific section."""
    _, mock_cursor = mock_db
    instance_id = 1
    number = 1
    exclude_section_id = 5
    mock_cursor.fetchone.return_value = {'count': 0}

    result = section_service.section_number_exists(instance_id, number, exclude_section_id)

    expected_query = (
        "SELECT COUNT(*) as count FROM Sections "
        "WHERE instance_id = %s AND number = %s AND id != %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (instance_id, number, exclude_section_id)
    )
    assert result is False


def test_create_section_success(section_service, mock_db):
    """Test successful creation of a new section."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    instance_id = 1
    number = 1
    professor_id = 1
    weight_or_percentage = True

    result = section_service.create(instance_id, number, professor_id, weight_or_percentage)

    expected_query = (
        "INSERT INTO Sections (instance_id, number, professor_id, "
        "weight_or_percentage, is_closed) VALUES (%s, %s, %s, %s, FALSE)"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (instance_id, number, professor_id, weight_or_percentage)
    )
    mock_db_instance.commit.assert_called_once()
    assert result == 1


def test_create_section_sets_is_closed_to_false(section_service, mock_db):
    """Test that new sections are created with is_closed = FALSE."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    section_service.create(1, 1, 1, True)

    query = mock_cursor.execute.call_args[0][0]
    assert "is_closed) VALUES (%s, %s, %s, %s, FALSE)" in query


def test_update_section_success_when_not_closed(section_service, mock_db):
    """Test successful update of a section that is not closed."""
    mock_db_instance, mock_cursor = mock_db
    section_id = 1
    number = 2
    professor_id = 2
    weight_or_percentage = False

    mock_section = {'is_closed': False}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        section_service.update(section_id, number, professor_id, weight_or_percentage)

    expected_query = (
        "UPDATE Sections SET number = %s, professor_id = %s, "
        "weight_or_percentage = %s WHERE id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (number, professor_id, weight_or_percentage, section_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_update_section_raises_error_when_closed(section_service, mock_db):
    """Test that updating a closed section raises ValueError."""
    section_id = 1
    number = 2
    professor_id = 2
    weight_or_percentage = False

    mock_section = {'is_closed': True}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        with pytest.raises(ValueError, match="Cannot modify a closed section"):
            section_service.update(section_id, number, professor_id, weight_or_percentage)


def test_close_section_success(section_service, mock_db):
    """Test successful closing of a section."""
    mock_db_instance, mock_cursor = mock_db
    section_id = 1

    mock_section = {'id': 1, 'is_closed': False}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        result = section_service.close_section(section_id)

    expected_query = "UPDATE Sections SET is_closed = TRUE WHERE id = %s"
    mock_cursor.execute.assert_called_once_with(expected_query, (section_id,))
    mock_db_instance.commit.assert_called_once()
    assert result is True


def test_close_section_raises_error_when_not_found(section_service, mock_db):
    """Test that closing a non-existent section raises ValueError."""
    section_id = 999

    with patch.object(section_service, 'get_by_id', return_value=None):
        with pytest.raises(ValueError, match="Section not found"):
            section_service.close_section(section_id)


def test_delete_section_success_when_not_closed(section_service, mock_db):
    """Test successful deletion of a section that is not closed."""
    mock_db_instance, mock_cursor = mock_db
    section_id = 1

    mock_section = {'is_closed': False}

    topics = [{'id': 1}]
    activities = [{'id': 1}]
    
    mock_cursor.fetchall.side_effect = [topics, activities]
    
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        section_service.delete(section_id)

    mock_cursor.execute.assert_any_call(
        "DELETE FROM Grades WHERE activity_id = %s", (1,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Activities WHERE topic_id = %s", (1,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Topics WHERE section_id = %s", (section_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Courses_Taken WHERE section_id = %s", (section_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Sections WHERE id = %s", (section_id,)
    )
    
    mock_db_instance.commit.assert_called_once()


def test_delete_section_raises_error_when_closed(section_service, mock_db):
    """Test that deleting a closed section raises ValueError."""
    section_id = 1

    mock_section = {'is_closed': True}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        with pytest.raises(ValueError, match="Cannot delete a closed section"):
            section_service.delete(section_id)


def test_delete_section_with_no_topics(section_service, mock_db):
    """Test deleting a section with no topics."""
    mock_db_instance, mock_cursor = mock_db
    section_id = 1

    mock_section = {'is_closed': False}
    mock_cursor.fetchall.return_value = []
    
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        section_service.delete(section_id)

    mock_cursor.execute.assert_any_call(
        "DELETE FROM Courses_Taken WHERE section_id = %s", (section_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Sections WHERE id = %s", (section_id,)
    )


def test_delete_section_maintains_proper_cascade_order(section_service, mock_db):
    """Test that deletion maintains proper cascade order."""
    mock_db_instance, mock_cursor = mock_db
    section_id = 1

    mock_section = {'is_closed': False}

    topics = [{'id': 1}]
    activities = [{'id': 1}]
    
    mock_cursor.fetchall.side_effect = [topics, activities]
    
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        section_service.delete(section_id)

    delete_calls = [call[0][0] for call in mock_cursor.execute.call_args_list 
                   if call[0][0].startswith('DELETE')]
    
    assert "DELETE FROM Grades" in delete_calls[0]
    assert "DELETE FROM Activities" in delete_calls[1]
    assert "DELETE FROM Topics" in delete_calls[2]
    assert "DELETE FROM Courses_Taken" in delete_calls[3]
    assert "DELETE FROM Sections" in delete_calls[4]


@pytest.mark.parametrize("instance_id,number,professor_id,weight_or_percentage", [
    (1, 1, 1, True),
    (2, 3, 5, False),
    (10, 1, 3, True),
])
def test_create_section_with_various_parameters(section_service, mock_db,
                                               instance_id, number, professor_id, weight_or_percentage):
    """Test section creation with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    result = section_service.create(instance_id, number, professor_id, weight_or_percentage)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (instance_id, number, professor_id, weight_or_percentage)
    mock_db_instance.commit.assert_called_once()
    assert result == 1


@pytest.mark.parametrize("section_id,number,professor_id,weight_or_percentage", [
    (1, 2, 2, False),
    (5, 1, 3, True),
    (10, 3, 1, False),
])
def test_update_section_with_various_parameters(section_service, mock_db,
                                               section_id, number, professor_id, weight_or_percentage):
    """Test section update with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db

    mock_section = {'is_closed': False}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        section_service.update(section_id, number, professor_id, weight_or_percentage)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (number, professor_id, weight_or_percentage, section_id)


def test_section_operations_sequence(section_service, mock_db):
    """Test sequence of section operations."""
    mock_db_instance, mock_cursor = mock_db

    mock_cursor.lastrowid = 1
    section_id = section_service.create(1, 1, 1, True)

    mock_cursor.reset_mock()
    mock_db_instance.reset_mock()

    mock_section = {'is_closed': False}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        section_service.update(section_id, 2, 2, False)

    mock_cursor.reset_mock()
    mock_db_instance.reset_mock()

    mock_section = {'id': section_id, 'is_closed': False}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        section_service.close_section(section_id)

    expected_query = "UPDATE Sections SET is_closed = TRUE WHERE id = %s"
    mock_cursor.execute.assert_called_with(expected_query, (section_id,))


def test_database_error_handling_on_create(section_service, mock_db):
    """Test that database errors during create are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        section_service.create(1, 1, 1, True)


def test_database_error_handling_on_update(section_service, mock_db):
    """Test that database errors during update are properly raised."""
    mock_db_instance, mock_cursor = mock_db

    mock_section = {'is_closed': False}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        mock_cursor.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            section_service.update(1, 1, 1, True)


def test_database_error_handling_on_delete(section_service, mock_db):
    """Test that database errors during delete are properly raised."""
    mock_db_instance, mock_cursor = mock_db

    mock_section = {'is_closed': False}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        mock_cursor.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            section_service.delete(1)


def test_database_error_handling_on_close_section(section_service, mock_db):
    """Test that database errors during close_section are properly raised."""
    mock_db_instance, mock_cursor = mock_db

    mock_section = {'id': 1, 'is_closed': False}
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        mock_cursor.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            section_service.close_section(1)


def test_database_error_handling_on_get_all(section_service, mock_db):
    """Test that database errors during get_all are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        section_service.get_all()


def test_database_error_handling_on_section_number_exists(section_service, mock_db):
    """Test that database errors during section_number_exists are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        section_service.section_number_exists(1, 1)


def test_complex_section_with_multiple_topics_and_activities(section_service, mock_db):
    """Test deletion of section with complex cascade structure."""
    mock_db_instance, mock_cursor = mock_db
    section_id = 1

    mock_section = {'is_closed': False}

    topics = [{'id': 1}, {'id': 2}]
    activities_topic_1 = [{'id': 1}, {'id': 2}]
    activities_topic_2 = [{'id': 3}]
    
    mock_cursor.fetchall.side_effect = [topics, activities_topic_1, activities_topic_2]
    
    with patch.object(section_service, 'get_by_id', return_value=mock_section):
        section_service.delete(section_id)

    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (1,))
    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (2,))
    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (3,))
    mock_cursor.execute.assert_any_call("DELETE FROM Activities WHERE topic_id = %s", (1,))
    mock_cursor.execute.assert_any_call("DELETE FROM Activities WHERE topic_id = %s", (2,))
    mock_cursor.execute.assert_any_call("DELETE FROM Sections WHERE id = %s", (section_id,))