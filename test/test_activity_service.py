"""Unit tests for ActivityService module.

This module contains comprehensive tests for the ActivityService class,
including CRUD operations, instance numbering, and contextual queries.
"""

import pytest
from unittest.mock import Mock, patch
from Service.activity_service import ActivityService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def activity_service(mock_db):
    """Create ActivityService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.activity_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return ActivityService()


def test_init_creates_database_connection():
    """Test that ActivityService initializes with database connection."""
    with patch('Service.activity_service.DatabaseConnection') as mock_db_class:
        service = ActivityService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_get_all_returns_all_activities(activity_service, mock_db):
    """Test getting all activities from database."""
    _, mock_cursor = mock_db
    expected_activities = [
        {'id': 1, 'topic_id': 1, 'instance': 1, 'weight': 100},
        {'id': 2, 'topic_id': 1, 'instance': 2, 'weight': 150}
    ]
    mock_cursor.fetchall.return_value = expected_activities

    result = activity_service.get_all()

    mock_cursor.execute.assert_called_once_with("SELECT * FROM Activities")
    assert result == expected_activities


def test_get_by_id_returns_specific_activity(activity_service, mock_db):
    """Test getting a specific activity by ID."""
    _, mock_cursor = mock_db
    activity_id = 1
    expected_activity = {
        'id': 1, 'topic_id': 1, 'instance': 1, 'weight': 100
    }
    mock_cursor.fetchone.return_value = expected_activity

    result = activity_service.get_by_id(activity_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Activities WHERE id = %s", (activity_id,)
    )
    assert result == expected_activity


def test_get_by_id_returns_none_when_not_found(activity_service, mock_db):
    """Test getting activity by ID when activity doesn't exist."""
    _, mock_cursor = mock_db
    activity_id = 999
    mock_cursor.fetchone.return_value = None

    result = activity_service.get_by_id(activity_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Activities WHERE id = %s", (activity_id,)
    )
    assert result is None


def test_get_by_topic_id_returns_activities_ordered(activity_service, mock_db):
    """Test getting activities by topic ID ordered by instance."""
    _, mock_cursor = mock_db
    topic_id = 1
    expected_activities = [
        {'id': 1, 'topic_id': 1, 'instance': 1, 'weight': 100},
        {'id': 2, 'topic_id': 1, 'instance': 2, 'weight': 150}
    ]
    mock_cursor.fetchall.return_value = expected_activities

    result = activity_service.get_by_topic_id(topic_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Activities WHERE topic_id = %s ORDER BY instance",
        (topic_id,)
    )
    assert result == expected_activities


def test_get_by_topic_id_returns_empty_list_when_none_found(activity_service, mock_db):
    """Test getting activities by topic ID when none exist."""
    _, mock_cursor = mock_db
    topic_id = 999
    mock_cursor.fetchall.return_value = []

    result = activity_service.get_by_topic_id(topic_id)

    assert result == []


def test_get_all_with_context_returns_detailed_info(activity_service, mock_db):
    """Test getting all activities with contextual information."""
    _, mock_cursor = mock_db
    expected_activities = [
        {
            'id': 1, 'instance': 1, 'weight': 100,
            'topic_name': 'Controles', 'section_number': 1,
            'course_name': 'Diseño de Software', 'period': '2025-1'
        }
    ]
    mock_cursor.fetchall.return_value = expected_activities

    result = activity_service.get_all_with_context()

    expected_query = """
            SELECT a.id, a.instance, a.weight,
                   t.name as topic_name,
                   s.number as section_number,
                   c.name as course_name, i.period
            FROM Activities a
            JOIN Topics t ON a.topic_id = t.id
            JOIN Sections s ON t.section_id = s.id
            JOIN Instances i ON s.instance_id = i.id
            JOIN Courses c ON i.course_id = c.id
            ORDER BY c.name, i.period, s.number, t.name, a.instance
        """
    mock_cursor.execute.assert_called_once_with(expected_query)
    assert result == expected_activities


def test_get_next_instance_number_first_instance(activity_service, mock_db):
    """Test getting next instance number when no activities exist."""
    _, mock_cursor = mock_db
    topic_id = 1
    mock_cursor.fetchone.return_value = {'max_instance': None}

    result = activity_service.get_next_instance_number(topic_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT MAX(instance) as max_instance FROM Activities "
        "WHERE topic_id = %s",
        (topic_id,)
    )
    assert result == 1


