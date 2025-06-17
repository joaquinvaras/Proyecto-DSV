"""Unit tests for GradeService module.

This module contains comprehensive tests for the GradeService class,
including CRUD operations, grade calculations, and final grade computation.
"""

import pytest
from unittest.mock import Mock, patch
from Service.grade_service import GradeService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    mock_db = Mock()
    mock_cursor = Mock()
    mock_db.connect.return_value = mock_cursor
    return mock_db, mock_cursor


@pytest.fixture
def grade_service(mock_db):
    """Create GradeService instance with mocked database."""
    mock_db_instance, _ = mock_db
    with patch('Service.grade_service.DatabaseConnection') as mock_db_class:
        mock_db_class.return_value = mock_db_instance
        return GradeService()


def test_init_creates_database_connection():
    """Test that GradeService initializes with database connection."""
    with patch('Service.grade_service.DatabaseConnection') as mock_db_class:
        service = GradeService()
        mock_db_class.assert_called_once()
        assert service.db is not None


def test_get_all_returns_all_grades(grade_service, mock_db):
    """Test getting all grades from database."""
    _, mock_cursor = mock_db
    expected_grades = [
        {'id': 1, 'grade': 5.5, 'user_id': 1, 'activity_id': 1},
        {'id': 2, 'grade': 6.0, 'user_id': 2, 'activity_id': 1}
    ]
    mock_cursor.fetchall.return_value = expected_grades

    result = grade_service.get_all()

    mock_cursor.execute.assert_called_once_with("SELECT * FROM Grades")
    assert result == expected_grades


def test_get_by_id_returns_specific_grade(grade_service, mock_db):
    """Test getting a specific grade by ID."""
    _, mock_cursor = mock_db
    grade_id = 1
    expected_grade = {'id': 1, 'grade': 5.5, 'user_id': 1, 'activity_id': 1}
    mock_cursor.fetchone.return_value = expected_grade

    result = grade_service.get_by_id(grade_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Grades WHERE id = %s", (grade_id,)
    )
    assert result == expected_grade


def test_get_by_id_returns_none_when_not_found(grade_service, mock_db):
    """Test getting grade by ID when grade doesn't exist."""
    _, mock_cursor = mock_db
    grade_id = 999
    mock_cursor.fetchone.return_value = None

    result = grade_service.get_by_id(grade_id)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM Grades WHERE id = %s", (grade_id,)
    )
    assert result is None


def test_get_by_activity_and_student_returns_grade(grade_service, mock_db):
    """Test getting grade for specific activity and student."""
    _, mock_cursor = mock_db
    activity_id = 1
    user_id = 1
    expected_grade = {'id': 1, 'grade': 5.5, 'user_id': 1, 'activity_id': 1}
    mock_cursor.fetchone.return_value = expected_grade

    result = grade_service.get_by_activity_and_student(activity_id, user_id)

    expected_query = (
        "SELECT * FROM Grades WHERE activity_id = %s AND user_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (activity_id, user_id)
    )
    assert result == expected_grade


def test_get_by_activity_and_student_returns_none_when_not_found(grade_service, mock_db):
    """Test getting grade when combination doesn't exist."""
    _, mock_cursor = mock_db
    activity_id = 999
    user_id = 999
    mock_cursor.fetchone.return_value = None

    result = grade_service.get_by_activity_and_student(activity_id, user_id)

    assert result is None


