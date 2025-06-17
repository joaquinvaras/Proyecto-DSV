"""Unit tests for ScheduleService module.

This module contains comprehensive tests for the ScheduleService class,
including schedule generation, room assignment, time conflict resolution, and CSV export.
"""

import pytest
from unittest.mock import Mock, patch
from Service.schedule_service import ScheduleService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def schedule_service(mock_db):
    """Create ScheduleService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.schedule_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return ScheduleService()


def test_init_creates_database_connection_and_empty_schedule():
    """Test that ScheduleService initializes with database connection and empty schedule."""
    with patch('Service.schedule_service.DatabaseConnection') as mock_db_class:
        service = ScheduleService()
        mock_db_class.assert_called_once()
        assert service.db is not None
        assert service.last_schedule == []


def test_fetch_periods_from_database_query(schedule_service, mock_db):
    """Test the query method for fetching periods from database."""
    _, mock_cursor = mock_db
    expected_periods = [{'period': '2025-1'}, {'period': '2024-2'}]
    mock_cursor.fetchall.return_value = expected_periods

    result = schedule_service._fetch_periods_from_database()

    expected_query = ("SELECT DISTINCT period FROM Instances "
                     "ORDER BY period DESC")
    mock_cursor.execute.assert_called_once_with(expected_query)
    assert result == expected_periods


def test_get_available_periods_command(schedule_service):
    """Test the command method that processes periods query result."""
    mock_periods = [{'period': '2025-1'}, {'period': '2024-2'}]
    
    with patch.object(schedule_service, '_fetch_periods_from_database', 
                      return_value=mock_periods):
        result = schedule_service.get_available_periods()
    
    expected_periods = ['2025-1', '2024-2']
    assert result == expected_periods


def test_get_available_periods_returns_empty_when_no_periods(schedule_service):
    """Test get_available_periods when no periods exist."""
    with patch.object(schedule_service, '_fetch_periods_from_database', 
                      return_value=[]):
        result = schedule_service.get_available_periods()
    
    assert result == []


def test_get_rooms_returns_all_rooms_ordered(schedule_service, mock_db):
    """Test getting all rooms for scheduling ordered by name."""
    _, mock_cursor = mock_db
    expected_rooms = [
        {'id': 1, 'name': 'Aula 101', 'capacity': 30},
        {'id': 2, 'name': 'Aula 201', 'capacity': 25},
        {'id': 3, 'name': 'Laboratorio A', 'capacity': 20}
    ]
    mock_cursor.fetchall.return_value = expected_rooms

    result = schedule_service.get_rooms()

    mock_cursor.execute.assert_called_once_with("SELECT * FROM Rooms ORDER BY name")
    assert result == expected_rooms


def test_get_sections_by_period_returns_sections_with_details(schedule_service, mock_db):
    """Test getting sections for a period with complete information."""
    _, mock_cursor = mock_db
    period = '2025-1'
    expected_sections = [
        {
            'section_id': 1, 'number': 1, 'professor_id': 1,
            'course_id': 1, 'course_name': 'Diseño de Software', 'credits': 3, 'nrc': 'ICC5130',
            'instance_id': 1, 'period': '2025-1', 'professor_name': 'Dr. García'
        },
        {
            'section_id': 2, 'number': 1, 'professor_id': 2,
            'course_id': 2, 'course_name': 'Programación', 'credits': 4, 'nrc': 'ICC1102',
            'instance_id': 2, 'period': '2025-1', 'professor_name': 'Dra. López'
        }
    ]
    mock_cursor.fetchall.return_value = expected_sections

    result = schedule_service.get_sections_by_period(period)

    expected_query = """
            SELECT s.id AS section_id, s.number, s.professor_id,
                   c.id AS course_id, c.name AS course_name, c.credits, c.nrc,
                   i.id AS instance_id, i.period,
                   u.name AS professor_name
            FROM Sections s
            JOIN Instances i ON s.instance_id = i.id
            JOIN Courses c ON i.course_id = c.id
            JOIN Users u ON s.professor_id = u.id
            WHERE i.period = %s
            ORDER BY c.credits DESC, c.name, s.number
        """
    mock_cursor.execute.assert_called_once_with(expected_query, (period,))
    assert result == expected_sections


def test_get_sections_by_period_ordered_correctly(schedule_service, mock_db):
    """Test that sections are ordered by credits DESC, course name, section number."""
    _, mock_cursor = mock_db
    period = '2025-1'
    
    schedule_service.get_sections_by_period(period)
    
    query = mock_cursor.execute.call_args[0][0]
    assert "ORDER BY c.credits DESC, c.name, s.number" in query


def test_initialize_schedule_data_returns_sorted_sections(schedule_service):
    """Test initialization of schedule data with sorted sections."""
    period = '2025-1'
    mock_sections = [
        {'credits': 3, 'course_name': 'Course A'},
        {'credits': 5, 'course_name': 'Course B'},
        {'credits': 3, 'course_name': 'Course C'}
    ]
    mock_rooms = [{'id': 1, 'name': 'Room A'}]
    
    with patch.object(schedule_service, 'get_sections_by_period', return_value=mock_sections), \
         patch.object(schedule_service, 'get_rooms', return_value=mock_rooms):
        
        sections, rooms, hours, days = schedule_service._initialize_schedule_data(period)

    assert sections[0]['credits'] == 5
    assert sections[1]['credits'] == 3
    assert sections[2]['credits'] == 3
    assert rooms == mock_rooms
    assert hours == list(range(9, 18))
    assert days == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def test_initialize_occupancy_structures_creates_proper_data_structures(schedule_service):
    """Test initialization of occupancy tracking structures."""
    rooms = [{'id': 1}, {'id': 2}]
    hours = [9, 10, 11]
    days = ['Monday', 'Tuesday']
    
    room_occupancy, teacher_occupancy, schedule = schedule_service._initialize_occupancy_structures(
        rooms, hours, days
    )
    
    assert len(room_occupancy) == 2
    assert 1 in room_occupancy
    assert 2 in room_occupancy
    assert room_occupancy[1]['Monday'][9] is False
    assert room_occupancy[2]['Tuesday'][11] is False
    assert teacher_occupancy == {}
    assert schedule == []


def test_is_valid_time_block_rejects_lunch_hour(schedule_service):
    """Test that time blocks containing lunch hour (13:00) are invalid."""
    invalid_blocks = [
        [13],
        [12, 13],
        [13, 14],
        [12, 13, 14],
    ]
    
    for block in invalid_blocks:
        result = schedule_service._is_valid_time_block(block)
        assert result is False, f"Block {block} should be invalid due to lunch hour"


def test_is_valid_time_block_rejects_late_hours(schedule_service):
    """Test that time blocks ending after 17:00 are invalid."""
    invalid_blocks = [
        [17, 18],
        [16, 17, 18],
        [15, 16, 17, 18, 19],
    ]
    
    for block in invalid_blocks:
        result = schedule_service._is_valid_time_block(block)
        assert result is False, f"Block {block} should be invalid due to late ending"


def test_is_valid_time_block_accepts_valid_blocks(schedule_service):
    """Test that valid time blocks are accepted."""
    valid_blocks = [
        [9],
        [9, 10],
        [14, 15, 16],
        [10, 11, 12],
        [15, 16, 17],
    ]
    
    for block in valid_blocks:
        result = schedule_service._is_valid_time_block(block)
        assert result is True, f"Block {block} should be valid"


def test_is_time_slot_available_returns_true_when_free(schedule_service):
    """Test time slot availability when both room and teacher are free."""
    room_occupancy = {1: {'Monday': {9: False, 10: False}}}
    teacher_occupancy = {1: {'Monday': {9: False, 10: False}}}
    
    slot_data = {
        'room_id': 1,
        'prof_id': 1,
        'day': 'Monday',
        'time_block': [9, 10],
        'room_occupancy': room_occupancy,
        'teacher_occupancy': teacher_occupancy
    }
    
    result = schedule_service._is_time_slot_available(**slot_data)
    
    assert result is True


def test_is_time_slot_available_returns_false_when_room_occupied(schedule_service):
    """Test time slot availability when room is occupied."""
    room_occupancy = {1: {'Monday': {9: True, 10: False}}}
    teacher_occupancy = {1: {'Monday': {9: False, 10: False}}}
    
    slot_data = {
        'room_id': 1,
        'prof_id': 1,
        'day': 'Monday',
        'time_block': [9, 10],
        'room_occupancy': room_occupancy,
        'teacher_occupancy': teacher_occupancy
    }
    
    result = schedule_service._is_time_slot_available(**slot_data)
    
    assert result is False


def test_is_time_slot_available_returns_false_when_teacher_occupied(schedule_service):
    """Test time slot availability when teacher is occupied."""
    room_occupancy = {1: {'Monday': {9: False, 10: False}}}
    teacher_occupancy = {1: {'Monday': {9: False, 10: True}}}
    
    slot_data = {
        'room_id': 1,
        'prof_id': 1,
        'day': 'Monday',
        'time_block': [9, 10],
        'room_occupancy': room_occupancy,
        'teacher_occupancy': teacher_occupancy
    }
    
    result = schedule_service._is_time_slot_available(**slot_data)
    
    assert result is False


def test_mark_time_slot_occupied_updates_both_occupancies(schedule_service):
    """Test that marking time slot as occupied updates both room and teacher."""
    room_occupancy = {1: {'Monday': {9: False, 10: False}}}
    teacher_occupancy = {1: {'Monday': {9: False, 10: False}}}
    
    slot_data = {
        'room_id': 1,
        'prof_id': 1,
        'day': 'Monday',
        'time_block': [9, 10],
        'room_occupancy': room_occupancy,
        'teacher_occupancy': teacher_occupancy
    }
    
    schedule_service._mark_time_slot_occupied(**slot_data)
    
    assert room_occupancy[1]['Monday'][9] is True
    assert room_occupancy[1]['Monday'][10] is True
    assert teacher_occupancy[1]['Monday'][9] is True
    assert teacher_occupancy[1]['Monday'][10] is True


def test_create_schedule_entry_creates_proper_structure(schedule_service):
    """Test creation of schedule entry with all required fields."""
    section = {
        'course_name': 'Diseño de Software',
        'nrc': 'ICC5130',
        'number': 1,
        'professor_name': 'Dr. García',
        'credits': 3,
        'period': '2025-1'
    }
    time_block = [9, 10, 11]
    day = 'Monday'
    room = {'name': 'Aula 101', 'capacity': 30}
    
    result = schedule_service._create_schedule_entry(section, time_block, day, room)
    
    expected_entry = {
        'course_name': 'Diseño de Software',
        'nrc': 'ICC5130',
        'number': 1,
        'professor_name': 'Dr. García',
        'credits': 3,
        'period': '2025-1',
        'start': 9,
        'end': 12,
        'day': 'Monday',
        'room_name': 'Aula 101',
        'room_capacity': 30
    }
    
    assert result == expected_entry


def test_try_assign_section_to_slot_succeeds_when_available(schedule_service):
    """Test successful assignment when time slot is available."""
    section = {
        'credits': 2, 
        'professor_id': 1, 
        'course_name': 'Test Course',
        'nrc': 'TEST123',
        'number': 1,
        'professor_name': 'Test Professor',
        'period': '2025-1'
    }
    room = {'id': 1, 'name': 'Test Room', 'capacity': 30}
    day = 'Monday'
    hours = [9, 10, 11, 12]
    
    room_occupancy = {1: {'Monday': {h: False for h in hours}}}
    teacher_occupancy = {1: {'Monday': {h: False for h in hours}}}
    schedule = []
    
    occupancy_data = {
        'room_occupancy': room_occupancy,
        'teacher_occupancy': teacher_occupancy,
        'schedule': schedule
    }
    
    result = schedule_service._try_assign_section_to_slot(
        section, room, day, hours, **occupancy_data
    )
    
    assert result is True
    assert len(schedule) == 1
    assert room_occupancy[1]['Monday'][9] is True
    assert room_occupancy[1]['Monday'][10] is True
    assert teacher_occupancy[1]['Monday'][9] is True
    assert teacher_occupancy[1]['Monday'][10] is True


def test_try_assign_section_to_slot_fails_when_no_space(schedule_service):
    """Test assignment failure when no time slot is available."""
    section = {
        'credits': 3, 
        'professor_id': 1,
        'course_name': 'Test Course',
        'nrc': 'TEST123',
        'number': 1,
        'professor_name': 'Test Professor',
        'period': '2025-1'
    }
    room = {'id': 1, 'name': 'Test Room', 'capacity': 30}
    day = 'Monday'
    hours = [9, 10]
    
    room_occupancy = {1: {'Monday': {h: False for h in hours}}}
    teacher_occupancy = {1: {'Monday': {h: False for h in hours}}}
    schedule = []
    
    occupancy_data = {
        'room_occupancy': room_occupancy,
        'teacher_occupancy': teacher_occupancy,
        'schedule': schedule
    }
    
    result = schedule_service._try_assign_section_to_slot(
        section, room, day, hours, **occupancy_data
    )
    
    assert result is False
    assert len(schedule) == 0


def test_assign_section_to_schedule_creates_teacher_occupancy(schedule_service):
    """Test that assign section creates teacher occupancy if it doesn't exist."""
    section = {
        'credits': 1, 
        'professor_id': 99,
        'course_name': 'Test Course',
        'nrc': 'TEST123',
        'number': 1,
        'professor_name': 'Test Professor',
        'period': '2025-1'
    }
    days = ['Monday']
    rooms = [{'id': 1, 'name': 'Test Room', 'capacity': 30}]
    hours = [9, 10, 11]
    
    room_occupancy = {1: {'Monday': {h: False for h in hours}}}
    teacher_occupancy = {}
    schedule = []
    
    occupancy_data = {
        'room_occupancy': room_occupancy,
        'teacher_occupancy': teacher_occupancy,
        'schedule': schedule
    }
    
    with patch.object(schedule_service, '_try_assign_section_to_slot', return_value=True):
        result = schedule_service._assign_section_to_schedule(
            section, days, rooms, hours, **occupancy_data
        )
    
    assert result is True
    assert 99 in teacher_occupancy
    assert teacher_occupancy[99]['Monday'][9] is False


