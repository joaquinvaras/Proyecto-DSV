from db import DatabaseConnection

class CourseService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Course")
        return cursor.fetchall()

    def get_by_id(self, course_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Course WHERE Id = %s", (course_id,))
        return cursor.fetchone()

    def create(self, name, ncr, prerequisite):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Course (Name, NCR, Prerequisite) VALUES (%s, %s, %s)",
            (name, ncr, prerequisite)
        )
        self.db.commit()

    def update(self, course_id, name, ncr, prerequisite):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Course SET Name = %s, NCR = %s, Prerequisite = %s WHERE Id = %s",
            (name, ncr, prerequisite, course_id)
        )
        self.db.commit()

    def delete(self, course_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Course WHERE Id = %s", (course_id,))
        self.db.commit()
