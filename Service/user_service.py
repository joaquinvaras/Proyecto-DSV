"""User Service module for managing users (students and professors).

This module provides CRUD operations for users, including professor and student
management, import ID tracking, and relationship handling with courses and sections.
"""

from db import DatabaseConnection


class UserService:
    """Service class for managing users in the academic system."""

    def __init__(self):
        """Initialize the user service with database connection."""
        self.db = DatabaseConnection()

    def get_all(self, is_professor=None):
        """Get all users, optionally filtered by professor status."""
        cursor = self.db.connect()
        if is_professor is None:
            cursor.execute("SELECT * FROM Users")
        else:
            cursor.execute("SELECT * FROM Users WHERE is_professor = %s",
                           (is_professor,))
        return cursor.fetchall()

    def get_by_id(self, user_id):
        """Get a specific user by their ID."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Users WHERE id = %s", (user_id,))
        return cursor.fetchone()

    def get_by_email(self, email):
        """Get a specific user by their email address."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        return cursor.fetchone()

    def get_next_import_id(self, is_professor):
        """Get the next available import ID for a user type."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT MAX(import_id) as max_import_id FROM Users "
            "WHERE is_professor = %s",
            (is_professor,)
        )
        result = cursor.fetchone()

        if not result or result['max_import_id'] is None:
            return 1

        return result['max_import_id'] + 1

    # Static analysis error fixing: too many arguments - using keyword args
    def create(self, name, email, is_professor, **user_data):
        """Create a new user with optional admission date and import ID."""
        admission_date = user_data.get('admission_date')
        import_id = user_data.get('import_id')

        cursor = self.db.connect()

        if import_id is None:
            import_id = self.get_next_import_id(is_professor)

        # Static analysis error fixing: line length
        cursor.execute(
            "INSERT INTO Users (name, email, admission_date, is_professor, "
            "import_id) VALUES (%s, %s, %s, %s, %s)",
            (name, email, admission_date, is_professor, import_id)
        )
        self.db.commit()
        return cursor.lastrowid

    # Static analysis error fixing: too many arguments - using keyword args
    def update(self, user_id, name, email, is_professor, **user_data):
        """Update an existing user with optional admission date and import ID."""
        admission_date = user_data.get('admission_date')
        import_id = user_data.get('import_id')

        cursor = self.db.connect()

        if import_id is not None:
            # Static analysis error fixing: line length
            cursor.execute(
                "UPDATE Users SET name = %s, email = %s, "
                "admission_date = %s, is_professor = %s, import_id = %s "
                "WHERE id = %s",
                (name, email, admission_date, is_professor, import_id,
                 user_id)
            )
        else:
            # Static analysis error fixing: line length
            cursor.execute(
                "UPDATE Users SET name = %s, email = %s, "
                "admission_date = %s, is_professor = %s WHERE id = %s",
                (name, email, admission_date, is_professor, user_id)
            )
        self.db.commit()

    def delete(self, user_id):
        """Delete a user and handle related data appropriately."""
        cursor = self.db.connect()

        cursor.execute("DELETE FROM Grades WHERE user_id = %s", (user_id,))

        cursor.execute("DELETE FROM Courses_Taken WHERE user_id = %s",
                       (user_id,))

        if self.is_professor_with_sections(user_id):
            # Static analysis error fixing: line length
            cursor.execute("UPDATE Sections SET professor_id = NULL "
                           "WHERE professor_id = %s", (user_id,))

        cursor.execute("DELETE FROM Users WHERE id = %s", (user_id,))

        self.db.commit()

    def is_professor_with_sections(self, user_id):
        """Check if a professor has any assigned sections."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT COUNT(*) as count FROM Sections WHERE professor_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        return result['count'] > 0

    def get_courses_taken(self, user_id):
        """Get all courses taken by a specific user."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT ct.*, c.name as course_name, i.period, "
            "s.number as section_number "
            "FROM Courses_Taken ct "
            "JOIN Courses c ON ct.course_id = c.id "
            "JOIN Sections s ON ct.section_id = s.id "
            "JOIN Instances i ON s.instance_id = i.id "
            "WHERE ct.user_id = %s",
            (user_id,)
        )
        return cursor.fetchall()

    def get_sections_taught(self, user_id):
        """Get all sections taught by a specific professor."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT s.*, i.period, c.name as course_name, c.nrc "
            "FROM Sections s "
            "JOIN Instances i ON s.instance_id = i.id "
            "JOIN Courses c ON i.course_id = c.id "
            "WHERE s.professor_id = %s",
            (user_id,)
        )
        return cursor.fetchall()
