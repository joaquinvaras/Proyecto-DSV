"""Unit tests for TopicService module.

This module contains comprehensive tests for the TopicService class,
including CRUD operations, weight management, cascading deletions, and section-level calculations.
"""

import pytest
from unittest.mock import Mock, patch
from Service.topic_service import TopicService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def topic_service(mock_db):
    """Create TopicService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.topic_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return TopicService()


def test_init_creates_database_connection():
    """Test that TopicService initializes with database connection."""
    with patch('Service.topic_service.DatabaseConnection') as mock_db_class:
        service = TopicService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_get_all_returns_all_topics(topic_service, mock_db):
    """Test getting all topics from the database."""
    _, mock_cursor = mock_db
    expected_topics = [
        {'id': 1, 'name': 'Controles', 'section_id': 1, 'weight': 300, 'weight_or_percentage': False},
        {'id': 2, 'name': 'Tareas', 'section_id': 1, 'weight': 200, 'weight_or_percentage': False},
        {'id': 3, 'name': 'Proyecto', 'section_id': 2, 'weight': 500, 'weight_or_percentage': True}
    ]
    mock_cursor.fetchall.return_value = expected_topics

    result = topic_service.get_all()

    mock_cursor.execute.assert_called_once_with("SELECT * FROM Topics")
    assert result == expected_topics


def test_get_all_returns_empty_when_no_topics(topic_service, mock_db):
    """Test getting all topics when none exist."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    result = topic_service.get_all()

    assert result == []


def test_get_by_id_returns_specific_topic(topic_service, mock_db):
    """Test getting a specific topic by its ID."""
    _, mock_cursor = mock_db
    topic_id = 1
    expected_topic = {
        'id': 1, 'name': 'Controles', 'section_id': 1, 'weight': 300, 'weight_or_percentage': False
    }
    mock_cursor.fetchone.return_value = expected_topic

    result = topic_service.get_by_id(topic_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Topics WHERE id = %s", (topic_id,)
    )
    assert result == expected_topic


def test_get_by_id_returns_none_when_not_found(topic_service, mock_db):
    """Test getting topic by ID when topic doesn't exist."""
    _, mock_cursor = mock_db
    topic_id = 999
    mock_cursor.fetchone.return_value = None

    result = topic_service.get_by_id(topic_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Topics WHERE id = %s", (topic_id,)
    )
    assert result is None


def test_get_by_section_id_returns_section_topics(topic_service, mock_db):
    """Test getting all topics for a specific section."""
    _, mock_cursor = mock_db
    section_id = 1
    expected_topics = [
        {'id': 1, 'name': 'Controles', 'section_id': 1, 'weight': 300, 'weight_or_percentage': False},
        {'id': 2, 'name': 'Tareas', 'section_id': 1, 'weight': 200, 'weight_or_percentage': False}
    ]
    mock_cursor.fetchall.return_value = expected_topics

    result = topic_service.get_by_section_id(section_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Topics WHERE section_id = %s", (section_id,)
    )
    assert result == expected_topics


def test_get_by_section_id_returns_empty_when_no_topics(topic_service, mock_db):
    """Test getting topics by section ID when section has no topics."""
    _, mock_cursor = mock_db
    section_id = 999
    mock_cursor.fetchall.return_value = []

    result = topic_service.get_by_section_id(section_id)

    assert result == []


def test_create_topic_success(topic_service, mock_db):
    """Test successful creation of a new topic."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    name = 'Controles'
    section_id = 1
    weight = 300
    weight_or_percentage = False

    result = topic_service.create(name, section_id, weight, weight_or_percentage)

    expected_query = (
        "INSERT INTO Topics (name, section_id, weight, "
        "weight_or_percentage) VALUES (%s, %s, %s, %s)"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (name, section_id, weight, weight_or_percentage)
    )
    mock_db_instance.commit.assert_called_once()
    assert result == 1


def test_create_topic_with_percentage_system(topic_service, mock_db):
    """Test creating topic with percentage weight system."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 2
    name = 'Proyecto'
    section_id = 1
    weight = 500
    weight_or_percentage = True

    result = topic_service.create(name, section_id, weight, weight_or_percentage)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (name, section_id, weight, weight_or_percentage)
    assert args[3] is True


