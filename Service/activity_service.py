from db import DatabaseConnection

class ActivityService:
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Activity")
        return cursor.fetchall()

    def get_by_id(self, activity_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Activity WHERE Id = %s", (activity_id,))
        return cursor.fetchone()

    def create(self, name, topic_id, weight):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Activity (Name, Topic_id, Weight) VALUES (%s, %s, %s)",
            (name, topic_id, weight)
        )
        self.db.commit()

    def update(self, activity_id, name, topic_id, weight):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Activity SET Name = %s, Topic_id = %s, Weight = %s WHERE Id = %s",
            (name, topic_id, weight, activity_id)
        )
        self.db.commit()

    def delete(self, activity_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Activity WHERE Id = %s", (activity_id,))
        self.db.commit()
