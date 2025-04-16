from db import DatabaseConnection

class GradeService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Grade")
        return cursor.fetchall()

    def get_by_id(self, grade_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Grade WHERE Id = %s", (grade_id,))
        return cursor.fetchone()

    def get_by_activity_and_student(self, activity_id, user_id):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT * FROM Grade WHERE Activity_id = %s AND User_id = %s",
            (activity_id, user_id)
        )
        return cursor.fetchone()

    def create(self, value, user_id, activity_id):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Grade (Value, User_id, Activity_id) VALUES (%s, %s, %s)",
            (value, user_id, activity_id)
        )
        self.db.commit()

    def update(self, grade_id, value):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Grade SET Value = %s WHERE Id = %s",
            (value, grade_id)
        )
        self.db.commit()

    def delete(self, grade_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Grade WHERE Id = %s", (grade_id,))
        self.db.commit()
