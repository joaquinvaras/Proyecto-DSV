from db import DatabaseConnection

class CourseTakenService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Course_Taken")
        return cursor.fetchall()

    def get_by_id(self, course_taken_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Course_Taken WHERE Id = %s", (course_taken_id,))
        return cursor.fetchone()

    def get_by_user(self, user_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Course_Taken WHERE User_id = %s", (user_id,))
        return cursor.fetchall()

    def create(self, user_id, section_id):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Course_Taken (User_id, Section_id) VALUES (%s, %s)",
            (user_id, section_id)
        )
        self.db.commit()

    def delete(self, course_taken_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Course_Taken WHERE Id = %s", (course_taken_id,))
        self.db.commit()
