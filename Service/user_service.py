from db import DatabaseConnection

class UserService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self, is_professor=None):
        cursor = self.db.connect()
        if is_professor is None:
            cursor.execute("SELECT * FROM Users")
        else:
            cursor.execute("SELECT * FROM Users WHERE is_professor = %s", (is_professor,))
        return cursor.fetchall()

    def get_by_id(self, user_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Users WHERE id = %s", (user_id,))
        return cursor.fetchone()

    def create(self, name, email, is_professor, admission_date=None):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Users (name, email, admission_date, is_professor) VALUES (%s, %s, %s, %s)",
            (name, email, admission_date, is_professor)
        )
        self.db.commit()

    def update(self, user_id, name, email, is_professor, admission_date=None):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Users SET name = %s, email = %s, admission_date = %s, is_professor = %s WHERE id = %s",
            (name, email, admission_date, is_professor, user_id)
        )
        self.db.commit()

    def delete(self, user_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Users WHERE id = %s", (user_id,))
        self.db.commit()