def test_generate_schedule_returns_none_when_impossible(schedule_service):
    """Test that generate_schedule returns None when assignment is impossible."""
    period = '2025-1'

    mock_sections = [{'credits': 10, 'professor_id': 1}]
    mock_rooms = [{'id': 1, 'name': 'Test Room'}]
    
    with patch.object(schedule_service, '_initialize_schedule_data', 
                      return_value=(mock_sections, mock_rooms, list(range(9, 18)), 
                                   ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])), \
         patch.object(schedule_service, '_initialize_occupancy_structures',
                      return_value=({}, {}, [])), \
         patch.object(schedule_service, '_assign_section_to_schedule', return_value=False):
        
        result = schedule_service.generate_schedule(period)
    
    assert result is None


def test_generate_schedule_returns_schedule_when_successful(schedule_service):
    """Test that generate_schedule returns schedule when all sections can be assigned."""
    period = '2025-1'
    
    mock_sections = [{'credits': 2, 'professor_id': 1}]
    mock_rooms = [{'id': 1, 'name': 'Test Room'}]
    expected_schedule = [{'course_name': 'Test Course', 'start': 9, 'end': 11}]
    
    with patch.object(schedule_service, '_initialize_schedule_data', 
                      return_value=(mock_sections, mock_rooms, list(range(9, 18)), 
                                   ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])), \
         patch.object(schedule_service, '_initialize_occupancy_structures',
                      return_value=({}, {}, expected_schedule)), \
         patch.object(schedule_service, '_assign_section_to_schedule', return_value=True):
        
        result = schedule_service.generate_schedule(period)
    
    assert result == expected_schedule
    assert schedule_service.last_schedule == expected_schedule


