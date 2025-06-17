"""Unit tests for RoomService module.

This module contains comprehensive tests for the RoomService class,
including CRUD operations, capacity management, availability checking, and room search functionality.
"""

import pytest
from unittest.mock import Mock, patch
from Service.room_service import RoomService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def room_service(mock_db):
    """Create RoomService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.room_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return RoomService()


def test_init_creates_database_connection():
    """Test that RoomService initializes with database connection."""
    with patch('Service.room_service.DatabaseConnection') as mock_db_class:
        service = RoomService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_get_all_returns_rooms_ordered_by_name(room_service, mock_db):
    """Test getting all rooms ordered by name."""
    _, mock_cursor = mock_db
    expected_rooms = [
        {'id': 1, 'name': 'Aula 101', 'capacity': 30},
        {'id': 2, 'name': 'Laboratorio A', 'capacity': 25},
        {'id': 3, 'name': 'Sala Magna', 'capacity': 200}
    ]
    mock_cursor.fetchall.return_value = expected_rooms

    result = room_service.get_all()

    mock_cursor.execute.assert_called_once_with("SELECT * FROM Rooms ORDER BY name")
    assert result == expected_rooms


def test_get_all_returns_empty_when_no_rooms(room_service, mock_db):
    """Test getting all rooms when none exist."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    result = room_service.get_all()

    assert result == []


def test_get_by_id_returns_specific_room(room_service, mock_db):
    """Test getting a specific room by its ID."""
    _, mock_cursor = mock_db
    room_id = 1
    expected_room = {'id': 1, 'name': 'Aula 101', 'capacity': 30}
    mock_cursor.fetchone.return_value = expected_room

    result = room_service.get_by_id(room_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Rooms WHERE id = %s", (room_id,)
    )
    assert result == expected_room


def test_get_by_id_returns_none_when_not_found(room_service, mock_db):
    """Test getting room by ID when room doesn't exist."""
    _, mock_cursor = mock_db
    room_id = 999
    mock_cursor.fetchone.return_value = None

    result = room_service.get_by_id(room_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Rooms WHERE id = %s", (room_id,)
    )
    assert result is None


def test_get_by_name_returns_specific_room(room_service, mock_db):
    """Test getting a specific room by its name."""
    _, mock_cursor = mock_db
    room_name = 'Aula 101'
    expected_room = {'id': 1, 'name': 'Aula 101', 'capacity': 30}
    mock_cursor.fetchone.return_value = expected_room

    result = room_service.get_by_name(room_name)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Rooms WHERE name = %s", (room_name,)
    )
    assert result == expected_room


def test_get_by_name_returns_none_when_not_found(room_service, mock_db):
    """Test getting room by name when room doesn't exist."""
    _, mock_cursor = mock_db
    room_name = 'Nonexistent Room'
    mock_cursor.fetchone.return_value = None

    result = room_service.get_by_name(room_name)

    assert result is None


def test_create_room_success(room_service, mock_db):
    """Test successful creation of a new room."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    name = 'Aula 101'
    capacity = 30

    result = room_service.create(name, capacity)

    expected_query = "INSERT INTO Rooms (name, capacity) VALUES (%s, %s)"
    mock_cursor.execute.assert_called_once_with(expected_query, (name, capacity))
    mock_db_instance.commit.assert_called_once()
    assert result == 1


def test_create_room_returns_lastrowid(room_service, mock_db):
    """Test that create returns the correct last row ID."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 5
    name = 'Nueva Aula'
    capacity = 50

    result = room_service.create(name, capacity)

    assert result == 5