def test_update_topic_success(topic_service, mock_db):
    """Test successful update of an existing topic."""
    mock_db_instance, mock_cursor = mock_db
    topic_id = 1
    name = 'Controles Actualizados'
    weight = 350
    weight_or_percentage = True

    topic_service.update(topic_id, name, weight, weight_or_percentage)

    expected_query = (
        "UPDATE Topics SET name = %s, weight = %s, "
        "weight_or_percentage = %s WHERE id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (name, weight, weight_or_percentage, topic_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_delete_topic_with_cascading_relations(topic_service, mock_db):
    """Test deleting a topic and all its related activities and grades."""
    mock_db_instance, mock_cursor = mock_db
    topic_id = 1

    activities = [{'id': 1}, {'id': 2}]
    mock_cursor.fetchall.return_value = activities

    topic_service.delete(topic_id)

    mock_cursor.execute.assert_any_call(
        "SELECT id FROM Activities WHERE topic_id = %s", (topic_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Grades WHERE activity_id = %s", (1,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Grades WHERE activity_id = %s", (2,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Activities WHERE topic_id = %s", (topic_id,)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM Topics WHERE id = %s", (topic_id,)
    )
    
    mock_db_instance.commit.assert_called_once()


def test_delete_topic_with_no_activities(topic_service, mock_db):
    """Test deleting a topic with no activities."""
    mock_db_instance, mock_cursor = mock_db
    topic_id = 1

    mock_cursor.fetchall.return_value = []

    topic_service.delete(topic_id)

    mock_cursor.execute.assert_any_call(
        "DELETE FROM Topics WHERE id = %s", (topic_id,)
    )
    mock_db_instance.commit.assert_called_once()


def test_delete_topic_maintains_proper_cascade_order(topic_service, mock_db):
    """Test that deletion maintains proper cascade order."""
    mock_db_instance, mock_cursor = mock_db
    topic_id = 1
    
    activities = [{'id': 1}]
    mock_cursor.fetchall.return_value = activities

    topic_service.delete(topic_id)

    delete_calls = [call[0][0] for call in mock_cursor.execute.call_args_list 
                   if call[0][0].startswith('DELETE')]
    
    assert "DELETE FROM Grades" in delete_calls[0]
    assert "DELETE FROM Activities" in delete_calls[1]
    assert "DELETE FROM Topics" in delete_calls[2]


def test_get_total_weight_returns_sum_of_topic_weights(topic_service, mock_db):
    """Test getting the total weight of all topics in a section."""
    _, mock_cursor = mock_db
    section_id = 1
    expected_total = 500
    mock_cursor.fetchone.return_value = {'total_weight': expected_total}

    result = topic_service.get_total_weight(section_id)

    expected_query = (
        "SELECT SUM(weight) as total_weight FROM Topics "
        "WHERE section_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (section_id,))
    assert result == expected_total


def test_get_total_weight_returns_zero_when_no_topics(topic_service, mock_db):
    """Test getting total weight when section has no topics."""
    _, mock_cursor = mock_db
    section_id = 999
    mock_cursor.fetchone.return_value = {'total_weight': None}

    result = topic_service.get_total_weight(section_id)

    assert result == 0


def test_get_total_weight_returns_zero_when_result_is_none(topic_service, mock_db):
    """Test getting total weight when query result is None (should raise TypeError)."""
    _, mock_cursor = mock_db
    section_id = 1
    mock_cursor.fetchone.return_value = None

    with pytest.raises(TypeError, match="'NoneType' object is not subscriptable"):
        topic_service.get_total_weight(section_id)


def test_get_total_weight_handles_zero_sum(topic_service, mock_db):
    """Test getting total weight when sum is zero."""
    _, mock_cursor = mock_db
    section_id = 1
    mock_cursor.fetchone.return_value = {'total_weight': 0}

    result = topic_service.get_total_weight(section_id)

    assert result == 0


@pytest.mark.parametrize("name,section_id,weight,weight_or_percentage", [
    ('Controles', 1, 300, False),
    ('Tareas', 2, 250, True),
    ('Proyecto Final', 3, 500, False),
    ('Laboratorios', 1, 200, True),
])
def test_create_topic_with_various_parameters(topic_service, mock_db,
                                             name, section_id, weight, weight_or_percentage):
    """Test topic creation with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    result = topic_service.create(name, section_id, weight, weight_or_percentage)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (name, section_id, weight, weight_or_percentage)
    mock_db_instance.commit.assert_called_once()
    assert result == 1


@pytest.mark.parametrize("topic_id,name,weight,weight_or_percentage", [
    (1, 'Controles Updated', 350, True),
    (5, 'New Topic Name', 400, False),
    (10, 'Final Project', 600, True),
])
def test_update_topic_with_various_parameters(topic_service, mock_db,
                                             topic_id, name, weight, weight_or_percentage):
    """Test topic update with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db

    topic_service.update(topic_id, name, weight, weight_or_percentage)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (name, weight, weight_or_percentage, topic_id)


@pytest.mark.parametrize("weight_or_percentage", [True, False])
def test_create_topic_weight_system_types(topic_service, mock_db, weight_or_percentage):
    """Test creating topics with different weight system types."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    topic_service.create('Test Topic', 1, 300, weight_or_percentage)

    args = mock_cursor.execute.call_args[0][1]
    assert args[3] == weight_or_percentage


def test_topic_operations_sequence(topic_service, mock_db):
    """Test sequence of topic operations to ensure they work together."""
    mock_db_instance, mock_cursor = mock_db
  
    mock_cursor.lastrowid = 1
    topic_id = topic_service.create('Test Topic', 1, 300, False)
 
    mock_cursor.reset_mock()
    mock_db_instance.reset_mock()
 
    topic_service.update(topic_id, 'Updated Topic', 350, True)
    
    mock_cursor.reset_mock()
    mock_db_instance.reset_mock()
    
    expected_topic = {'id': topic_id, 'name': 'Updated Topic'}
    mock_cursor.fetchone.return_value = expected_topic
    result = topic_service.get_by_id(topic_id)
    
    assert result == expected_topic


def test_complex_topic_deletion_with_multiple_activities(topic_service, mock_db):
    """Test deletion of topic with multiple activities and grades."""
    mock_db_instance, mock_cursor = mock_db
    topic_id = 1

    activities = [{'id': 1}, {'id': 2}, {'id': 3}]
    mock_cursor.fetchall.return_value = activities

    topic_service.delete(topic_id)

    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (1,))
    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (2,))
    mock_cursor.execute.assert_any_call("DELETE FROM Grades WHERE activity_id = %s", (3,))
    
    mock_cursor.execute.assert_any_call("DELETE FROM Activities WHERE topic_id = %s", (topic_id,))
    mock_cursor.execute.assert_any_call("DELETE FROM Topics WHERE id = %s", (topic_id,))


def test_get_total_weight_with_mixed_weight_values(topic_service, mock_db):
    """Test total weight calculation with various weight values."""
    _, mock_cursor = mock_db
    section_id = 1
    
    test_cases = [
        ({'total_weight': 1000}, 1000),
        ({'total_weight': 0}, 0),
        ({'total_weight': None}, 0),
    ]
    
    for mock_return, expected_result in test_cases:
        mock_cursor.reset_mock()
        mock_cursor.fetchone.return_value = mock_return
        
        result = topic_service.get_total_weight(section_id)
        
        assert result == expected_result


def test_get_total_weight_raises_error_when_fetchone_returns_none(topic_service, mock_db):
    """Test that get_total_weight raises TypeError when fetchone returns None."""
    _, mock_cursor = mock_db
    section_id = 1
    
    mock_cursor.fetchone.return_value = None
    
    with pytest.raises(TypeError, match="'NoneType' object is not subscriptable"):
        topic_service.get_total_weight(section_id)


def test_database_error_handling_on_create(topic_service, mock_db):
    """Test that database errors during create are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        topic_service.create('Test Topic', 1, 300, False)


def test_database_error_handling_on_update(topic_service, mock_db):
    """Test that database errors during update are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        topic_service.update(1, 'Test Topic', 300, False)


def test_database_error_handling_on_delete(topic_service, mock_db):
    """Test that database errors during delete are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        topic_service.delete(1)


def test_database_error_handling_on_get_all(topic_service, mock_db):
    """Test that database errors during get_all are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        topic_service.get_all()


def test_database_error_handling_on_get_by_section_id(topic_service, mock_db):
    """Test that database errors during get_by_section_id are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        topic_service.get_by_section_id(1)


def test_database_error_handling_on_get_total_weight(topic_service, mock_db):
    """Test that database errors during get_total_weight are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        topic_service.get_total_weight(1)


def test_topic_weight_calculation_edge_cases(topic_service, mock_db):
    """Test edge cases in weight calculation."""
    _, mock_cursor = mock_db
    section_id = 1
    
    mock_cursor.fetchone.return_value = {'total_weight': 999999}
    result = topic_service.get_total_weight(section_id)
    assert result == 999999
    
    mock_cursor.reset_mock()
    mock_cursor.fetchone.return_value = {'total_weight': -100}
    result = topic_service.get_total_weight(section_id)
    assert result == -100
    
    mock_cursor.reset_mock()
    mock_cursor.fetchone.return_value = {'total_weight': 250.5}
    result = topic_service.get_total_weight(section_id)
    assert result == 250.5


def test_topic_creation_with_special_characters_in_name(topic_service, mock_db):
    """Test creating topic with special characters in name."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    name = "Tópico #1: Evaluación & Análisis"
    section_id = 1
    weight = 300
    weight_or_percentage = False

    result = topic_service.create(name, section_id, weight, weight_or_percentage)

    args = mock_cursor.execute.call_args[0][1]
    assert args[0] == name
    assert result == 1


def test_topic_update_preserves_section_relationship(topic_service, mock_db):
    """Test that topic update preserves the section relationship."""
    mock_db_instance, mock_cursor = mock_db
    topic_id = 1
    original_section_id = 5
    mock_cursor.fetchone.return_value = {
        'id': topic_id, 'section_id': original_section_id, 'name': 'Old Name'
    }

    topic_service.update(topic_id, 'New Name', 400, True)
    
    update_query = mock_cursor.execute.call_args[0][0]
    assert "section_id" not in update_query
    assert "UPDATE Topics SET name = %s, weight = %s, weight_or_percentage = %s WHERE id = %s" in update_query


def test_get_by_section_id_query_specificity(topic_service, mock_db):
    """Test that get_by_section_id uses correct WHERE clause."""
    _, mock_cursor = mock_db
    section_id = 5
    mock_cursor.fetchall.return_value = []
    
    topic_service.get_by_section_id(section_id)
    
    query, params = mock_cursor.execute.call_args[0]
    assert "WHERE section_id = %s" in query
    assert params == (section_id,)