from db import DatabaseConnection

class TopicService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Topic")
        return cursor.fetchall()

    def get_by_id(self, topic_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Topic WHERE Id = %s", (topic_id,))
        return cursor.fetchone()

    def create(self, name, course_id):
        cursor = self.db.connect()
        cursor.execute
