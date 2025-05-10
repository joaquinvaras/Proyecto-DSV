from db import DatabaseConnection

class SectionService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("""
            SELECT s.id, s.course_id, s.period, s.number, s.weight_or_percentage, u.name AS professor_name
            FROM Sections s
            LEFT JOIN Users u ON s.professor_id = u.id
        """)
        return cursor.fetchall()

    def get_by_id(self, section_id):
        cursor = self.db.connect()
        cursor.execute("""
            SELECT s.id, s.course_id, s.period, s.number, s.weight_or_percentage, u.name AS professor_name
            FROM Sections s
            LEFT JOIN Users u ON s.professor_id = u.id
            WHERE s.id = %s
        """, (section_id,))
        return cursor.fetchone()

    def get_by_course_id(self, course_id):
        cursor = self.db.connect()
        cursor.execute("""
            SELECT s.id, s.course_id, s.period, s.number, s.weight_or_percentage, u.name AS professor_name
            FROM Sections s
            LEFT JOIN Users u ON s.professor_id = u.id
            WHERE s.course_id = %s
        """, (course_id,))
        return cursor.fetchall()

    def create(self, course_id, period, number, professor_id, weight_or_percentage):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Sections (course_id, period, number, professor_id, weight_or_percentage) VALUES (%s, %s, %s, %s, %s)",
            (course_id, period, number, professor_id, weight_or_percentage)
        )
        self.db.commit()

    def update(self, section_id, course_id, period, number, professor_id, weight_or_percentage):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Sections SET course_id = %s, period = %s, number = %s, professor_id = %s, weight_or_percentage = %s WHERE id = %s",
            (course_id, period, number, professor_id, weight_or_percentage, section_id)
        )
        self.db.commit()

    def delete(self, section_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Sections WHERE id = %s", (section_id,))
        self.db.commit()