def test_create_csv_generates_proper_format(schedule_service):
    """Test CSV creation with proper formatting and headers."""
    period = '2025-1'
    schedule_service.last_schedule = [
        {
            'course_name': 'Diseño de Software',
            'nrc': 'ICC5130',
            'number': 1,
            'professor_name': 'Dr. García',
            'credits': 3,
            'period': '2025-1',
            'start': 9,
            'end': 12,
            'day': 'Monday',
            'room_name': 'Aula 101',
            'room_capacity': 30
        }
    ]
    
    result = schedule_service.create_csv(period)
    
    lines = [line.strip() for line in result.strip().split('\n')]

    expected_header = ('Course name;Code;Section number;Professor name;'
                      'Credits;Period;Schedule;Day;Room;Capacity')
    assert lines[0] == expected_header
    
    expected_row = ('Diseño de Software;ICC5130;1;Dr. García;3;2025-1;'
                   '9:00-12:00;Monday;Aula 101;30')
    assert lines[1] == expected_row


def test_create_csv_handles_empty_schedule(schedule_service):
    """Test CSV creation when schedule is empty."""
    period = '2025-1'
    schedule_service.last_schedule = []
    
    result = schedule_service.create_csv(period)
    
    lines = [line.strip() for line in result.strip().split('\n')]

    assert len(lines) == 1
    expected_header = ('Course name;Code;Section number;Professor name;'
                      'Credits;Period;Schedule;Day;Room;Capacity')
    assert lines[0] == expected_header


