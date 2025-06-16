from db import DatabaseConnection

class GradeService:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Grades")
        return cursor.fetchall()
    
    def get_by_id(self, grade_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Grades WHERE id = %s", (grade_id,))
        return cursor.fetchone()
    
    def get_by_activity_and_student(self, activity_id, user_id):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT * FROM Grades WHERE activity_id = %s AND user_id = %s",
            (activity_id, user_id)
        )
        return cursor.fetchone()
    
    def get_by_student(self, user_id):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT g.*, a.instance, t.name as topic_name, s.id as section_id, i.period " 
            "FROM Grades g "
            "JOIN Activities a ON g.activity_id = a.id "
            "JOIN Topics t ON a.topic_id = t.id "
            "JOIN Sections s ON t.section_id = s.id "
            "JOIN Instances i ON s.instance_id = i.id "
            "WHERE g.user_id = %s",
            (user_id,)
        )
        return cursor.fetchall()
    
    def get_by_section(self, section_id):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT g.*, a.instance, t.name as topic_name, u.name as user_name " 
            "FROM Grades g "
            "JOIN Activities a ON g.activity_id = a.id "
            "JOIN Topics t ON a.topic_id = t.id "
            "JOIN Users u ON g.user_id = u.id "
            "WHERE t.section_id = %s",
            (section_id,)
        )
        return cursor.fetchall()
    
    def create(self, grade, user_id, activity_id):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Grades (grade, user_id, activity_id) VALUES (%s, %s, %s)",
            (grade, user_id, activity_id)
        )
        self.db.commit()
    
    def update(self, grade_id, grade):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Grades SET grade = %s WHERE id = %s",
            (grade, grade_id)
        )
        self.db.commit()
    
    def delete(self, grade_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Grades WHERE id = %s", (grade_id,))
        self.db.commit()
    
    # ----- solution SEPARATION OF QUERY AND COMMAND error ---
    def _fetch_grade_calculation_data(self, user_id, section_id):
        cursor = self.db.connect()
        
        cursor.execute(
            "SELECT id, name, weight, weight_or_percentage FROM Topics WHERE section_id = %s",
            (section_id,)
        )
        topics = cursor.fetchall()
        
        for topic in topics:
            topic_id = topic['id']
            
            cursor.execute(
                "SELECT id, instance, weight, optional_flag FROM Activities WHERE topic_id = %s",
                (topic_id,)
            )
            topic['activities'] = cursor.fetchall()
            
            for activity in topic['activities']:
                activity_id = activity['id']
                cursor.execute(
                    "SELECT grade FROM Grades WHERE user_id = %s AND activity_id = %s",
                    (user_id, activity_id)
                )
                activity['grade_result'] = cursor.fetchone()
        
        return topics
    
    def calculate_final_grade(self, user_id, section_id):
        topics = self._fetch_grade_calculation_data(user_id, section_id)
        
        final_grade = 0
        total_weight = 0
        
        for topic in topics:
            topic_weight = topic['weight']
            is_percentage = topic['weight_or_percentage']
            
            topic_grade = 0
            topic_total_weight = 0
            
            for activity in topic['activities']:
                activity_weight = activity['weight']
                is_optional = activity['optional_flag']
                grade_result = activity['grade_result']
                
                if not grade_result:
                    if is_optional:
                        continue 
                    else:
                        activity_grade = 1.0
                else:
                    activity_grade = grade_result['grade']
                
                if is_percentage:
                    topic_grade += activity_grade * (activity_weight / 100)
                    topic_total_weight += activity_weight / 100
                else:
                    topic_grade += activity_grade * activity_weight
                    topic_total_weight += activity_weight
            
            if topic_total_weight > 0:
                topic_final_grade = topic_grade / topic_total_weight
            else:
                topic_final_grade = 0
            
            final_grade += topic_final_grade * topic_weight
            total_weight += topic_weight
        
        if total_weight > 0:
            return round(final_grade / total_weight, 1)
        else:
            return 0
    # ----- solution SEPARATION OF QUERY AND COMMAND error ---