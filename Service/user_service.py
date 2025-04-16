from db import DatabaseConnection

class UserService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self, is_professor=None):
        cursor = self.db.connect()
        if is_professor is None:
            cursor.execute("SELECT * FROM User")
        else:
            cursor.execute("SELECT * FROM User WHERE Is_Professor = %s", (is_professor,))
        return cursor.fetchall()

    def get_by_id(self, user_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM User WHERE Id = %s", (user_id,))
        return cursor.fetchone()

    def create(self, name, email, admission_date, is_professor):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO User (Name, Email, Admision_Date, Is_Professor) VALUES (%s, %s, %s, %s)",
            (name, email, admission_date, is_professor)
        )
        self.db.commit()

    def update(self, user_id, name, email, admission_date, is_professor):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE User SET Name = %s, Email = %s, Admision_Date = %s, Is_Professor = %s WHERE Id = %s",
            (name, email, admission_date, is_professor, user_id)
        )
        self.db.commit()

    def delete(self, user_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM User WHERE Id = %s", (user_id,))
        self.db.commit()
