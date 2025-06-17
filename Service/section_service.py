"""Section Service module for managing course sections.

This module provides CRUD operations for course sections, including professor
assignment, enrollment management, section state tracking, and cascading deletions.
"""

from db import DatabaseConnection


class SectionService:
    """Service class for managing sections in the academic system."""

    def __init__(self):
        """Initialize the section service with database connection."""
        self.db = DatabaseConnection()

    def get_all(self):
        """Get all sections with professor and instance information."""
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        """)
        return cursor.fetchall()

    def get_by_id(self, section_id):
        """Get a specific section by its ID with related information."""
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.professor_id, s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE s.id = %s
        """, (section_id,))
        return cursor.fetchone()

    def get_by_instance_id(self, instance_id):
        """Get all sections for a specific instance."""
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE s.instance_id = %s
        """, (instance_id,))
        return cursor.fetchall()

    def get_by_course_id(self, course_id):
        """Get all sections for a specific course."""
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE i.course_id = %s
        """, (course_id,))
        return cursor.fetchall()

    def get_by_course_and_period(self, course_id, period):
        """Get all sections for a specific course and period."""
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage,
               s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE i.course_id = %s AND i.period = %s
        """, (course_id, period))
        return cursor.fetchall()

    def get_closed_sections(self):
        """Get all closed sections with course and period information."""
        cursor = self.db.connect()
        cursor.execute("""
            SELECT s.id, s.number, s.is_closed,
                   c.name as course_name, i.period
            FROM Sections s
            JOIN Instances i ON s.instance_id = i.id
            JOIN Courses c ON i.course_id = c.id
            WHERE s.is_closed = 1
            ORDER BY c.name, i.period, s.number
        """)
        return cursor.fetchall()

    def section_number_exists(self, instance_id, number,
                              exclude_section_id=None):
        """Check if a section number already exists for an instance."""
        cursor = self.db.connect()

        if exclude_section_id:
            cursor.execute(
                "SELECT COUNT(*) as count FROM Sections "
                "WHERE instance_id = %s AND number = %s AND id != %s",
                (instance_id, number, exclude_section_id)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) as count FROM Sections "
                "WHERE instance_id = %s AND number = %s",
                (instance_id, number)
            )

        result = cursor.fetchone()
        return result['count'] > 0

    def create(self, instance_id, number, professor_id, weight_or_percentage):
        """Create a new section for an instance."""
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Sections (instance_id, number, professor_id, "
            "weight_or_percentage, is_closed) VALUES (%s, %s, %s, %s, FALSE)",
            (instance_id, number, professor_id, weight_or_percentage)
        )
        self.db.commit()
        return cursor.lastrowid

    def update(self, section_id, number, professor_id, weight_or_percentage):
        """Update an existing section (only if not closed)."""
        section = self.get_by_id(section_id)
        if section and section['is_closed']:
            raise ValueError("Cannot modify a closed section")

        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Sections SET number = %s, professor_id = %s, "
            "weight_or_percentage = %s WHERE id = %s",
            (number, professor_id, weight_or_percentage, section_id)
        )
        self.db.commit()

    def close_section(self, section_id):
        """Close a section to prevent further modifications."""
        section = self.get_by_id(section_id)
        if not section:
            raise ValueError("Section not found")

        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Sections SET is_closed = TRUE WHERE id = %s",
            (section_id,)
        )
        self.db.commit()
        return True

    def delete(self, section_id):
        """Delete a section and all its related data (only if not closed)."""
        section = self.get_by_id(section_id)
        if section and section['is_closed']:
            raise ValueError("Cannot delete a closed section")

        cursor = self.db.connect()

        cursor.execute("SELECT id FROM Topics WHERE section_id = %s",
                       (section_id,))
        topics = cursor.fetchall()

        for topic in topics:
            topic_id = topic['id']

            cursor.execute("SELECT id FROM Activities WHERE topic_id = %s",
                           (topic_id,))
            activities = cursor.fetchall()

            for activity in activities:
                activity_id = activity['id']
                cursor.execute("DELETE FROM Grades WHERE activity_id = %s",
                               (activity_id,))

            cursor.execute("DELETE FROM Activities WHERE topic_id = %s",
                           (topic_id,))

        cursor.execute("DELETE FROM Topics WHERE section_id = %s",
                       (section_id,))

        cursor.execute("DELETE FROM Courses_Taken WHERE section_id = %s",
                       (section_id,))

        cursor.execute("DELETE FROM Sections WHERE id = %s", (section_id,))

        self.db.commit()
