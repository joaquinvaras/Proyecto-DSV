from db import DatabaseConnection

class CourseService:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Courses")
        return cursor.fetchall()
    
    def get_by_id(self, course_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Courses WHERE id = %s", (course_id,))
        return cursor.fetchone()
    
    def get_prerequisites(self, course_id):
        cursor = self.db.connect()
        query = """
        SELECT c.* FROM Courses c
        JOIN CoursePrerequisites cp ON c.id = cp.prerequisite_id
        WHERE cp.course_id = %s
        """
        cursor.execute(query, (course_id,))
        return cursor.fetchall()
    
    def get_enrollments_in_section(self, section_id):
        cursor = self.db.connect()
        query = """
        SELECT u.id AS user_id, u.name AS user_name, u.email AS user_email
        FROM Users u
        JOIN Courses_Taken ct ON u.id = ct.user_id
        WHERE ct.section_id = %s
        """
        cursor.execute(query, (section_id,))
        return cursor.fetchall()
    
    def unenroll_student_from_section(self, course_id, section_id, user_id):
        cursor = self.db.connect()
        cursor.execute(
            "DELETE FROM Courses_Taken WHERE course_id = %s AND section_id = %s AND user_id = %s",
            (course_id, section_id, user_id)
        )
        self.db.commit()
    
    def create(self, name, nrc, credits, prerequisites=None):
        if prerequisites is None:
            prerequisites = []
        
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Courses (name, nrc, credits) VALUES (%s, %s, %s)",
            (name, nrc, credits)
        )
        course_id = cursor.lastrowid
        
        for prereq_id in prerequisites:
            cursor.execute(
                "INSERT INTO CoursePrerequisites (course_id, prerequisite_id) VALUES (%s, %s)",
                (course_id, prereq_id)
            )
        
        self.db.commit()
        return course_id
    
    def update(self, course_id, name, nrc, credits, prerequisites=None):
        if prerequisites is None:
            prerequisites = []
        
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Courses SET name = %s, nrc = %s, credits = %s WHERE id = %s",
            (name, nrc, credits, course_id)
        )
        
        cursor.execute(
            "DELETE FROM CoursePrerequisites WHERE course_id = %s",
            (course_id,)
        )
        
        for prereq_id in prerequisites:
            cursor.execute(
                "INSERT INTO CoursePrerequisites (course_id, prerequisite_id) VALUES (%s, %s)",
                (course_id, prereq_id)
            )
        
        self.db.commit()
    
    def delete(self, course_id):
        cursor = self.db.connect()
        
        
        cursor.execute("SELECT id FROM Instances WHERE course_id = %s", (course_id,))
        instances = cursor.fetchall()
        
        for instance in instances:
            instance_id = instance['id']
            
            cursor.execute("SELECT id FROM Sections WHERE instance_id = %s", (instance_id,))
            sections = cursor.fetchall()
            
            for section in sections:
                section_id = section['id']
                
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
            
            cursor.execute("DELETE FROM Sections WHERE instance_id = %s", (instance_id,))
        
        cursor.execute("DELETE FROM Instances WHERE course_id = %s", (course_id,))
        
        cursor.execute("DELETE FROM CoursePrerequisites WHERE course_id = %s OR prerequisite_id = %s", (course_id, course_id))
        
        cursor.execute("DELETE FROM Courses WHERE id = %s", (course_id,))
        
        self.db.commit()
    
    def get_instances(self, course_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Instances WHERE course_id = %s", (course_id,))
        return cursor.fetchall()
    
    def create_instance(self, course_id, period):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Instances (course_id, period) VALUES (%s, %s)",
            (course_id, period)
        )
        self.db.commit()
        return cursor.lastrowid