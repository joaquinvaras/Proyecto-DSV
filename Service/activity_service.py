from db import DatabaseConnection

class ActivityService:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Activities")
        return cursor.fetchall()
    
    def get_by_id(self, activity_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Activities WHERE id = %s", (activity_id,))
        return cursor.fetchone()
    
    def get_by_topic_id(self, topic_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Activities WHERE topic_id = %s ORDER BY instance", (topic_id,))
        return cursor.fetchall()
    
    def get_next_instance_number(self, topic_id):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT MAX(instance) as max_instance FROM Activities WHERE topic_id = %s", 
            (topic_id,)
        )
        result = cursor.fetchone()
        
        if not result or result['max_instance'] is None:
            return 1
        
        return result['max_instance'] + 1
    
    def create(self, topic_id, instance, weight, optional_flag):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Activities (topic_id, instance, weight, optional_flag) VALUES (%s, %s, %s, %s)",
            (topic_id, instance, weight, optional_flag)
        )
        self.db.commit()
    
    def update(self, activity_id, instance, weight, optional_flag):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Activities SET instance = %s, weight = %s, optional_flag = %s WHERE id = %s",
            (instance, weight, optional_flag, activity_id)
        )
        self.db.commit()
    
    def delete(self, activity_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Grades WHERE activity_id = %s", (activity_id,))
        cursor.execute("DELETE FROM Activities WHERE id = %s", (activity_id,))
        self.db.commit()