def test_get_by_student_returns_grades_with_context(grade_service, mock_db):
    """Test getting all grades for a student with context information."""
    _, mock_cursor = mock_db
    user_id = 1
    expected_grades = [
        {
            'id': 1, 'grade': 5.5, 'instance': 1, 'topic_name': 'Controles',
            'section_id': 1, 'period': '2025-1'
        },
        {
            'id': 2, 'grade': 6.0, 'instance': 2, 'topic_name': 'Tareas',
            'section_id': 1, 'period': '2025-1'
        }
    ]
    mock_cursor.fetchall.return_value = expected_grades

    result = grade_service.get_by_student(user_id)

    expected_query = (
        "SELECT g.*, a.instance, t.name as topic_name, "
        "s.id as section_id, i.period "
        "FROM Grades g "
        "JOIN Activities a ON g.activity_id = a.id "
        "JOIN Topics t ON a.topic_id = t.id "
        "JOIN Sections s ON t.section_id = s.id "
        "JOIN Instances i ON s.instance_id = i.id "
        "WHERE g.user_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (user_id,))
    assert result == expected_grades


def test_get_by_section_returns_grades_with_context(grade_service, mock_db):
    """Test getting all grades for a section with context information."""
    _, mock_cursor = mock_db
    section_id = 1
    expected_grades = [
        {
            'id': 1, 'grade': 5.5, 'instance': 1, 'topic_name': 'Controles',
            'user_name': 'Juan Pérez'
        },
        {
            'id': 2, 'grade': 6.0, 'instance': 2, 'topic_name': 'Tareas',
            'user_name': 'María García'
        }
    ]
    mock_cursor.fetchall.return_value = expected_grades

    result = grade_service.get_by_section(section_id)

    expected_query = (
        "SELECT g.*, a.instance, t.name as topic_name, "
        "u.name as user_name "
        "FROM Grades g "
        "JOIN Activities a ON g.activity_id = a.id "
        "JOIN Topics t ON a.topic_id = t.id "
        "JOIN Users u ON g.user_id = u.id "
        "WHERE t.section_id = %s"
    )
    mock_cursor.execute.assert_called_once_with(expected_query, (section_id,))
    assert result == expected_grades


def test_create_grade_success(grade_service, mock_db):
    """Test successful creation of a new grade."""
    mock_db_instance, mock_cursor = mock_db
    grade = 5.5
    user_id = 1
    activity_id = 1

    grade_service.create(grade, user_id, activity_id)

    expected_query = (
        "INSERT INTO Grades (grade, user_id, activity_id) "
        "VALUES (%s, %s, %s)"
    )
    mock_cursor.execute.assert_called_once_with(
        expected_query, (grade, user_id, activity_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_update_grade_success(grade_service, mock_db):
    """Test successful update of an existing grade."""
    mock_db_instance, mock_cursor = mock_db
    grade_id = 1
    new_grade = 6.0

    grade_service.update(grade_id, new_grade)

    expected_query = "UPDATE Grades SET grade = %s WHERE id = %s"
    mock_cursor.execute.assert_called_once_with(
        expected_query, (new_grade, grade_id)
    )
    mock_db_instance.commit.assert_called_once()


def test_delete_grade_success(grade_service, mock_db):
    """Test successful deletion of a grade."""
    mock_db_instance, mock_cursor = mock_db
    grade_id = 1

    grade_service.delete(grade_id)

    expected_query = "DELETE FROM Grades WHERE id = %s"
    mock_cursor.execute.assert_called_once_with(expected_query, (grade_id,))
    mock_db_instance.commit.assert_called_once()


def test_fetch_grade_calculation_data_returns_structured_data(grade_service, mock_db):
    """Test fetching grade calculation data with proper structure."""
    _, mock_cursor = mock_db
    user_id = 1
    section_id = 1
    
    topics = [{'id': 1, 'name': 'Controles', 'weight': 500, 'weight_or_percentage': True}]
    activities = [{'id': 1, 'instance': 1, 'weight': 300, 'optional_flag': False}]
    grade_result = {'grade': 5.5}
    
    mock_cursor.fetchall.side_effect = [topics, activities]
    mock_cursor.fetchone.return_value = grade_result

    result = grade_service._fetch_grade_calculation_data(user_id, section_id)

    mock_cursor.execute.assert_any_call(
        "SELECT id, name, weight, weight_or_percentage "
        "FROM Topics WHERE section_id = %s",
        (section_id,)
    )

    assert len(result) == 1
    assert result[0]['activities'][0]['grade_result'] == grade_result


def test_calculate_activity_grade_with_percentage_system(grade_service, mock_db):
    """Test calculating activity grade contribution with percentage system."""
    activity = {
        'weight': 30,
        'optional_flag': False,
        'grade_result': {'grade': 6.0}
    }
    is_percentage = True

    contribution, weight_contribution = grade_service._calculate_activity_grade(
        activity, is_percentage
    )

    assert contribution == pytest.approx(1.8)
    assert weight_contribution == pytest.approx(0.3)


def test_calculate_activity_grade_with_weight_system(grade_service, mock_db):
    """Test calculating activity grade contribution with weight system."""
    activity = {
        'weight': 300,
        'optional_flag': False,
        'grade_result': {'grade': 5.5}
    }
    is_percentage = False

    contribution, weight_contribution = grade_service._calculate_activity_grade(
        activity, is_percentage
    )

    assert contribution == 1650
    assert weight_contribution == 300


def test_calculate_activity_grade_optional_without_grade(grade_service, mock_db):
    """Test calculating activity grade for optional activity without grade."""
    activity = {
        'weight': 300,
        'optional_flag': True,
        'grade_result': None
    }
    is_percentage = False

    contribution, weight_contribution = grade_service._calculate_activity_grade(
        activity, is_percentage
    )

    assert contribution == 0
    assert weight_contribution == 0


def test_calculate_activity_grade_mandatory_without_grade(grade_service, mock_db):
    """Test calculating activity grade for mandatory activity without grade."""
    activity = {
        'weight': 300,
        'optional_flag': False,
        'grade_result': None
    }
    is_percentage = False

    contribution, weight_contribution = grade_service._calculate_activity_grade(
        activity, is_percentage
    )

    assert contribution == 300
    assert weight_contribution == 300


def test_calculate_topic_grade_with_activities(grade_service, mock_db):
    """Test calculating final grade for a topic with activities."""
    topic = {
        'weight_or_percentage': False,
        'activities': [
            {
                'weight': 300,
                'optional_flag': False,
                'grade_result': {'grade': 6.0}
            },
            {
                'weight': 200,
                'optional_flag': False,
                'grade_result': {'grade': 5.0}
            }
        ]
    }

    result = grade_service._calculate_topic_grade(topic)

    assert result == pytest.approx(5.6)


def test_calculate_topic_grade_with_no_activities(grade_service, mock_db):
    """Test calculating topic grade when there are no activities."""
    topic = {
        'weight_or_percentage': False,
        'activities': []
    }

    result = grade_service._calculate_topic_grade(topic)

    assert result == 0


def test_calculate_topic_grade_with_only_optional_activities_no_grades(grade_service, mock_db):
    """Test calculating topic grade with only optional activities without grades."""
    topic = {
        'weight_or_percentage': False,
        'activities': [
            {
                'weight': 300,
                'optional_flag': True,
                'grade_result': None
            }
        ]
    }

    result = grade_service._calculate_topic_grade(topic)

    assert result == 0


def test_calculate_final_grade_with_multiple_topics(grade_service, mock_db):
    """Test calculating final grade with multiple topics."""
    _, mock_cursor = mock_db
    user_id = 1
    section_id = 1

    topics_data = [
        {
            'id': 1, 'name': 'Controles', 'weight': 600, 'weight_or_percentage': False,
            'activities': [
                {
                    'weight': 300,
                    'optional_flag': False,
                    'grade_result': {'grade': 6.0}
                }
            ]
        },
        {
            'id': 2, 'name': 'Tareas', 'weight': 400, 'weight_or_percentage': False,
            'activities': [
                {
                    'weight': 200,
                    'optional_flag': False,
                    'grade_result': {'grade': 5.0}
                }
            ]
        }
    ]
    
    with patch.object(grade_service, '_fetch_grade_calculation_data', 
                      return_value=topics_data):
        result = grade_service.calculate_final_grade(user_id, section_id)

    assert result == pytest.approx(5.6)


def test_calculate_final_grade_with_no_topics(grade_service, mock_db):
    """Test calculating final grade when there are no topics."""
    user_id = 1
    section_id = 1

    with patch.object(grade_service, '_fetch_grade_calculation_data', 
                      return_value=[]):
        result = grade_service.calculate_final_grade(user_id, section_id)

    assert result == 0


def test_calculate_final_grade_rounds_to_one_decimal(grade_service, mock_db):
    """Test that final grade is rounded to one decimal place."""
    user_id = 1
    section_id = 1
    
    topics_data = [
        {
            'id': 1, 'name': 'Test', 'weight': 300, 'weight_or_percentage': False,
            'activities': [
                {
                    'weight': 100,
                    'optional_flag': False,
                    'grade_result': {'grade': 5.567}
                }
            ]
        }
    ]
    
    with patch.object(grade_service, '_fetch_grade_calculation_data', 
                      return_value=topics_data):
        result = grade_service.calculate_final_grade(user_id, section_id)

    assert isinstance(result, float)
    assert len(str(result).split('.')[-1]) <= 1


@pytest.mark.parametrize("grade,user_id,activity_id", [
    (1.0, 1, 1),
    (4.5, 2, 3),
    (7.0, 5, 10),
])
def test_create_grade_with_various_parameters(grade_service, mock_db,
                                             grade, user_id, activity_id):
    """Test grade creation with various parameter combinations."""
    mock_db_instance, mock_cursor = mock_db

    grade_service.create(grade, user_id, activity_id)

    args = mock_cursor.execute.call_args[0][1]
    assert args == (grade, user_id, activity_id)
    mock_db_instance.commit.assert_called_once()


@pytest.mark.parametrize("grade_value", [
    1.0, 2.5, 4.0, 5.5, 7.0
])
def test_update_grade_with_various_values(grade_service, mock_db, grade_value):
    """Test updating grades with various values."""
    mock_db_instance, mock_cursor = mock_db
    grade_id = 1

    grade_service.update(grade_id, grade_value)

    args = mock_cursor.execute.call_args[0][1]
    assert args[0] == grade_value
    assert args[1] == grade_id


def test_database_error_handling_on_create(grade_service, mock_db):
    """Test that database errors during create are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        grade_service.create(5.5, 1, 1)


def test_database_error_handling_on_update(grade_service, mock_db):
    """Test that database errors during update are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        grade_service.update(1, 5.5)


def test_database_error_handling_on_delete(grade_service, mock_db):
    """Test that database errors during delete are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        grade_service.delete(1)


def test_database_error_handling_on_get_by_student(grade_service, mock_db):
    """Test that database errors during get_by_student are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        grade_service.get_by_student(1)


def test_database_error_handling_on_get_by_section(grade_service, mock_db):
    """Test that database errors during get_by_section are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        grade_service.get_by_section(1)


def test_database_error_handling_on_calculate_final_grade(grade_service, mock_db):
    """Test that database errors during calculate_final_grade are properly raised."""
    mock_db_instance, mock_cursor = mock_db
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        grade_service.calculate_final_grade(1, 1)