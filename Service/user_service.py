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
    
    def get_by_email(self, email):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        return cursor.fetchone()
    
    def get_next_import_id(self, is_professor):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT MAX(import_id) as max_import_id FROM Users WHERE is_professor = %s",
            (is_professor,)
        )
        result = cursor.fetchone()
        
        if not result or result['max_import_id'] is None:
            return 1
        
        return result['max_import_id'] + 1
    
    def create(self, name, email, is_professor, admission_date=None, import_id=None):
        cursor = self.db.connect()
        
        if import_id is None:
            import_id = self.get_next_import_id(is_professor)
        
        cursor.execute(
            "INSERT INTO Users (name, email, admission_date, is_professor, import_id) VALUES (%s, %s, %s, %s, %s)",
            (name, email, admission_date, is_professor, import_id)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, user_id, name, email, is_professor, admission_date=None, import_id=None):
        cursor = self.db.connect()
        
        if import_id is not None:
            cursor.execute(
                "UPDATE Users SET name = %s, email = %s, admission_date = %s, is_professor = %s, import_id = %s WHERE id = %s",
                (name, email, admission_date, is_professor, import_id, user_id)
            )
        else:
            cursor.execute(
                "UPDATE Users SET name = %s, email = %s, admission_date = %s, is_professor = %s WHERE id = %s",
                (name, email, admission_date, is_professor, user_id)
            )
        self.db.commit()
    
    def delete(self, user_id):
        cursor = self.db.connect()
        
        cursor.execute("DELETE FROM Grades WHERE user_id = %s", (user_id,))
        
        cursor.execute("DELETE FROM Courses_Taken WHERE user_id = %s", (user_id,))
        
        if self.is_professor_with_sections(user_id):
            cursor.execute("UPDATE Sections SET professor_id = NULL WHERE professor_id = %s", (user_id,))
        
        cursor.execute("DELETE FROM Users WHERE id = %s", (user_id,))
        
        self.db.commit()
    
    def is_professor_with_sections(self, user_id):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT COUNT(*) as count FROM Sections WHERE professor_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        return result['count'] > 0
    
    def get_courses_taken(self, user_id):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT ct.*, c.name as course_name, i.period, s.number as section_number "
            "FROM Courses_Taken ct "
            "JOIN Courses c ON ct.course_id = c.id "
            "JOIN Sections s ON ct.section_id = s.id "
            "JOIN Instances i ON s.instance_id = i.id "
            "WHERE ct.user_id = %s",
            (user_id,)
        )
        return cursor.fetchall()
    
    def get_sections_taught(self, user_id):
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