from db import DatabaseConnection

class TopicService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        connection = self.db.connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Topics")
        topics = cursor.fetchall()
        cursor.close()
        connection.close()
        return topics

    def get_by_id(self, topic_id):
        connection = self.db.connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Topics WHERE id = %s", (topic_id,))
        topic = cursor.fetchone()
        cursor.close()
        connection.close()
        return topic

    def create(self, name, section_id, weight, weight_or_percentage):
        connection = self.db.connect()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Topics (name, section_id, weight, weight_or_percentage) VALUES (%s, %s, %s, %s)", 
                       (name, section_id, weight, weight_or_percentage))
        connection.commit()
        cursor.close()
        connection.close()

    def edit(self, topic_id, name, weight, weight_or_percentage):
        connection = self.db.connect()
        cursor = connection.cursor()
        cursor.execute("UPDATE Topics SET name = %s, weight = %s, weight_or_percentage = %s WHERE id = %s", 
                       (name, weight, weight_or_percentage, topic_id))
        connection.commit()
        cursor.close()
        connection.close()

    def delete(self, topic_id):
        connection = self.db.connect()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Topics WHERE id = %s", (topic_id,))
        connection.commit()
        cursor.close()
        connection.close()

    def calculate_total_percentage(self, section_id):
        connection = self.db.connect()
        cursor = connection.cursor()
        cursor.execute("SELECT weight, weight_or_percentage FROM Topics WHERE section_id = %s", (section_id,))
        topics = cursor.fetchall()
        cursor.close()
        connection.close()
        
        total_percentage = 0
        
        for topic in topics:
            weight, weight_or_percentage = topic
            if weight_or_percentage:
                total_percentage += weight  

        return total_percentage
