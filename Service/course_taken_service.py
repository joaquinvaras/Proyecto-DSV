from db import DatabaseConnection

class CourseTakenService:
    def __init__(self):
        self.db = DatabaseConnection()

    def enroll_student(self, user_id, course_id, section_id):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Courses_Taken (user_id, course_id, section_id, final_grade) VALUES (%s, %s, %s, %s)",
            (user_id, course_id, section_id, 1)  
        )
        self.db.commit()
    
    def unenroll_student(self, course_id, section_id, user_id):
        cursor = self.db.connect()
        cursor.execute(
            "DELETE FROM Courses_Taken WHERE course_id = %s AND section_id = %s AND user_id = %s",
            (course_id, section_id, user_id)
        )
        self.db.commit()

    def get_students_by_section(self, section_id):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT u.name, u.email, ct.final_grade FROM Courses_Taken ct "
            "JOIN Users u ON ct.user_id = u.id "
            "WHERE ct.section_id = %s",
            (section_id,)
        )
        return cursor.fetchall()

    def get_courses_taken_by_user(self, user_id):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT c.name, s.period, ct.final_grade FROM Courses_Taken ct "
            "JOIN Courses c ON ct.course_id = c.id "
            "JOIN Sections s ON ct.section_id = s.id "
            "WHERE ct.user_id = %s",
            (user_id,)
        )
        return cursor.fetchall()
