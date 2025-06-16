from db import DatabaseConnection

class RoomService:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_all(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms ORDER BY name")
        return cursor.fetchall()
    
    def get_by_id(self, room_id):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms WHERE id = %s", (room_id,))
        return cursor.fetchone()
    
    def get_by_name(self, name):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms WHERE name = %s", (name,))
        return cursor.fetchone()
    
    def create(self, name, capacity):
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Rooms (name, capacity) VALUES (%s, %s)",
            (name, capacity)
        )
        self.db.commit()
        return cursor.lastrowid4
    
    def update(self, room_id, name, capacity):
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Rooms SET name = %s, capacity = %s WHERE id = %s",
            (name, capacity, room_id)
        )
        self.db.commit()
    
    def delete(self, room_id):
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Rooms WHERE id = %s", (room_id,))
        self.db.commit()
    
    def search(self, query):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT * FROM Rooms WHERE name LIKE %s ORDER BY name",
            (f"%{query}%",)
        )
        return cursor.fetchall()
    
    def get_by_capacity(self, min_capacity):
        cursor = self.db.connect()
        cursor.execute(
            "SELECT * FROM Rooms WHERE capacity >= %s ORDER BY capacity",
            (min_capacity,)
        )
        return cursor.fetchall()
    
    def get_available_rooms(self, time_slot, day, period):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms ORDER BY name")
        return cursor.fetchall()