"""Grade Service module for managing student grades and calculations.

This module provides CRUD operations for grades, including grade calculations,
final grade computation, and academic performance tracking.
"""

from db import DatabaseConnection


class GradeService:
    """Service class for managing grades in the academic system."""

    def __init__(self):
        """Initialize the grade service with database connection."""
        self.db = DatabaseConnection()

    def get_all(self):
        """Get all grades from the database."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Grades")
        return cursor.fetchall()

    def get_by_id(self, grade_id):
        """Get a specific grade by its ID."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Grades WHERE id = %s", (grade_id,))
        return cursor.fetchone()

    def get_by_activity_and_student(self, activity_id, user_id):
        """Get a grade for a specific activity and student."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT * FROM Grades WHERE activity_id = %s AND user_id = %s",
            (activity_id, user_id)
        )
        return cursor.fetchone()

    def get_by_student(self, user_id):
        """Get all grades for a specific student with context information."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT g.*, a.instance, t.name as topic_name, "
            "s.id as section_id, i.period "
            "FROM Grades g "
            "JOIN Activities a ON g.activity_id = a.id "
            "JOIN Topics t ON a.topic_id = t.id "
            "JOIN Sections s ON t.section_id = s.id "
            "JOIN Instances i ON s.instance_id = i.id "
            "WHERE g.user_id = %s",
            (user_id,)
        )
        return cursor.fetchall()

    def get_by_section(self, section_id):
        """Get all grades for a specific section with context information."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT g.*, a.instance, t.name as topic_name, "
            "u.name as user_name "
            "FROM Grades g "
            "JOIN Activities a ON g.activity_id = a.id "
            "JOIN Topics t ON a.topic_id = t.id "
            "JOIN Users u ON g.user_id = u.id "
            "WHERE t.section_id = %s",
            (section_id,)
        )
        return cursor.fetchall()

    def create(self, grade, user_id, activity_id):
        """Create a new grade record."""
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Grades (grade, user_id, activity_id) "
            "VALUES (%s, %s, %s)",
            (grade, user_id, activity_id)
        )
        self.db.commit()

    def update(self, grade_id, grade):
        """Update an existing grade record."""
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Grades SET grade = %s WHERE id = %s",
            (grade, grade_id)
        )
        self.db.commit()

    def delete(self, grade_id):
        """Delete a grade record."""
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Grades WHERE id = %s", (grade_id,))
        self.db.commit()

    def _fetch_grade_calculation_data(self, user_id, section_id):
        """Fetch all data needed for grade calculation (query method)."""
        cursor = self.db.connect()

        cursor.execute(
            "SELECT id, name, weight, weight_or_percentage "
            "FROM Topics WHERE section_id = %s",
            (section_id,)
        )
        topics = cursor.fetchall()

        for topic in topics:
            topic_id = topic['id']

            cursor.execute(
                "SELECT id, instance, weight, optional_flag "
                "FROM Activities WHERE topic_id = %s",
                (topic_id,)
            )
            topic['activities'] = cursor.fetchall()

            for activity in topic['activities']:
                activity_id = activity['id']
                cursor.execute(
                    "SELECT grade FROM Grades "
                    "WHERE user_id = %s AND activity_id = %s",
                    (user_id, activity_id)
                )
                activity['grade_result'] = cursor.fetchone()

        return topics

    def _calculate_activity_grade(self, activity, is_percentage):
        """Calculate grade contribution for a single activity."""
        activity_weight = activity['weight']
        is_optional = activity['optional_flag']
        grade_result = activity['grade_result']

        if not grade_result:
            if is_optional:
                return 0, 0
            activity_grade = 1.0
        else:
            activity_grade = float(grade_result['grade'])

        if is_percentage:
            contribution = activity_grade * (activity_weight / 100)
            weight_contribution = activity_weight / 100
        else:
            contribution = activity_grade * activity_weight
            weight_contribution = activity_weight

        return contribution, weight_contribution

    def _calculate_topic_grade(self, topic):
        """Calculate the final grade for a single topic."""
        is_percentage = topic['weight_or_percentage']
        topic_grade = 0
        topic_total_weight = 0

        for activity in topic['activities']:
            contribution, weight_contrib = self._calculate_activity_grade(
                activity, is_percentage)

            if contribution == 0 and weight_contrib == 0:
                continue

            topic_grade += contribution
            topic_total_weight += weight_contrib

        if topic_total_weight > 0:
            return topic_grade / topic_total_weight

        return 0

    def calculate_final_grade(self, user_id, section_id):
        """Calculate the final grade for a student in a section."""
        topics = self._fetch_grade_calculation_data(user_id, section_id)

        final_grade = 0
        total_weight = 0

        for topic in topics:
            topic_weight = topic['weight']
            topic_final_grade = self._calculate_topic_grade(topic)

            final_grade += topic_final_grade * topic_weight
            total_weight += topic_weight

        if total_weight > 0:
            return round(final_grade / total_weight, 1)

        return 0