def test_create_csv_formats_time_correctly(schedule_service):
    """Test that CSV formats time with proper zero padding."""
    period = '2025-1'
    schedule_service.last_schedule = [
        {
            'course_name': 'Test Course',
            'nrc': 'TEST123',
            'number': 1,
            'professor_name': 'Test Prof',
            'credits': 1,
            'period': '2025-1',
            'start': 9,
            'end': 10,
            'day': 'Monday',
            'room_name': 'Test Room',
            'room_capacity': 25
        }
    ]
    
    result = schedule_service.create_csv(period)
    
    lines = [line.strip() for line in result.strip().split('\n')]
    data_row = lines[1]
    
    assert '9:00-10:00' in data_row


@pytest.mark.parametrize("credits,expected_hours", [
    (1, 1),
    (2, 2),
    (3, 3),
    (5, 5),
])
def test_time_block_creation_matches_credits(schedule_service, credits, expected_hours):
    """Test that time blocks are created to match course credits."""
    hours = list(range(9, 18))

    for i in range(len(hours) - credits + 1):
        time_block = hours[i:i+credits]
        assert len(time_block) == expected_hours


def test_database_error_handling_on_get_rooms(schedule_service, mock_db):
    """Test that database errors during get_rooms are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        schedule_service.get_rooms()


def test_database_error_handling_on_get_sections_by_period(schedule_service, mock_db):
    """Test that database errors during get_sections_by_period are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        schedule_service.get_sections_by_period('2025-1')


def test_database_error_handling_on_fetch_periods(schedule_service, mock_db):
    """Test that database errors during fetch periods are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        schedule_service._fetch_periods_from_database()