"""Unit tests for InstanceService module.

This module contains comprehensive tests for the InstanceService class,
including CRUD operations, period management, cascading deletions, and relationship handling.
"""

import pytest
from unittest.mock import Mock, patch
from Service.instance_service import InstanceService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def instance_service(mock_db):
    """Create InstanceService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.instance_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return InstanceService()


def test_init_creates_database_connection():
    """Test that InstanceService initializes with database connection."""
    with patch('Service.instance_service.DatabaseConnection') as mock_db_class:
        service = InstanceService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_get_all_returns_instances_with_course_info(instance_service, mock_db):
    """Test getting all instances with course information."""
    _, mock_cursor = mock_db
    expected_instances = [
        {
            'id': 1, 'period': '2025-1', 'course_id': 1,
            'course_name': 'Diseño de Software', 'nrc': 'ICC5130'
        },
        {
            'id': 2, 'period': '2025-2', 'course_id': 2,
            'course_name': 'Programación', 'nrc': 'ICC1102'
        }
    ]
    mock_cursor.fetchall.return_value = expected_instances

    result = instance_service.get_all()

    expected_query = """
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
        """
    mock_cursor.execute.assert_called_once_with(expected_query)
    assert result == expected_instances


def test_get_all_returns_empty_when_no_instances(instance_service, mock_db):
    """Test getting all instances when none exist."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    result = instance_service.get_all()

    assert result == []


def test_get_by_id_returns_specific_instance(instance_service, mock_db):
    """Test getting a specific instance by ID with course information."""
    _, mock_cursor = mock_db
    instance_id = 1
    expected_instance = {
        'id': 1, 'period': '2025-1', 'course_id': 1,
        'course_name': 'Diseño de Software', 'nrc': 'ICC5130'
    }
    mock_cursor.fetchone.return_value = expected_instance

    result = instance_service.get_by_id(instance_id)

    expected_query = """
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
            WHERE i.id = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (instance_id,))
    assert result == expected_instance


def test_get_by_id_returns_none_when_not_found(instance_service, mock_db):
    """Test getting instance by ID when instance doesn't exist."""
    _, mock_cursor = mock_db
    instance_id = 999
    mock_cursor.fetchone.return_value = None

    result = instance_service.get_by_id(instance_id)

    assert result is None


def test_get_by_course_id_returns_course_instances(instance_service, mock_db):
    """Test getting all instances for a specific course."""
    _, mock_cursor = mock_db
    course_id = 1
    expected_instances = [
        {
            'id': 1, 'period': '2025-1', 'course_id': 1,
            'course_name': 'Diseño de Software', 'nrc': 'ICC5130'
        },
        {
            'id': 2, 'period': '2025-2', 'course_id': 1,
            'course_name': 'Diseño de Software', 'nrc': 'ICC5130'
        }
    ]
    mock_cursor.fetchall.return_value = expected_instances

    result = instance_service.get_by_course_id(course_id)

    expected_query = """
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
            WHERE i.course_id = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (course_id,))
    assert result == expected_instances


def test_get_by_course_id_returns_empty_when_none(instance_service, mock_db):
    """Test getting instances by course ID when none exist."""
    _, mock_cursor = mock_db
    course_id = 999
    mock_cursor.fetchall.return_value = []

    result = instance_service.get_by_course_id(course_id)

    assert result == []


def test_get_by_period_returns_period_instances(instance_service, mock_db):
    """Test getting all instances for a specific period."""
    _, mock_cursor = mock_db
    period = '2025-1'
    expected_instances = [
        {
            'id': 1, 'period': '2025-1', 'course_id': 1,
            'course_name': 'Diseño de Software', 'nrc': 'ICC5130'
        },
        {
            'id': 3, 'period': '2025-1', 'course_id': 2,
            'course_name': 'Programación', 'nrc': 'ICC1102'
        }
    ]
    mock_cursor.fetchall.return_value = expected_instances

    result = instance_service.get_by_period(period)

    expected_query = """
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
            WHERE i.period = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (period,))
    assert result == expected_instances


def test_get_by_period_returns_empty_when_none(instance_service, mock_db):
    """Test getting instances by period when none exist."""
    _, mock_cursor = mock_db
    period = '2030-1'
    mock_cursor.fetchall.return_value = []

    result = instance_service.get_by_period(period)

    assert result == []


