"""Activity Service module for managing academic activities.

This module provides CRUD operations for activities within topics,
including instance numbering, weight management, and grade relationships.
"""

from db import DatabaseConnection


class ActivityService:
    """Service class for managing activities in the academic system."""

    def __init__(self):
        """Initialize the activity service with database connection."""
        self.db = DatabaseConnection()

    def get_all(self):
        """Get all activities from the database."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Activities")
        return cursor.fetchall()

    def get_by_id(self, activity_id):
        """Get a specific activity by its ID."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Activities WHERE id = %s",
                       (activity_id,))
        return cursor.fetchone()

    def get_by_topic_id(self, topic_id):
        """Get all activities for a specific topic, ordered by instance."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Activities WHERE topic_id = %s "
                       "ORDER BY instance", (topic_id,))
        return cursor.fetchall()

    def get_all_with_context(self):
        """Get all activities with their contextual information."""
        cursor = self.db.connect()
        cursor.execute("""
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
        """)
        return cursor.fetchall()

    def get_next_instance_number(self, topic_id):
        """Get the next available instance number for a topic."""
        cursor = self.db.connect()
        # Static analysis error fixing: line length
        cursor.execute(
            "SELECT MAX(instance) as max_instance FROM Activities "
            "WHERE topic_id = %s",
            (topic_id,)
        )
        result = cursor.fetchone()
        if not result or result['max_instance'] is None:
            return 1
        return result['max_instance'] + 1

    def create(self, topic_id, instance, weight, optional_flag):
        """Create a new activity."""
        cursor = self.db.connect()
        # Static analysis error fixing: line length
        cursor.execute(
            "INSERT INTO Activities (topic_id, instance, weight, "
            "optional_flag) VALUES (%s, %s, %s, %s)",
            (topic_id, instance, weight, optional_flag)
        )
        self.db.commit()

    def update(self, activity_id, instance, weight, optional_flag):
        """Update an existing activity."""
        cursor = self.db.connect()
        # Static analysis error fixing: line length
        cursor.execute(
            "UPDATE Activities SET instance = %s, weight = %s, "
            "optional_flag = %s WHERE id = %s",
            (instance, weight, optional_flag, activity_id)
        )
        self.db.commit()

    def delete(self, activity_id):
        """Delete an activity and its associated grades."""
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Grades WHERE activity_id = %s",
                       (activity_id,))
        cursor.execute("DELETE FROM Activities WHERE id = %s",
                       (activity_id,))
        self.db.commit()
        