"""Instance Service module for managing course instances.

This module provides CRUD operations for course instances, including period
management, cascading deletions, and relationship handling with sections.
"""

from db import DatabaseConnection


class InstanceService:
    """Service class for managing course instances in the academic system."""

    def __init__(self):
        """Initialize the instance service with database connection."""
        self.db = DatabaseConnection()

    def get_all(self):
        """Get all instances with course information."""
        cursor = self.db.connect()
        cursor.execute("""
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
        """)
        return cursor.fetchall()

    def get_by_id(self, instance_id):
        """Get a specific instance by its ID with course information."""
        cursor = self.db.connect()
        cursor.execute("""
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
            WHERE i.id = %s
        """, (instance_id,))
        return cursor.fetchone()

    def get_by_course_id(self, course_id):
        """Get all instances for a specific course."""
        cursor = self.db.connect()
        cursor.execute("""
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
            WHERE i.course_id = %s
        """, (course_id,))
        return cursor.fetchall()

    def get_by_period(self, period):
        """Get all instances for a specific period."""
        cursor = self.db.connect()
        cursor.execute("""
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
            WHERE i.period = %s
        """, (period,))
        return cursor.fetchall()

    def get_by_course_and_period(self, course_id, period):
        """Get a specific instance by course and period."""
        cursor = self.db.connect()
        cursor.execute("""
            SELECT i.*, c.name as course_name, c.nrc
            FROM Instances i
            JOIN Courses c ON i.course_id = c.id
            WHERE i.course_id = %s AND i.period = %s
        """, (course_id, period))
        return cursor.fetchone()

    def create(self, course_id, period):
        """Create a new instance for a course in a specific period."""
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Instances (course_id, period) VALUES (%s, %s)",
            (course_id, period)
        )
        self.db.commit()
        return cursor.lastrowid

    def update(self, instance_id, period):
        """Update the period for an existing instance."""
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Instances SET period = %s WHERE id = %s",
            (period, instance_id)
        )
        self.db.commit()

    def delete(self, instance_id):
        """Delete an instance and all its related data (cascading delete)."""
        cursor = self.db.connect()

        cursor.execute("SELECT id FROM Sections WHERE instance_id = %s",
                       (instance_id,))
        sections = cursor.fetchall()

        for section in sections:
            section_id = section['id']

            cursor.execute("SELECT id FROM Topics WHERE section_id = %s",
                           (section_id,))
            topics = cursor.fetchall()

            for topic in topics:
                topic_id = topic['id']

                cursor.execute("SELECT id FROM Activities WHERE "
                               "topic_id = %s", (topic_id,))
                activities = cursor.fetchall()

                for activity in activities:
                    activity_id = activity['id']
                    cursor.execute("DELETE FROM Grades WHERE "
                                   "activity_id = %s", (activity_id,))

                cursor.execute("DELETE FROM Activities WHERE "
                               "topic_id = %s", (topic_id,))

            cursor.execute("DELETE FROM Topics WHERE section_id = %s",
                           (section_id,))

            cursor.execute("DELETE FROM Courses_Taken WHERE "
                           "section_id = %s", (section_id,))

            cursor.execute("DELETE FROM Sections WHERE id = %s",
                           (section_id,))

        cursor.execute("DELETE FROM Instances WHERE id = %s",
                       (instance_id,))

        self.db.commit()

    def get_periods(self):
        """Get all distinct periods from instances, ordered by most recent."""
        cursor = self.db.connect()
        # Static analysis error fixing: line length
        cursor.execute("SELECT DISTINCT period FROM Instances "
                       "ORDER BY period DESC")
        results = cursor.fetchall()
        return [result['period'] for result in results]

    def get_section_count(self, instance_id):
        """Get the count of sections for a specific instance."""
        cursor = self.db.connect()
        cursor.execute("SELECT COUNT(*) as count FROM Sections "
                       "WHERE instance_id = %s", (instance_id,))
        result = cursor.fetchone()
        return result['count']