def test_get_next_instance_number_increments_existing(activity_service, mock_db):
    """Test getting next instance number when activities exist."""
    _, mock_cursor = mock_db
    topic_id = 1
    mock_cursor.fetchone.return_value = {'max_instance': 3}

    result = activity_service.get_next_instance_number(topic_id)

    assert result == 4


def test_get_next_instance_number_handles_none_result(activity_service, mock_db):
    """Test getting next instance number when result is None."""
    _, mock_cursor = mock_db
    topic_id = 1
    mock_cursor.fetchone.return_value = None

    result = activity_service.get_next_instance_number(topic_id)

    assert result == 1


def test_create_activity_success(activity_service, mock_db):
    """Test successful creation of a new activity."""
    mock_db_instance, mock_cursor = mock_db
    topic_id = 1
    instance = 1
    weight = 100
    optional_flag = False

    activity_service.create(topic_id, instance, weight, optional_flag)

    expected_query = (
        "INSERT INTO Activities (topic_id, instance, weight, "
        "optional_flag) VALUES (%s, %s, %s, %s)"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (topic_id, instance, weight, optional_flag)
    )
    mock_db_instance.commit.assert_called_once()


def test_create_activity_with_optional_flag_true(activity_service, mock_db):
    """Test creating an optional activity."""
    mock_db_instance, mock_cursor = mock_db
    topic_id = 1
    instance = 1
    weight = 100
    optional_flag = True

    activity_service.create(topic_id, instance, weight, optional_flag)

    mock_cursor.execute.assert_called_once()
    args = mock_cursor.execute.call_args[0][1]
    assert args[3] is True


def test_update_activity_success(activity_service, mock_db):
    """Test successful update of an existing activity."""
    mock_db_instance, mock_cursor = mock_db
    activity_id = 1
    instance = 2
    weight = 150
    optional_flag = True

    activity_service.update(activity_id, instance, weight, optional_flag)

    expected_query = (
        "UPDATE Activities SET instance = %s, weight = %s, "
        "optional_flag = %s WHERE id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (instance, weight, optional_flag, activity_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_delete_activity_removes_grades_and_activity(activity_service, mock_db):
    """Test deletion of activity and its associated grades."""
    mock_db_instance, mock_cursor = mock_db
    activity_id = 1

    activity_service.delete(activity_id)

    mock_cursor.execute.assert_any_call(
        "DELETE FROM Grades WHERE activity_id = %s", (activity_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Activities WHERE id = %s", (activity_id,)
    )
    assert mock_cursor.execute.call_count == 2
    mock_db_instance.commit.assert_called_once()


def test_delete_activity_maintains_order(activity_service, mock_db):
    """Test that deletion maintains proper order of operations."""
    mock_db_instance, mock_cursor = mock_db
    activity_id = 1

    activity_service.delete(activity_id)

    calls = mock_cursor.execute.call_args_list
    grades_call = calls[0][0][0]
    activity_call = calls[1][0][0]
    
    assert "DELETE FROM Grades" in grades_call
    assert "DELETE FROM Activities" in activity_call


@pytest.mark.parametrize("topic_id,instance,weight,optional_flag", [
    (1, 1, 100, False),
    (2, 3, 250, True),
    (5, 1, 50, False),
])
def test_create_with_various_parameters(activity_service, mock_db,
                                       topic_id, instance, weight, optional_flag):
    """Test creation with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db

    activity_service.create(topic_id, instance, weight, optional_flag)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (topic_id, instance, weight, optional_flag)
    mock_db_instance.commit.assert_called_once()


@pytest.mark.parametrize("max_instance,expected_next", [
    (None, 1),
    (0, 1),
    (1, 2),
    (5, 6),
    (10, 11),
])
def test_get_next_instance_number_edge_cases(activity_service, mock_db,
                                            max_instance, expected_next):
    """Test next instance number calculation with edge cases."""
    _, mock_cursor = mock_db
    topic_id = 1
    
    if max_instance is None:
        mock_cursor.fetchone.return_value = {'max_instance': None}
    else:
        mock_cursor.fetchone.return_value = {'max_instance': max_instance}

    result = activity_service.get_next_instance_number(topic_id)

    assert result == expected_next


def test_database_error_handling_on_create(activity_service, mock_db):
    """Test that database errors during create are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        activity_service.create(1, 1, 100, False)


def test_database_error_handling_on_update(activity_service, mock_db):
    """Test that database errors during update are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        activity_service.update(1, 1, 100, False)


def test_database_error_handling_on_delete(activity_service, mock_db):
    """Test that database errors during delete are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        activity_service.delete(1)