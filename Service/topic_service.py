from db import DatabaseConnection

class TopicService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Topics")
        return cursor.fetchall()

    def get_by_id(self, topic_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Topics WHERE id = %s", (topic_id,))
        return cursor.fetchone()

    def get_by_section_id(self, section_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Topics WHERE section_id = %s", (section_id,))
        return cursor.fetchall()

    def create(self, name, section_id, weight, weight_or_percentage):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Topics (name, section_id, weight, weight_or_percentage) VALUES (%s, %s, %s, %s)", 
            (name, section_id, weight, weight_or_percentage)
        )
        self.db.commit()

    def update(self, topic_id, name, weight, weight_or_percentage):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Topics SET name = %s, weight = %s, weight_or_percentage = %s WHERE id = %s", 
            (name, weight, weight_or_percentage, topic_id)
        )
        self.db.commit()

    def delete(self, topic_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Topics WHERE id = %s", (topic_id,))
        self.db.commit()