def test_get_by_course_and_period_returns_specific_instance(instance_service, mock_db):
    """Test getting a specific instance by course and period."""
    _, mock_cursor = mock_db
    course_id = 1
    period = '2025-1'
    expected_instance = {
        'id': 1, 'period': '2025-1', 'course_id': 1,
        'course_name': 'Diseño de Software', 'nrc': 'ICC5130'
    }
    mock_cursor.fetchone.return_value = expected_instance

    result = instance_service.get_by_course_and_period(course_id, period)

    expected_query = """
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
            WHERE i.course_id = %s AND i.period = %s
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (course_id, period))
    assert result == expected_instance


def test_get_by_course_and_period_returns_none_when_not_found(instance_service, mock_db):
    """Test getting instance by course and period when combination doesn't exist."""
    _, mock_cursor = mock_db
    course_id = 999
    period = '2030-1'
    mock_cursor.fetchone.return_value = None

    result = instance_service.get_by_course_and_period(course_id, period)

    assert result is None


def test_create_instance_success(instance_service, mock_db):
    """Test successful creation of a new instance."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    course_id = 1
    period = '2025-1'

    result = instance_service.create(course_id, period)

    expected_query = "INSERT INTO Instances (course_id, period) VALUES (%s, %s)"
    mock_cursor.execute.assert_called_once_with(expected_query, (course_id, period))
    mock_db_instance.commit.assert_called_once()
    assert result == 1


def test_update_instance_success(instance_service, mock_db):
    """Test successful update of an instance period."""
    mock_db_instance, mock_cursor = mock_db
    instance_id = 1
    new_period = '2025-2'

    instance_service.update(instance_id, new_period)

    expected_query = "UPDATE Instances SET period = %s WHERE id = %s"
    mock_cursor.execute.assert_called_once_with(expected_query, (new_period, instance_id))
    mock_db_instance.commit.assert_called_once()


def test_delete_instance_with_cascading_relations(instance_service, mock_db):
    """Test deleting an instance with cascading deletion of related data."""
    mock_db_instance, mock_cursor = mock_db
    instance_id = 1
    
    sections = [{'id': 1}]
    topics = [{'id': 1}]
    activities = [{'id': 1}]
    
    mock_cursor.fetchall.side_effect = [
        sections,
        topics,
        activities,
    ]

    instance_service.delete(instance_id)

    mock_cursor.execute.assert_any_call(
        "SELECT id FROM Sections WHERE instance_id = %s", (instance_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Grades WHERE activity_id = %s", (1,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Activities WHERE topic_id = %s", (1,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Topics WHERE section_id = %s", (1,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Courses_Taken WHERE section_id = %s", (1,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Sections WHERE id = %s", (1,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Instances WHERE id = %s", (instance_id,)
    )
    
    mock_db_instance.commit.assert_called_once()


def test_delete_instance_with_no_sections(instance_service, mock_db):
    """Test deleting an instance with no sections."""
    mock_db_instance, mock_cursor = mock_db
    instance_id = 1

    mock_cursor.fetchall.return_value = []

    instance_service.delete(instance_id)

    mock_cursor.execute.assert_any_call(
        "DELETE FROM Instances WHERE id = %s", (instance_id,)
    )
    mock_db_instance.commit.assert_called_once()


def test_delete_instance_maintains_proper_order(instance_service, mock_db):
    """Test that delete maintains proper order of cascading deletions."""
    mock_db_instance, mock_cursor = mock_db
    instance_id = 1
    
    sections = [{'id': 1}]
    topics = [{'id': 1}]
    activities = [{'id': 1}]
    
    mock_cursor.fetchall.side_effect = [sections, topics, activities]

    instance_service.delete(instance_id)

    calls = [call[0][0] for call in mock_cursor.execute.call_args_list if call[0][0].startswith('DELETE')]
    
    assert "DELETE FROM Grades" in calls[0]
    assert "DELETE FROM Activities" in calls[1]
    assert "DELETE FROM Topics" in calls[2]
    assert "DELETE FROM Courses_Taken" in calls[3]
    assert "DELETE FROM Sections" in calls[4]
    assert "DELETE FROM Instances" in calls[5]


def test_get_periods_returns_distinct_periods_ordered(instance_service, mock_db):
    """Test getting all distinct periods ordered by most recent."""
    _, mock_cursor = mock_db
    expected_periods_data = [
        {'period': '2025-2'},
        {'period': '2025-1'},
        {'period': '2024-2'}
    ]
    mock_cursor.fetchall.return_value = expected_periods_data

    result = instance_service.get_periods()

    expected_query = ("SELECT DISTINCT period FROM Instances "
                     "ORDER BY period DESC")
    mock_cursor.execute.assert_called_once_with(expected_query)
    
    expected_periods = ['2025-2', '2025-1', '2024-2']
    assert result == expected_periods


def test_get_periods_returns_empty_when_no_instances(instance_service, mock_db):
    """Test getting periods when no instances exist."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    result = instance_service.get_periods()

    assert result == []


