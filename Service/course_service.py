from db import DatabaseConnection

class CourseService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Courses")
        return cursor.fetchall()

    def get_by_id(self, course_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Courses WHERE id = %s", (course_id,))
        return cursor.fetchone()

    def get_prerequisites(self, course_id):
        cursor = self.db.connect()
        query = """
            SELECT c.* FROM Courses c
            JOIN CoursePrerequisites cp ON c.id = cp.prerequisite_id
            WHERE cp.course_id = %s
        """
        cursor.execute(query, (course_id,))
        return cursor.fetchall()

    def create(self, name, nrc, prerequisites=None):
        if prerequisites is None:
            prerequisites = []

        cursor = self.db.connect()

        cursor.execute(
            "INSERT INTO Courses (name, nrc) VALUES (%s, %s)",
            (name, nrc)
        )
        course_id = cursor.lastrowid

        for prereq_id in prerequisites:
            cursor.execute(
                "INSERT INTO CoursePrerequisites (course_id, prerequisite_id) VALUES (%s, %s)",
                (course_id, prereq_id)
            )

        self.db.commit()

    def update(self, course_id, name, nrc, prerequisites=None):
        if prerequisites is None:
            prerequisites = []

        cursor = self.db.connect()

        cursor.execute(
            "UPDATE Courses SET name = %s, nrc = %s WHERE id = %s",
            (name, nrc, course_id)
        )

        cursor.execute(
            "DELETE FROM CoursePrerequisites WHERE course_id = %s",
            (course_id,)
        )

        for prereq_id in prerequisites:
            cursor.execute(
                "INSERT INTO CoursePrerequisites (course_id, prerequisite_id) VALUES (%s, %s)",
                (course_id, prereq_id)
            )

        self.db.commit()

    def delete(self, course_id):
        cursor = self.db.connect()

        cursor.execute("DELETE FROM CoursePrerequisites WHERE course_id = %s", (course_id,))

        cursor.execute("DELETE FROM Courses WHERE id = %s", (course_id,))

        self.db.commit()
