from db import DatabaseConnection

class SectionService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Section")
        return cursor.fetchall()

    def get_by_id(self, section_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Section WHERE Id = %s", (section_id,))
        return cursor.fetchone()

    def create(self, course_id, period, number, professor_id):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Section (Course_id, Period, Number, Professor) VALUES (%s, %s, %s, %s)",
            (course_id, period, number, professor_id)
        )
        self.db.commit()

    def update(self, section_id, course_id, period, number, professor_id):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Section SET Course_id = %s, Period = %s, Number = %s, Professor = %s WHERE Id = %s",
            (course_id, period, number, professor_id, section_id)
        )
        self.db.commit()

    def delete(self, section_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Section WHERE Id = %s", (section_id,))
        self.db.commit()
