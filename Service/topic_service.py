"""Topic Service module for managing evaluation topics.

This module provides CRUD operations for topics within sections, including
weight management, cascading deletions, and section-level calculations.
"""

from db import DatabaseConnection


class TopicService:
    """Service class for managing topics in the academic system."""

    def __init__(self):
        """Initialize the topic service with database connection."""
        self.db = DatabaseConnection()

    def get_all(self):
        """Get all topics from the database."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Topics")
        return cursor.fetchall()

    def get_by_id(self, topic_id):
        """Get a specific topic by its ID."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Topics WHERE id = %s", (topic_id,))
        return cursor.fetchone()

    def get_by_section_id(self, section_id):
        """Get all topics for a specific section."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Topics WHERE section_id = %s",
                       (section_id,))
        return cursor.fetchall()

    def create(self, name, section_id, weight, weight_or_percentage):
        """Create a new topic for a section."""
        cursor = self.db.connect()
        # Static analysis error fixing: line length
        cursor.execute(
            "INSERT INTO Topics (name, section_id, weight, "
            "weight_or_percentage) VALUES (%s, %s, %s, %s)",
            (name, section_id, weight, weight_or_percentage)
        )
        self.db.commit()
        return cursor.lastrowid

    def update(self, topic_id, name, weight, weight_or_percentage):
        """Update an existing topic."""
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Topics SET name = %s, weight = %s, "
            "weight_or_percentage = %s WHERE id = %s",
            (name, weight, weight_or_percentage, topic_id)
        )
        self.db.commit()

    def delete(self, topic_id):
        """Delete a topic and all its related activities and grades."""
        cursor = self.db.connect()
        cursor.execute("SELECT id FROM Activities WHERE topic_id = %s",
                       (topic_id,))
        activities = cursor.fetchall()

        for activity in activities:
            activity_id = activity['id']
            cursor.execute("DELETE FROM Grades WHERE activity_id = %s",
                           (activity_id,))

        cursor.execute("DELETE FROM Activities WHERE topic_id = %s",
                       (topic_id,))
        cursor.execute("DELETE FROM Topics WHERE id = %s", (topic_id,))
        self.db.commit()

    def get_total_weight(self, section_id):
        """Get the total weight of all topics in a section."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT SUM(weight) as total_weight FROM Topics "
            "WHERE section_id = %s",
            (section_id,)
        )
        result = cursor.fetchone()
        return result['total_weight'] if result['total_weight'] else 0
