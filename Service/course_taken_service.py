"""Course Taken Service module for managing student enrollments.

This module provides CRUD operations for student enrollments in courses,
including enrollment management, grade tracking, and academic history.
"""

from db import DatabaseConnection


class CourseTakenService:
    """Service class for managing student course enrollments."""

    def __init__(self):
        """Initialize the course taken service with database connection."""
        self.db = DatabaseConnection()

    def enroll_student(self, user_id, course_id, section_id):
        """Enroll a student in a specific course section."""
        cursor = self.db.connect()
        # Static analysis error fixing: line length
        cursor.execute(
            "INSERT INTO Courses_Taken (user_id, course_id, section_id, "
            "final_grade) VALUES (%s, %s, %s, %s)",
            (user_id, course_id, section_id, 1)
        )
        self.db.commit()

    def unenroll_student(self, course_id, section_id, user_id):
        """Remove a student's enrollment from a specific course section."""
        cursor = self.db.connect()
        # Static analysis error fixing: line length
        cursor.execute(
            "DELETE FROM Courses_Taken WHERE course_id = %s AND "
            "section_id = %s AND user_id = %s",
            (course_id, section_id, user_id)
        )
        self.db.commit()

    def get_students_by_section(self, section_id):
        """Get all students enrolled in a specific section."""
        cursor = self.db.connect()
        # Static analysis error fixing: line length
        cursor.execute(
            "SELECT u.id AS user_id, u.name AS user_name, "
            "u.email AS user_email, ct.final_grade "
            "FROM Courses_Taken ct "
            "JOIN Users u ON ct.user_id = u.id "
            "WHERE ct.section_id = %s",
            (section_id,)
        )
        return cursor.fetchall()

    def get_courses_taken_by_user(self, user_id):
        """Get all courses taken by a specific user."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT c.name, i.period, ct.final_grade "
            "FROM Courses_Taken ct "
            "JOIN Courses c ON ct.course_id = c.id "
            "JOIN Sections s ON ct.section_id = s.id "
            "JOIN Instances i ON s.instance_id = i.id "
            "WHERE ct.user_id = %s",
            (user_id,)
        )
        return cursor.fetchall()

    def get_closed_courses_by_student(self, student_id):
        """Get all closed courses taken by a specific student."""
        cursor = self.db.connect()
        cursor.execute("""
            SELECT ct.final_grade,
                   c.name as course_name,
                   i.period,
                   s.number as section_number
            FROM Courses_Taken ct
            JOIN Sections s ON ct.section_id = s.id
            JOIN Instances i ON s.instance_id = i.id
            JOIN Courses c ON i.course_id = c.id
            WHERE ct.user_id = %s AND s.is_closed = 1
            ORDER BY i.period DESC, c.name
        """, (student_id,))
        return cursor.fetchall()

    def update_final_grade(self, user_id, section_id, final_grade):
        """Update the final grade for a student in a specific section."""
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Courses_Taken SET final_grade = %s "
            "WHERE user_id = %s AND section_id = %s",
            (final_grade, user_id, section_id)
        )
        self.db.commit()

    def is_student_enrolled(self, user_id, section_id):
        """Check if a student is enrolled in a specific section."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT COUNT(*) as count FROM Courses_Taken "
            "WHERE user_id = %s AND section_id = %s",
            (user_id, section_id)
        )
        result = cursor.fetchone()
        return result['count'] > 0
