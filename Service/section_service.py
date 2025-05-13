from db import DatabaseConnection

class SectionService:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage, s.is_closed, 
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        """)
        return cursor.fetchall()
    
    def get_by_id(self, section_id):
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage, s.professor_id, s.is_closed,
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE s.id = %s
        """, (section_id,))
        return cursor.fetchone()
    
    def get_by_instance_id(self, instance_id):
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage, s.is_closed, 
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE s.instance_id = %s
        """, (instance_id,))
        return cursor.fetchall()
    
    def get_by_course_id(self, course_id):
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage, s.is_closed, 
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE i.course_id = %s
        """, (course_id,))
        return cursor.fetchall()
    
    def get_by_course_and_period(self, course_id, period):
        cursor = self.db.connect()
        cursor.execute("""
        SELECT s.id, s.instance_id, s.number, s.weight_or_percentage, s.is_closed, 
               u.name AS professor_name, i.period, i.course_id
        FROM Sections s
        JOIN Instances i ON s.instance_id = i.id
        LEFT JOIN Users u ON s.professor_id = u.id
        WHERE i.course_id = %s AND i.period = %s
        """, (course_id, period))
        return cursor.fetchall()
    
    def section_number_exists(self, instance_id, number, exclude_section_id=None):
        cursor = self.db.connect()
        
        if exclude_section_id:
            cursor.execute(
                "SELECT COUNT(*) as count FROM Sections WHERE instance_id = %s AND number = %s AND id != %s",
                (instance_id, number, exclude_section_id)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) as count FROM Sections WHERE instance_id = %s AND number = %s",
                (instance_id, number)
            )
            
        result = cursor.fetchone()
        return result['count'] > 0
    
    def create(self, instance_id, number, professor_id, weight_or_percentage):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Sections (instance_id, number, professor_id, weight_or_percentage, is_closed) VALUES (%s, %s, %s, %s, FALSE)",
            (instance_id, number, professor_id, weight_or_percentage)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, section_id, number, professor_id, weight_or_percentage):
        section = self.get_by_id(section_id)
        if section and section['is_closed']:
            raise ValueError("Cannot modify a closed section")
            
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Sections SET number = %s, professor_id = %s, weight_or_percentage = %s WHERE id = %s",
            (number, professor_id, weight_or_percentage, section_id)
        )
        self.db.commit()
    
    def close_section(self, section_id):
        section = self.get_by_id(section_id)
        if not section:
            raise ValueError("Section not found")
        
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Sections SET is_closed = TRUE WHERE id = %s",
            (section_id,)
        )
        self.db.commit()
        return True
    
    def delete(self, section_id):
        section = self.get_by_id(section_id)
        if section and section['is_closed']:
            raise ValueError("Cannot delete a closed section")
            
        cursor = self.db.connect()
        
        cursor.execute("SELECT id FROM Topics WHERE section_id = %s", (section_id,))
        topics = cursor.fetchall()
        
        for topic in topics:
            topic_id = topic['id']
            
            cursor.execute("SELECT id FROM Activities WHERE topic_id = %s", (topic_id,))
            activities = cursor.fetchall()
            
            for activity in activities:
                activity_id = activity['id']
                cursor.execute("DELETE FROM Grades WHERE activity_id = %s", (activity_id,))
            
            cursor.execute("DELETE FROM Activities WHERE topic_id = %s", (topic_id,))
        
        cursor.execute("DELETE FROM Topics WHERE section_id = %s", (section_id,))
        
        cursor.execute("DELETE FROM Courses_Taken WHERE section_id = %s", (section_id,))
        
        cursor.execute("DELETE FROM Sections WHERE id = %s", (section_id,))
        
        self.db.commit()