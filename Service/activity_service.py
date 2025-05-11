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
        cursor.execute("SELECT * FROM Activities WHERE topic_id = %s", (topic_id,))
        return cursor.fetchall()
    
    def create(self, name, topic_id, weight, optional_flag):

        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Activities (name, topic_id, weight, optional_flag) VALUES (%s, %s, %s, %s)",
            (name, topic_id, weight, optional_flag)
        )
        self.db.commit()
    
    def update(self, activity_id, name, weight, optional_flag):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Activities SET name = %s, weight = %s, optional_flag = %s WHERE id = %s",
            (name, weight, optional_flag, activity_id)
        )
        self.db.commit()
    
    def delete(self, activity_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Grades WHERE activity_id = %s", (activity_id,))
        cursor.execute("DELETE FROM Activities WHERE id = %s", (activity_id,))
        self.db.commit()