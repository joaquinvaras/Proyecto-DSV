"""Unit tests for Flask routes in main.py module.

This module contains comprehensive tests for Flask application routes,
including CRUD operations for courses, topics, instances, and sections.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import url_for


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    with patch('main.CourseService'), \
         patch('main.UserService'), \
         patch('main.SectionService'), \
         patch('main.CourseTakenService'), \
         patch('main.TopicService'), \
         patch('main.ActivityService'), \
         patch('main.ImportService'), \
         patch('main.InstanceService'), \
         patch('main.RoomService'), \
         patch('main.GradeService'), \
         patch('main.ScheduleService'):
        
        from main import app as flask_app
        flask_app.config['TESTING'] = True
        flask_app.config['WTF_CSRF_ENABLED'] = False
        return flask_app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    services = {
        'course_service': Mock(),
        'user_service': Mock(),
        'section_service': Mock(),
        'course_taken_service': Mock(),
        'topic_service': Mock(),
        'activity_service': Mock(),
        'import_service': Mock(),
        'instance_service': Mock(),
        'room_service': Mock(),
        'grade_service': Mock(),
        'schedule_service': Mock()
    }
    
    with patch.multiple('main', **services):
        yield services


class TestHomeRoute:
    """Test cases for home route."""
    
    @patch('main.render_template')
    def test_index_returns_home_page(self, mock_render, client):
        """Test that index route returns home page."""
        mock_render.return_value = "Home Page"
        response = client.get('/')
        assert response.status_code == 200
        mock_render.assert_called_once_with('home.html')


class TestCourseRoutes:
    """Test cases for course-related routes."""
    
    @patch('main.render_template')
    def test_list_courses_returns_courses_with_context(self, mock_render, client, mock_services):
        """Test listing courses with prerequisites and instances."""
        mock_courses = [
            {'id': 1, 'name': 'Test Course', 'nrc': 'TST001'},
            {'id': 2, 'name': 'Another Course', 'nrc': 'TST002'}
        ]
        mock_services['course_service'].get_all.return_value = mock_courses
        mock_services['course_service'].get_prerequisites.return_value = []
        mock_services['instance_service'].get_by_course_id.return_value = []
        mock_render.return_value = "Courses Page"
        
        response = client.get('/courses')
        
        assert response.status_code == 200
        mock_services['course_service'].get_all.assert_called_once()
        assert mock_services['course_service'].get_prerequisites.call_count == 2
        assert mock_services['instance_service'].get_by_course_id.call_count == 2

    @patch('main.render_template')
    def test_create_course_get_renders_form(self, mock_render, client, mock_services):
        """Test GET request to create course renders form."""
        mock_services['course_service'].get_all.return_value = []
        mock_render.return_value = "Create Course Form"
        
        response = client.get('/courses/create')
        
        assert response.status_code == 200
        mock_services['course_service'].get_all.assert_called_once()

    def test_create_course_post_creates_and_redirects(self, client, mock_services):
        """Test POST request creates course and redirects."""
        form_data = {
            'name': 'New Course',
            'nrc': 'NEW001',
            'credits': '3',
            'prerequisites': ['1', '2']
        }
        
        response = client.post('/courses/create', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['course_service'].create.assert_called_once_with(
            'New Course', 'NEW001', 3, ['1', '2']
        )

    @patch('main.render_template')
    def test_edit_course_get_with_valid_id(self, mock_render, client, mock_services):
        """Test GET request to edit course with valid ID."""
        mock_course = {'id': 1, 'name': 'Test Course', 'nrc': 'TST001'}
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['course_service'].get_all.return_value = [
            {'id': 2, 'name': 'Other Course', 'nrc': 'OTH001'}
        ]
        mock_services['course_service'].get_prerequisites.return_value = []
        mock_render.return_value = "Edit Course Form"
        
        response = client.get('/courses/edit/1')
        
        assert response.status_code == 200
        mock_services['course_service'].get_by_id.assert_called_once_with(1)

    def test_edit_course_get_with_invalid_id(self, client, mock_services):
        """Test GET request to edit course with invalid ID."""
        mock_services['course_service'].get_by_id.return_value = None
        
        response = client.get('/courses/edit/999')
        
        assert response.status_code == 404

    def test_edit_course_post_updates_and_redirects(self, client, mock_services):
        """Test POST request updates course and redirects."""
        mock_course = {'id': 1, 'name': 'Test Course', 'nrc': 'TST001'}
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['course_service'].get_all.return_value = []
        mock_services['course_service'].get_prerequisites.return_value = []
        
        form_data = {
            'name': 'Updated Course',
            'nrc': 'UPD001',
            'credits': '4',
            'prerequisites': ['2']
        }
        
        response = client.post('/courses/edit/1', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['course_service'].update.assert_called_once_with(
            1, name='Updated Course', nrc='UPD001', credits=4, prerequisites=['2']
        )

    def test_delete_course_removes_and_redirects(self, client, mock_services):
        """Test deleting a course."""
        response = client.post('/courses/delete/1', follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['course_service'].delete.assert_called_once_with(1)


class TestTopicRoutes:
    """Test cases for topic-related routes."""
    
    @patch('main.render_template')
    def test_list_topics_with_valid_section(self, mock_render, client, mock_services):
        """Test listing topics for a valid section."""
        mock_section = {'id': 1, 'instance_id': 1, 'number': 1}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_topics = [{'id': 1, 'name': 'Topic 1', 'section_id': 1}]
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = mock_topics
        mock_render.return_value = "Topics List"
        
        response = client.get('/instances/1/sections/1/topics')
        
        assert response.status_code == 200
        mock_services['topic_service'].get_by_section_id.assert_called_once_with(1)

    def test_list_topics_with_invalid_instance_id(self, client, mock_services):
        """Test listing topics with mismatched instance ID."""
        mock_section = {'id': 1, 'instance_id': 2, 'number': 1}
        mock_services['section_service'].get_by_id.return_value = mock_section
        
        response = client.get('/instances/1/sections/1/topics')
        
        assert response.status_code == 400

    @patch('main.render_template')
    def test_create_topic_get_renders_form(self, mock_render, client, mock_services):
        """Test GET request to create topic renders form."""
        mock_section = {'id': 1, 'instance_id': 1, 'weight_or_percentage': False}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = []
        mock_render.return_value = "Create Topic Form"
        
        response = client.get('/instances/1/sections/1/topics/create')
        
        assert response.status_code == 200

    def test_create_topic_post_creates_and_redirects(self, client, mock_services):
        """Test POST request creates topic and redirects."""
        mock_section = {'id': 1, 'instance_id': 1, 'weight_or_percentage': False}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = []
        
        form_data = {
            'name': 'New Topic',
            'weight': '100'
        }
        
        response = client.post('/instances/1/sections/1/topics/create', 
                             data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['topic_service'].create.assert_called_once_with(
            'New Topic', 1, 100, False
        )

    def test_create_topic_post_with_invalid_weight(self, client, mock_services):
        """Test POST request with invalid weight value."""
        mock_section = {'id': 1, 'instance_id': 1, 'weight_or_percentage': False}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        
        form_data = {
            'name': 'New Topic',
            'weight': 'invalid'
        }
        
        response = client.post('/instances/1/sections/1/topics/create', 
                             data=form_data, follow_redirects=False)
        
        assert response.status_code == 302

    @patch('main.render_template')
    def test_edit_topic_get_with_valid_id(self, mock_render, client, mock_services):
        """Test GET request to edit topic with valid ID."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1, 'weight': 100}
        mock_section = {'id': 1, 'instance_id': 1, 'weight_or_percentage': False}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = [mock_topic]
        mock_render.return_value = "Edit Topic Form"
        
        response = client.get('/topics/edit/1')
        
        assert response.status_code == 200
        mock_services['topic_service'].get_by_id.assert_called_once_with(1)

    def test_edit_topic_get_with_invalid_id(self, client, mock_services):
        """Test GET request to edit topic with invalid ID."""
        mock_services['topic_service'].get_by_id.return_value = None
        
        response = client.get('/topics/edit/999')
        
        assert response.status_code == 404

    def test_edit_topic_post_updates_and_redirects(self, client, mock_services):
        """Test POST request updates topic and redirects."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1, 'weight_or_percentage': False}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = [mock_topic]
        
        form_data = {
            'name': 'Updated Topic',
            'weight': '150'
        }
        
        response = client.post('/topics/edit/1', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['topic_service'].update.assert_called_once_with(
            1, 'Updated Topic', 150, False
        )

    def test_delete_topic_direct_removes_and_redirects(self, client, mock_services):
        """Test deleting topic directly."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1}
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        
        response = client.post('/topics/delete/1', follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['topic_service'].delete.assert_called_once_with(1)

    def test_delete_topic_direct_with_invalid_id(self, client, mock_services):
        """Test deleting topic with invalid ID."""
        mock_services['topic_service'].get_by_id.return_value = None
        
        response = client.post('/topics/delete/999')
        
        assert response.status_code == 404

    @patch('main.render_template')
    def test_delete_topic_percentage_view_get(self, mock_render, client, mock_services):
        """Test GET request for topic deletion with percentage redistribution."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_topics = [
            {'id': 1, 'name': 'Test Topic', 'weight': 500},
            {'id': 2, 'name': 'Other Topic', 'weight': 500}
        ]
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = mock_topics
        mock_render.return_value = "Delete Topic Percentage Form"
        
        response = client.get('/topics/delete/percentage/1')
        
        assert response.status_code == 200

    def test_delete_topic_percentage_view_post_success(self, client, mock_services):
        """Test POST request for topic deletion with valid percentages."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_other_topic = {'id': 2, 'name': 'Other Topic', 'weight_or_percentage': True}
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = [
            mock_topic, mock_other_topic
        ]
        
        form_data = {'percentages_2': '100'}
        
        response = client.post('/topics/delete/percentage/1', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['topic_service'].update.assert_called_once()
        mock_services['topic_service'].delete.assert_called_once_with(1)


class TestInstanceRoutes:
    """Test cases for instance-related routes."""
    
    @patch('main.render_template')
    def test_list_instances_returns_instances_with_sections(self, mock_render, client, mock_services):
        """Test listing instances with their sections."""
        mock_instances = [{'id': 1, 'course_id': 1, 'period': '2025-1'}]
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['instance_service'].get_by_course_id.return_value = mock_instances
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['section_service'].get_by_instance_id.return_value = []
        mock_render.return_value = "Instances List"
        
        response = client.get('/courses/1/instances')
        
        assert response.status_code == 200
        mock_services['instance_service'].get_by_course_id.assert_called_once_with(1)

    @patch('main.render_template')
    def test_create_instance_get_renders_form(self, mock_render, client, mock_services):
        """Test GET request to create instance renders form."""
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['instance_service'].get_by_course_id.return_value = []
        mock_render.return_value = "Create Instance Form"
        
        response = client.get('/courses/1/instances/create')
        
        assert response.status_code == 200

    def test_create_instance_get_with_invalid_course(self, client, mock_services):
        """Test GET request to create instance with invalid course."""
        mock_services['course_service'].get_by_id.return_value = None
        
        response = client.get('/courses/999/instances/create')
        
        assert response.status_code == 404

    def test_create_instance_post_creates_new_instance(self, client, mock_services):
        """Test POST request creates new instance."""
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['instance_service'].get_by_course_and_period.return_value = None
        
        form_data = {'period': '2025-2'}
        
        response = client.post('/courses/1/instances/create', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['instance_service'].create.assert_called_once_with(1, '2025-2')

    def test_create_instance_post_with_duplicate_period(self, client, mock_services):
        """Test POST request with duplicate period."""
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_existing_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['instance_service'].get_by_course_and_period.return_value = mock_existing_instance
        
        form_data = {'period': '2025-1'}
        
        response = client.post('/courses/1/instances/create', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['instance_service'].create.assert_not_called()

    @patch('main.render_template')
    def test_edit_instance_get_with_valid_id(self, mock_render, client, mock_services):
        """Test GET request to edit instance with valid ID."""
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['instance_service'].get_periods.return_value = ['2025-1', '2025-2']
        mock_render.return_value = "Edit Instance Form"
        
        response = client.get('/instances/1/edit')
        
        assert response.status_code == 200

    def test_edit_instance_get_with_invalid_id(self, client, mock_services):
        """Test GET request to edit instance with invalid ID."""
        mock_services['instance_service'].get_by_id.return_value = None
        
        response = client.get('/instances/999/edit')
        
        assert response.status_code == 404

    def test_edit_instance_post_updates_period(self, client, mock_services):
        """Test POST request updates instance period."""
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['instance_service'].get_by_course_and_period.return_value = None
        
        form_data = {'period': '2025-2'}
        
        response = client.post('/instances/1/edit', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['instance_service'].update.assert_called_once_with(1, '2025-2')

    def test_delete_instance_with_sections(self, client, mock_services):
        """Test deleting instance that has sections."""
        mock_instance = {'id': 1, 'course_id': 1}
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['instance_service'].get_section_count.return_value = 2
        
        response = client.post('/instances/1/delete', follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['instance_service'].delete.assert_not_called()

    def test_delete_instance_without_sections(self, client, mock_services):
        """Test deleting instance without sections."""
        mock_instance = {'id': 1, 'course_id': 1}
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['instance_service'].get_section_count.return_value = 0
        
        response = client.post('/instances/1/delete', follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['instance_service'].delete.assert_called_once_with(1)


class TestEnrollmentRoutes:
    """Test cases for student enrollment routes."""
    
    def test_enroll_student_in_section_success(self, client, mock_services):
        """Test successful student enrollment."""
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_taken_service'].is_student_enrolled.return_value = False
        
        form_data = {'user_id': '1'}
        
        response = client.post('/sections/1/enroll', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['course_taken_service'].enroll_student.assert_called_once_with('1', 1, 1)

    def test_enroll_student_invalid_section(self, client, mock_services):
        """Test enrolling student in non-existent section."""
        mock_services['section_service'].get_by_id.return_value = None
        
        response = client.post('/sections/999/enroll', data={'user_id': '1'})
        
        assert response.status_code == 404

    def test_enroll_student_already_enrolled(self, client, mock_services):
        """Test enrolling student already enrolled."""
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_taken_service'].is_student_enrolled.return_value = True
        
        form_data = {'user_id': '1'}
        
        response = client.post('/sections/1/enroll', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['course_taken_service'].enroll_student.assert_not_called()

    def test_unenroll_student_from_section(self, client, mock_services):
        """Test unenrolling student from section."""
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        
        response = client.post('/sections/1/unenroll/1', follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['course_taken_service'].unenroll_student.assert_called_once_with(1, 1, 1)

    @patch('main.render_template')
    def test_list_students_in_section(self, mock_render, client, mock_services):
        """Test listing students in a section."""
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_enrollments = [{'user_id': 1, 'user_name': 'Student 1'}]
        mock_students = [{'id': 1, 'name': 'Student 1'}]
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['course_taken_service'].get_students_by_section.return_value = mock_enrollments
        mock_services['user_service'].get_all.return_value = mock_students
        mock_render.return_value = "Students List"
        
        response = client.get('/sections/1/students')
        
        assert response.status_code == 200
        mock_services['course_taken_service'].get_students_by_section.assert_called_once_with(1)


class TestActivityRoutes:
    """Test cases for activity-related routes."""
    
    @patch('main.render_template')
    def test_list_activities(self, mock_render, client, mock_services):
        """Test listing activities for a topic."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_activities = [{'id': 1, 'topic_id': 1, 'instance': 1}]
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['activity_service'].get_by_topic_id.return_value = mock_activities
        mock_render.return_value = "Activities List"
        
        response = client.get('/topics/1/activities')
        
        assert response.status_code == 200
        mock_services['activity_service'].get_by_topic_id.assert_called_once_with(1)

    def test_list_activities_invalid_topic(self, client, mock_services):
        """Test listing activities for non-existent topic."""
        mock_services['topic_service'].get_by_id.return_value = None
        
        response = client.get('/topics/999/activities')
        
        assert response.status_code == 404

    @patch('main.render_template')
    def test_create_activity_get(self, mock_render, client, mock_services):
        """Test GET request for creating activity."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_activities = []
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['activity_service'].get_by_topic_id.return_value = mock_activities
        mock_render.return_value = "Create Activity Form"
        
        response = client.get('/topics/1/activities/create')
        
        assert response.status_code == 200

    def test_create_activity_post_success(self, client, mock_services):
        """Test successful activity creation."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1, 'weight_or_percentage': False}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['activity_service'].get_by_topic_id.return_value = []
        mock_services['activity_service'].get_next_instance_number.return_value = 1
        
        form_data = {'weight': '100'}
        
        response = client.post('/topics/1/activities/create', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['activity_service'].create.assert_called_once_with(1, 1, 100, False)

    def test_create_activity_invalid_weight(self, client, mock_services):
        """Test creating activity with invalid weight."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        
        form_data = {'weight': 'invalid'}
        
        response = client.post('/topics/1/activities/create', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302

    @patch('main.render_template')
    def test_edit_activity_get(self, mock_render, client, mock_services):
        """Test GET request for editing activity."""
        mock_activity = {'id': 1, 'topic_id': 1, 'instance': 1, 'weight': 100}
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['activity_service'].get_by_id.return_value = mock_activity
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['activity_service'].get_by_topic_id.return_value = [mock_activity]
        mock_render.return_value = "Edit Activity Form"
        
        response = client.get('/activities/edit/1')
        
        assert response.status_code == 200

    def test_edit_activity_invalid_id(self, client, mock_services):
        """Test editing non-existent activity."""
        mock_services['activity_service'].get_by_id.return_value = None
        
        response = client.get('/activities/edit/999')
        
        assert response.status_code == 404

    def test_delete_activity_direct(self, client, mock_services):
        """Test deleting activity directly."""
        mock_activity = {'id': 1, 'topic_id': 1}
        mock_topic = {'id': 1}
        
        mock_services['activity_service'].get_by_id.return_value = mock_activity
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        
        response = client.post('/activities/delete/1', follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['activity_service'].delete.assert_called_once_with(1)


class TestProfessorRoutes:
    """Test cases for professor-related routes."""
    
    @patch('main.render_template')
    def test_list_professors(self, mock_render, client, mock_services):
        """Test listing all professors."""
        mock_professors = [
            {'id': 1, 'name': 'Prof 1', 'email': 'prof1@test.com', 'is_professor': True},
            {'id': 2, 'name': 'Prof 2', 'email': 'prof2@test.com', 'is_professor': True}
        ]
        mock_services['user_service'].get_all.return_value = mock_professors
        mock_render.return_value = "Professors List"
        
        response = client.get('/professors')
        
        assert response.status_code == 200
        mock_services['user_service'].get_all.assert_called_once_with(is_professor=True)

    @patch('main.render_template')
    def test_create_professor_get(self, mock_render, client, mock_services):
        """Test GET request for creating professor."""
        mock_services['user_service'].get_next_import_id.return_value = 1
        mock_render.return_value = "Create Professor Form"
        
        response = client.get('/professors/create')
        
        assert response.status_code == 200
        mock_services['user_service'].get_next_import_id.assert_called_once_with(is_professor=True)

    def test_create_professor_post_success(self, client, mock_services):
        """Test successful professor creation."""
        form_data = {
            'name': 'New Professor',
            'email': 'newprof@test.com',
            'import_id': '1'
        }
        
        response = client.post('/professors/create', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['user_service'].create.assert_called_once_with(
            'New Professor', 'newprof@test.com', is_professor=True, import_id=1
        )

    @patch('main.render_template')
    def test_edit_professor_get(self, mock_render, client, mock_services):
        """Test GET request for editing professor."""
        mock_professor = {'id': 1, 'name': 'Prof 1', 'email': 'prof1@test.com', 'is_professor': True}
        mock_services['user_service'].get_by_id.return_value = mock_professor
        mock_render.return_value = "Edit Professor Form"
        
        response = client.get('/professors/edit/1')
        
        assert response.status_code == 200

    def test_edit_professor_invalid_id(self, client, mock_services):
        """Test editing non-existent professor."""
        mock_services['user_service'].get_by_id.return_value = None
        
        response = client.get('/professors/edit/999')
        
        assert response.status_code == 404

    def test_delete_professor(self, client, mock_services):
        """Test deleting professor."""
        mock_professor = {'id': 1, 'name': 'Prof 1'}
        mock_services['user_service'].get_by_id.return_value = mock_professor
        
        response = client.post('/professors/delete/1', follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['user_service'].delete.assert_called_once_with(1)


class TestStudentRoutes:
    """Test cases for student-related routes."""
    
    @patch('main.render_template')
    def test_list_students(self, mock_render, client, mock_services):
        """Test listing all students."""
        mock_students = [
            {'id': 1, 'name': 'Student 1', 'email': 'student1@test.com', 'is_professor': False},
            {'id': 2, 'name': 'Student 2', 'email': 'student2@test.com', 'is_professor': False}
        ]
        mock_services['user_service'].get_all.return_value = mock_students
        mock_render.return_value = "Students List"
        
        response = client.get('/students')
        
        assert response.status_code == 200
        mock_services['user_service'].get_all.assert_called_once_with(is_professor=False)

    @patch('main.render_template')
    def test_create_student_get(self, mock_render, client, mock_services):
        """Test GET request for creating student."""
        mock_services['user_service'].get_next_import_id.return_value = 1
        mock_render.return_value = "Create Student Form"
        
        response = client.get('/students/create')
        
        assert response.status_code == 200
        mock_services['user_service'].get_next_import_id.assert_called_once_with(is_professor=False)

    def test_create_student_post_success(self, client, mock_services):
        """Test successful student creation."""
        form_data = {
            'name': 'New Student',
            'email': 'newstudent@test.com',
            'admission_date': '2025-01-15',
            'import_id': '1'
        }
        
        response = client.post('/students/create', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['user_service'].create.assert_called_once_with(
            'New Student', 'newstudent@test.com', is_professor=False, 
            admission_date='2025-01-15', import_id=1
        )

    @patch('main.render_template')
    def test_edit_student_get(self, mock_render, client, mock_services):
        """Test GET request for editing student."""
        mock_student = {'id': 1, 'name': 'Student 1', 'email': 'student1@test.com', 'is_professor': False}
        mock_services['user_service'].get_by_id.return_value = mock_student
        mock_render.return_value = "Edit Student Form"
        
        response = client.get('/students/edit/1')
        
        assert response.status_code == 200

    def test_edit_student_invalid_id(self, client, mock_services):
        """Test editing non-existent student."""
        mock_services['user_service'].get_by_id.return_value = None
        
        response = client.get('/students/edit/999')
        
        assert response.status_code == 404

    def test_delete_student(self, client, mock_services):
        """Test deleting student."""
        mock_student = {'id': 1, 'name': 'Student 1'}
        mock_services['user_service'].get_by_id.return_value = mock_student
        
        response = client.post('/students/delete/1', follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['user_service'].delete.assert_called_once_with(1)


class TestGradeRoutes:
    """Test cases for grade-related routes."""
    
    @patch('main.render_template')
    def test_evaluate_students(self, mock_render, client, mock_services):
        """Test evaluating students for an activity."""
        mock_activity = {'id': 1, 'topic_id': 1}
        mock_topic = {'id': 1, 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_enrollments = [
            {'user_id': 1, 'user_name': 'Student 1', 'user_email': 'student1@test.com'}
        ]
        
        mock_services['activity_service'].get_by_id.return_value = mock_activity
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['course_taken_service'].get_students_by_section.return_value = mock_enrollments
        mock_services['grade_service'].get_by_activity_and_student.return_value = None
        mock_render.return_value = "Evaluate Students Form"
        
        response = client.get('/activities/1/evaluate')
        
        assert response.status_code == 200

    def test_evaluate_students_invalid_activity(self, client, mock_services):
        """Test evaluating students for non-existent activity."""
        mock_services['activity_service'].get_by_id.return_value = None
        
        response = client.get('/activities/999/evaluate')
        
        assert response.status_code == 404

    def test_save_grades_success(self, client, mock_services):
        """Test saving grades successfully."""
        mock_activity = {'id': 1, 'topic_id': 1}
        mock_topic = {'id': 1, 'section_id': 1}
        mock_section = {'id': 1}
        mock_enrollments = [
            {'user_id': 1, 'user_name': 'Student 1'}
        ]
        
        mock_services['activity_service'].get_by_id.return_value = mock_activity
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['course_taken_service'].get_students_by_section.return_value = mock_enrollments
        
        form_data = {'grade_1': '6.5'}
        
        response = client.post('/activities/1/save_grades', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['grade_service'].create.assert_called_once_with(6.5, 1, 1)

    def test_save_grades_invalid_format(self, client, mock_services):
        """Test saving grades with invalid format."""
        mock_activity = {'id': 1, 'topic_id': 1}
        mock_topic = {'id': 1, 'section_id': 1}
        mock_section = {'id': 1}
        mock_enrollments = [
            {'user_id': 1, 'user_name': 'Student 1'}
        ]
        
        mock_services['activity_service'].get_by_id.return_value = mock_activity
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['course_taken_service'].get_students_by_section.return_value = mock_enrollments
        
        form_data = {'grade_1': 'invalid_grade'}
        
        response = client.post('/activities/1/save_grades', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['grade_service'].create.assert_not_called()


class TestUploadRoutes:
    """Test cases for upload/import routes."""
    
    @patch('main.render_template')
    def test_import_data_get(self, mock_render, client):
        """Test GET request for import page."""
        mock_render.return_value = "Import Page"
        
        response = client.get('/import')
        
        assert response.status_code == 200

    def test_import_data_missing_file(self, client):
        """Test import with missing file."""
        form_data = {'data_type': 'alumnos'}
        
        response = client.post('/import', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302

    def test_import_data_success(self, client, mock_services):
        """Test successful data import."""
        from io import BytesIO

        file_data = b'{"test": "data"}'
        
        form_data = {
            'data_type': 'alumnos',
            'json_file': (BytesIO(file_data), 'test.json')
        }
        
        response = client.post('/import', data=form_data, 
                             content_type='multipart/form-data', follow_redirects=False)
        
        assert response.status_code == 302


class TestScheduleRoutes:
    """Test cases for schedule-related routes."""
    
    @patch('main.render_template')
    def test_schedule_page_with_periods(self, mock_render, client, mock_services):
        """Test schedule page with available periods."""
        mock_periods = ['2025-1', '2025-2']
        mock_services['instance_service'].get_periods.return_value = mock_periods
        mock_render.return_value = "Schedule Page"
        
        response = client.get('/schedule')
        
        assert response.status_code == 200

    @patch('main.render_template')
    def test_schedule_page_no_periods(self, mock_render, client, mock_services):
        """Test schedule page with no periods."""
        mock_services['instance_service'].get_periods.return_value = []
        mock_render.return_value = "Schedule Page"
        
        response = client.get('/schedule')
        
        assert response.status_code == 200

    def test_generate_schedule_no_period(self, client):
        """Test generating schedule without period selection."""
        response = client.post('/schedule/generate', data={}, follow_redirects=False)
        
        assert response.status_code == 302

    def test_generate_schedule_success(self, client, mock_services):
        """Test successful schedule generation."""
        mock_services['schedule_service'].generate_schedule.return_value = {'schedule': 'data'}
        mock_services['schedule_service'].create_csv.return_value = "csv,content"
        
        form_data = {'period': '2025-1'}
        
        response = client.post('/schedule/generate', data=form_data)
        
        mock_services['schedule_service'].generate_schedule.assert_called_once_with('2025-1')
        mock_services['schedule_service'].create_csv.assert_called_once_with('2025-1')


class TestReportRoutes:
    """Test cases for report-related routes."""
    
    @patch('main.render_template')
    def test_reports_get(self, mock_render, client, mock_services):
        """Test GET request for reports page."""
        mock_students = [{'id': 1, 'name': 'Student 1'}]
        mock_sections = [{'id': 1, 'number': 1, 'is_closed': True}]
        mock_activities = [{'id': 1, 'name': 'Activity 1'}]
        
        mock_services['user_service'].get_all.return_value = mock_students
        mock_services['section_service'].get_closed_sections.return_value = mock_sections
        mock_services['activity_service'].get_all_with_context.return_value = mock_activities
        mock_render.return_value = "Reports Page"
        
        response = client.get('/reports')
        
        assert response.status_code == 200

    def test_reports_post_no_type(self, client):
        """Test POST request without report type."""
        response = client.post('/reports', data={}, follow_redirects=False)
        
        assert response.status_code == 302

    @patch('main.render_template')
    def test_reports_topic_instance_report(self, mock_render, client, mock_services):
        """Test generating topic instance report."""
        mock_activity = {'id': 1, 'topic_id': 1}
        mock_topic = {'id': 1, 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_enrollments = [{'user_id': 1, 'user_name': 'Student 1', 'user_email': 'student1@test.com'}]
        
        mock_services['activity_service'].get_by_id.return_value = mock_activity
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['course_taken_service'].get_students_by_section.return_value = mock_enrollments
        mock_services['grade_service'].get_by_activity_and_student.return_value = {'grade': 6.5}
        mock_services['user_service'].get_all.return_value = []
        mock_services['section_service'].get_closed_sections.return_value = []
        mock_services['activity_service'].get_all_with_context.return_value = []
        mock_render.return_value = "Reports Page with Data"
        
        form_data = {
            'report_type': 'topic_instance',
            'activity_id': '1'
        }
        
        response = client.post('/reports', data=form_data)
        
        assert response.status_code == 200


@pytest.mark.parametrize("route,expected_code", [
    ('/', 200),
    ('/courses', 200),
    ('/courses/create', 200),
])
@patch('main.render_template')
def test_basic_routes_render_successfully(mock_render, client, route, expected_code):
    """Test that basic routes render successfully when templates are mocked."""
    mock_render.return_value = "Mocked Template"
    response = client.get(route)
    assert response.status_code == expected_code


class TestHelperFunctions:
    """Test cases for helper functions."""
    
    @patch('main.course_service')
    def test_get_edit_course_context_with_valid_course(self, mock_course_service):
        """Test _get_edit_course_context with valid course ID."""
        from main import _get_edit_course_context
        
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_all_courses = [
            {'id': 1, 'name': 'Test Course'},
            {'id': 2, 'name': 'Other Course'}
        ]
        mock_prerequisites = [{'id': 2, 'name': 'Other Course'}]
        
        mock_course_service.get_by_id.return_value = mock_course
        mock_course_service.get_all.return_value = mock_all_courses
        mock_course_service.get_prerequisites.return_value = mock_prerequisites
        
        course, all_courses, current_prerequisites = _get_edit_course_context(1)
        
        assert course == mock_course
        assert len(all_courses) == 1
        assert all_courses[0]['id'] == 2
        assert current_prerequisites == mock_prerequisites

    @patch('main.course_service')
    def test_get_edit_course_context_with_invalid_course(self, mock_course_service):
        """Test _get_edit_course_context with invalid course ID."""
        from main import _get_edit_course_context
        
        mock_course_service.get_by_id.return_value = None
        
        result = _get_edit_course_context(999)
        
        assert result == (None, None, None)


class TestErrorHandling:
    """Test cases for error handling scenarios."""
    
    def test_create_topic_with_invalid_instance_section_mismatch(self, client, mock_services):
        """Test creating topic with mismatched instance and section."""
        mock_section = {'id': 1, 'instance_id': 2}
        mock_services['section_service'].get_by_id.return_value = mock_section
        
        response = client.get('/instances/1/sections/1/topics/create')
        
        assert response.status_code == 400

    def test_edit_topic_with_invalid_weight_value(self, client, mock_services):
        """Test editing topic with invalid weight value."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1, 'weight_or_percentage': False}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = [mock_topic]
        
        form_data = {
            'name': 'Updated Topic',
            'weight': 'invalid_weight'
        }
        
        response = client.post('/topics/edit/1', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['topic_service'].update.assert_not_called()

    def test_delete_topic_percentage_invalid_values(self, client, mock_services):
        """Test deleting topic with invalid percentage values."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1}
        mock_course = {'id': 1, 'name': 'Test Course'}
        mock_other_topic = {'id': 2, 'name': 'Other Topic'}
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = [
            mock_topic, mock_other_topic
        ]
        
        form_data = {'percentages_2': 'invalid_percentage'}
        
        response = client.post('/topics/delete/percentage/1', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['topic_service'].delete.assert_not_called()


class TestServiceIntegration:
    """Test cases for service integration points."""
    
    @patch('main.render_template')
    def test_course_service_integration(self, mock_render, client, mock_services):
        """Test integration with course service."""
        mock_services['course_service'].get_all.return_value = [
            {'id': 1, 'name': 'Course 1', 'nrc': 'C001'},
            {'id': 2, 'name': 'Course 2', 'nrc': 'C002'}
        ]
        mock_services['course_service'].get_prerequisites.return_value = []
        mock_services['instance_service'].get_by_course_id.return_value = []
        mock_render.return_value = "Courses Page"
        
        response = client.get('/courses')
        
        assert response.status_code == 200
        mock_services['course_service'].get_all.assert_called_once()
        
    @patch('main.render_template')
    def test_topic_service_integration(self, mock_render, client, mock_services):
        """Test integration with topic service."""
        mock_section = {'id': 1, 'instance_id': 1}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = []
        mock_render.return_value = "Topics Page"
        
        response = client.get('/instances/1/sections/1/topics')
        
        assert response.status_code == 200
        mock_services['topic_service'].get_by_section_id.assert_called_once_with(1)


class TestFormValidation:
    """Test cases for form validation."""
    
    def test_create_topic_form_validation_missing_weight(self, client, mock_services):
        """Test creating topic with missing weight field."""
        mock_section = {'id': 1, 'instance_id': 1, 'weight_or_percentage': False}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        
        form_data = {'name': 'New Topic'}
        
        response = client.post('/instances/1/sections/1/topics/create', 
                             data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        
    def test_edit_topic_form_validation_success(self, client, mock_services):
        """Test successful topic editing with valid form data."""
        mock_topic = {'id': 1, 'name': 'Test Topic', 'section_id': 1}
        mock_section = {'id': 1, 'instance_id': 1, 'weight_or_percentage': False}
        mock_instance = {'id': 1, 'course_id': 1, 'period': '2025-1'}
        mock_course = {'id': 1, 'name': 'Test Course'}
        
        mock_services['topic_service'].get_by_id.return_value = mock_topic
        mock_services['section_service'].get_by_id.return_value = mock_section
        mock_services['instance_service'].get_by_id.return_value = mock_instance
        mock_services['course_service'].get_by_id.return_value = mock_course
        mock_services['topic_service'].get_by_section_id.return_value = [mock_topic]
        
        form_data = {
            'name': 'Updated Topic',
            'weight': '150'
        }
        
        response = client.post('/topics/edit/1', data=form_data, follow_redirects=False)
        
        assert response.status_code == 302
        mock_services['topic_service'].update.assert_called_once()


class TestHelperFunctionsAdvanced:
    """Test cases for helper functions in the second half."""
    
    @patch('main.activity_service')
    @patch('main.topic_service')
    def test_validate_activity_and_topic_success(self, mock_topic_service, mock_activity_service):
        """Test _validate_activity_and_topic with valid data."""
        from main import _validate_activity_and_topic
        
        mock_activity = {'id': 1, 'topic_id': 1}
        mock_topic = {'id': 1, 'name': 'Test Topic'}
        
        mock_activity_service.get_by_id.return_value = mock_activity
        mock_topic_service.get_by_id.return_value = mock_topic
        
        activity, topic, error_msg, error_code = _validate_activity_and_topic(1)
        
        assert activity == mock_activity
        assert topic == mock_topic
        assert error_msg is None
        assert error_code is None

    @patch('main.activity_service')
    def test_validate_activity_and_topic_invalid_activity(self, mock_activity_service):
        """Test _validate_activity_and_topic with invalid activity."""
        from main import _validate_activity_and_topic
        
        mock_activity_service.get_by_id.return_value = None
        
        activity, topic, error_msg, error_code = _validate_activity_and_topic(999)
        
        assert activity is None
        assert topic is None
        assert error_msg == "Activity not found"
        assert error_code == 404

    @patch('main.user_service')
    @patch('main.section_service')
    @patch('main.activity_service')
    def test_get_reports_initial_data(self, mock_activity_service, mock_section_service, mock_user_service):
        """Test _get_reports_initial_data function."""
        from main import _get_reports_initial_data
        
        mock_students = [{'id': 1, 'name': 'Student 1'}]
        mock_sections = [{'id': 1, 'is_closed': True}]
        mock_activities = [{'id': 1, 'name': 'Activity 1'}]
        
        mock_user_service.get_all.return_value = mock_students
        mock_section_service.get_closed_sections.return_value = mock_sections
        mock_activity_service.get_all_with_context.return_value = mock_activities
        
        students, closed_sections, activities = _get_reports_initial_data()
        
        assert students == mock_students
        assert closed_sections == mock_sections
        assert activities == mock_activities