def test_update_room_success(room_service, mock_db):
    """Test successful update of an existing room."""
    mock_db_instance, mock_cursor = mock_db
    room_id = 1
    name = 'Aula 101 - Renovada'
    capacity = 35

    room_service.update(room_id, name, capacity)

    expected_query = "UPDATE Rooms SET name = %s, capacity = %s WHERE id = %s"
    mock_cursor.execute.assert_called_once_with(
        expected_query, (name, capacity, room_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_delete_room_success(room_service, mock_db):
    """Test successful deletion of a room."""
    mock_db_instance, mock_cursor = mock_db
    room_id = 1

    room_service.delete(room_id)

    expected_query = "DELETE FROM Rooms WHERE id = %s"
    mock_cursor.execute.assert_called_once_with(expected_query, (room_id,))
    mock_db_instance.commit.assert_called_once()


def test_search_rooms_returns_matching_rooms(room_service, mock_db):
    """Test searching for rooms by name pattern."""
    _, mock_cursor = mock_db
    query = 'Aula'
    expected_rooms = [
        {'id': 1, 'name': 'Aula 101', 'capacity': 30},
        {'id': 2, 'name': 'Aula 201', 'capacity': 25},
        {'id': 3, 'name': 'Aula Magna', 'capacity': 200}
    ]
    mock_cursor.fetchall.return_value = expected_rooms

    result = room_service.search(query)

    expected_sql = "SELECT * FROM Rooms WHERE name LIKE %s ORDER BY name"
    mock_cursor.execute.assert_called_once_with(expected_sql, ("%Aula%",))
    assert result == expected_rooms


def test_search_rooms_returns_empty_when_no_matches(room_service, mock_db):
    """Test searching for rooms when no matches are found."""
    _, mock_cursor = mock_db
    query = 'Nonexistent'
    mock_cursor.fetchall.return_value = []

    result = room_service.search(query)

    expected_sql = "SELECT * FROM Rooms WHERE name LIKE %s ORDER BY name"
    mock_cursor.execute.assert_called_once_with(expected_sql, ("%Nonexistent%",))
    assert result == []


def test_search_rooms_handles_empty_query(room_service, mock_db):
    """Test searching with empty query string."""
    _, mock_cursor = mock_db
    query = ''
    expected_rooms = [
        {'id': 1, 'name': 'Aula 101', 'capacity': 30},
        {'id': 2, 'name': 'Laboratorio A', 'capacity': 25}
    ]
    mock_cursor.fetchall.return_value = expected_rooms

    result = room_service.search(query)

    expected_sql = "SELECT * FROM Rooms WHERE name LIKE %s ORDER BY name"
    mock_cursor.execute.assert_called_once_with(expected_sql, ("%%",))
    assert result == expected_rooms


def test_get_by_capacity_returns_rooms_with_sufficient_capacity(room_service, mock_db):
    """Test getting rooms with capacity greater than or equal to minimum."""
    _, mock_cursor = mock_db
    min_capacity = 25
    expected_rooms = [
        {'id': 2, 'name': 'Aula 201', 'capacity': 25},
        {'id': 1, 'name': 'Aula 101', 'capacity': 30},
        {'id': 3, 'name': 'Sala Magna', 'capacity': 200}
    ]
    mock_cursor.fetchall.return_value = expected_rooms

    result = room_service.get_by_capacity(min_capacity)

    expected_query = "SELECT * FROM Rooms WHERE capacity >= %s ORDER BY capacity"
    mock_cursor.execute.assert_called_once_with(expected_query, (min_capacity,))
    assert result == expected_rooms


def test_get_by_capacity_returns_empty_when_no_rooms_meet_criteria(room_service, mock_db):
    """Test getting rooms by capacity when none meet the minimum requirement."""
    _, mock_cursor = mock_db
    min_capacity = 500
    mock_cursor.fetchall.return_value = []

    result = room_service.get_by_capacity(min_capacity)

    assert result == []


def test_get_by_capacity_with_zero_minimum(room_service, mock_db):
    """Test getting rooms with zero minimum capacity (should return all rooms)."""
    _, mock_cursor = mock_db
    min_capacity = 0
    expected_rooms = [
        {'id': 1, 'name': 'Small Room', 'capacity': 5},
        {'id': 2, 'name': 'Medium Room', 'capacity': 25},
        {'id': 3, 'name': 'Large Room', 'capacity': 100}
    ]
    mock_cursor.fetchall.return_value = expected_rooms

    result = room_service.get_by_capacity(min_capacity)

    expected_query = "SELECT * FROM Rooms WHERE capacity >= %s ORDER BY capacity"
    mock_cursor.execute.assert_called_once_with(expected_query, (0,))
    assert result == expected_rooms


def test_get_available_rooms_returns_all_rooms(room_service, mock_db):
    """Test getting available rooms (currently returns all rooms)."""
    _, mock_cursor = mock_db
    time_slot = '09:00'
    day = 'Monday'
    period = '2025-1'
    expected_rooms = [
        {'id': 1, 'name': 'Aula 101', 'capacity': 30},
        {'id': 2, 'name': 'Aula 201', 'capacity': 25}
    ]
    mock_cursor.fetchall.return_value = expected_rooms

    result = room_service.get_available_rooms(time_slot, day, period)

    mock_cursor.execute.assert_called_once_with("SELECT * FROM Rooms ORDER BY name")
    assert result == expected_rooms


def test_get_available_rooms_ignores_parameters(room_service, mock_db):
    """Test that get_available_rooms ignores the provided parameters."""
    _, mock_cursor = mock_db
    expected_rooms = [{'id': 1, 'name': 'Test Room', 'capacity': 20}]
    mock_cursor.fetchall.return_value = expected_rooms

    result1 = room_service.get_available_rooms('10:00', 'Tuesday', '2025-1')
    result2 = room_service.get_available_rooms('14:00', 'Friday', '2024-2')
    result3 = room_service.get_available_rooms(None, None, None)

    assert result1 == expected_rooms
    assert result2 == expected_rooms
    assert result3 == expected_rooms


@pytest.mark.parametrize("name,capacity", [
    ('Aula 101', 30),
    ('Laboratorio A', 25),
    ('Sala Magna', 200),
    ('Auditorio', 500),
])
def test_create_room_with_various_parameters(room_service, mock_db, name, capacity):
    """Test room creation with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1

    result = room_service.create(name, capacity)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (name, capacity)
    mock_db_instance.commit.assert_called_once()
    assert result == 1


@pytest.mark.parametrize("room_id,name,capacity", [
    (1, 'Updated Aula', 35),
    (5, 'New Lab', 20),
    (10, 'Renovated Hall', 150),
])
def test_update_room_with_various_parameters(room_service, mock_db, 
                                           room_id, name, capacity):
    """Test room update with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db

    room_service.update(room_id, name, capacity)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (name, capacity, room_id)
    mock_db_instance.commit.assert_called_once()


@pytest.mark.parametrize("search_query,expected_pattern", [
    ('Aula', '%Aula%'),
    ('Lab', '%Lab%'),
    ('101', '%101%'),
    ('Magna', '%Magna%'),
])
def test_search_with_various_queries(room_service, mock_db, search_query, expected_pattern):
    """Test room search with various query patterns."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    room_service.search(search_query)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (expected_pattern,)


@pytest.mark.parametrize("min_capacity", [
    1, 10, 25, 50, 100, 200
])
def test_get_by_capacity_with_various_minimums(room_service, mock_db, min_capacity):
    """Test getting rooms by capacity with various minimum values."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []

    room_service.get_by_capacity(min_capacity)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (min_capacity,)


def test_create_room_with_special_characters_in_name(room_service, mock_db):
    """Test creating room with special characters in name."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.lastrowid = 1
    name = "Aula José María - Lab #1"
    capacity = 25

    result = room_service.create(name, capacity)

    args = mock_cursor.execute.call_args[0][1]
    assert args[0] == name
    assert args[1] == capacity


def test_search_with_special_characters(room_service, mock_db):
    """Test searching with special characters in query."""
    _, mock_cursor = mock_db
    mock_cursor.fetchall.return_value = []
    query = "José María"

    room_service.search(query)

    expected_pattern = "%José María%"
    args = mock_cursor.execute.call_args[0][1]
    assert args == (expected_pattern,)


def test_database_error_handling_on_create(room_service, mock_db):
    """Test that database errors during create are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        room_service.create("Test Room", 25)


def test_database_error_handling_on_update(room_service, mock_db):
    """Test that database errors during update are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        room_service.update(1, "Test Room", 25)


def test_database_error_handling_on_delete(room_service, mock_db):
    """Test that database errors during delete are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        room_service.delete(1)


def test_database_error_handling_on_get_all(room_service, mock_db):
    """Test that database errors during get_all are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        room_service.get_all()


def test_database_error_handling_on_search(room_service, mock_db):
    """Test that database errors during search are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        room_service.search("test")


def test_database_error_handling_on_get_by_capacity(room_service, mock_db):
    """Test that database errors during get_by_capacity are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        room_service.get_by_capacity(25)


def test_database_error_handling_on_get_available_rooms(room_service, mock_db):
    """Test that database errors during get_available_rooms are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        room_service.get_available_rooms("10:00", "Monday", "2025-1")


def test_room_operations_sequence(room_service, mock_db):
    """Test sequence of room operations to ensure they work together."""
    mock_db_instance, mock_cursor = mock_db
    
    mock_cursor.lastrowid = 1
    room_id = room_service.create("Test Room", 30)

    mock_cursor.reset_mock()
    mock_db_instance.reset_mock()
    
    room_service.update(room_id, "Updated Room", 35)
    
    mock_cursor.reset_mock()
    mock_db_instance.reset_mock()
    
    room_service.delete(room_id)
    
    expected_query = "DELETE FROM Rooms WHERE id = %s"
    mock_cursor.execute.assert_called_with(expected_query, (room_id,))


def test_search_ordering_is_by_name(room_service, mock_db):
    """Test that search results are ordered by name."""
    _, mock_cursor = mock_db
    
    room_service.search("test")
    
    query = mock_cursor.execute.call_args[0][0]
    assert "ORDER BY name" in query


def test_get_by_capacity_ordering_is_by_capacity(room_service, mock_db):
    """Test that capacity search results are ordered by capacity."""
    _, mock_cursor = mock_db
    
    room_service.get_by_capacity(25)
    
    query = mock_cursor.execute.call_args[0][0]
    assert "ORDER BY capacity" in query


def test_get_all_ordering_is_by_name(room_service, mock_db):
    """Test that get_all results are ordered by name."""
    _, mock_cursor = mock_db
    
    room_service.get_all()
    
    query = mock_cursor.execute.call_args[0][0]
    assert "ORDER BY name" in query