def test_get_section_count_returns_count(instance_service, mock_db):
    """Test getting the count of sections for a specific instance."""
    _, mock_cursor = mock_db
    instance_id = 1
    expected_count = 3
    mock_cursor.fetchone.return_value = {'count': expected_count}

    result = instance_service.get_section_count(instance_id)

    expected_query = ("SELECT COUNT(*) as count FROM Sections "
                     "WHERE instance_id = %s")
    mock_cursor.execute.assert_called_once_with(expected_query, (instance_id,))
    assert result == expected_count


def test_get_section_count_returns_zero_when_no_sections(instance_service, mock_db):
    """Test getting section count when instance has no sections."""
    _, mock_cursor = mock_db
    instance_id = 999
    mock_cursor.fetchone.return_value = {'count': 0}

    result = instance_service.get_section_count(instance_id)

    assert result == 0


@pytest.mark.parametrize("course_id,period", [
    (1, '2025-1'),
    (5, '2024-2'),
    (10, '2026-1'),
])
def test_create_instance_with_various_parameters(instance_service, mock_db,
                                                course_id, period):
    """Test instance creation with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    result = instance_service.create(course_id, period)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (course_id, period)
    mock_db_instance.commit.assert_called_once()
    assert result == 1


@pytest.mark.parametrize("period", [
    '2025-1', '2025-2', '2024-1', '2026-1'
])
def test_update_instance_with_various_periods(instance_service, mock_db, period):
    """Test updating instance with various period values."""
    mock_db_instance, mock_cursor = mock_db
    instance_id = 1

    instance_service.update(instance_id, period)

    args = mock_cursor.execute.call_args[0][1]
    assert args[0] == period
    assert args[1] == instance_id


def test_complex_cascading_delete_with_multiple_entities(instance_service, mock_db):
    """Test complex cascading delete with multiple sections, topics, and activities."""
    mock_db_instance, mock_cursor = mock_db
    instance_id = 1

    sections = [{'id': 1}, {'id': 2}]
    topics_section_1 = [{'id': 1}, {'id': 2}]
    activities_topic_1 = [{'id': 1}]
    activities_topic_2 = [{'id': 2}, {'id': 3}]
    topics_section_2 = [{'id': 3}]
    activities_topic_3 = [{'id': 4}]
    
    mock_cursor.fetchall.side_effect = [
        sections,
        topics_section_1,
        activities_topic_1,
        activities_topic_2,
        topics_section_2,
        activities_topic_3,
    ]

    instance_service.delete(instance_id)

    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (1,))
    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (2,))
    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (3,))
    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (4,))

    mock_cursor.execute.assert_any_call("DELETE FROM Instances WHERE id = %s", (instance_id,))


def test_database_error_handling_on_create(instance_service, mock_db):
    """Test that database errors during create are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        instance_service.create(1, '2025-1')


def test_database_error_handling_on_update(instance_service, mock_db):
    """Test that database errors during update are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        instance_service.update(1, '2025-1')


def test_database_error_handling_on_delete(instance_service, mock_db):
    """Test that database errors during delete are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        instance_service.delete(1)


def test_database_error_handling_on_get_by_id(instance_service, mock_db):
    """Test that database errors during get_by_id are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        instance_service.get_by_id(1)


def test_database_error_handling_on_get_periods(instance_service, mock_db):
    """Test that database errors during get_periods are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        instance_service.get_periods()


def test_database_error_handling_on_get_section_count(instance_service, mock_db):
    """Test that database errors during get_section_count are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        instance_service.get_section_count(1)


def test_get_periods_extracts_period_values_correctly(instance_service, mock_db):
    """Test that get_periods correctly extracts period values from result dictionaries."""
    _, mock_cursor = mock_db
    periods_data = [
        {'period': '2025-2', 'other_field': 'ignore'},
        {'period': '2025-1', 'another_field': 'ignore'},
        {'period': '2024-2', 'extra_field': 'ignore'}
    ]
    mock_cursor.fetchall.return_value = periods_data

    result = instance_service.get_periods()

    expected_periods = ['2025-2', '2025-1', '2024-2']
    assert result == expected_periods