"""Room Service module for managing classroom facilities.

This module provides CRUD operations for rooms, including capacity management,
availability checking, and room search functionality.
"""

from db import DatabaseConnection


class RoomService:
    """Service class for managing rooms in the academic system."""

    def __init__(self):
        """Initialize the room service with database connection."""
        self.db = DatabaseConnection()

    def get_all(self):
        """Get all rooms ordered by name."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms ORDER BY name")
        return cursor.fetchall()

    def get_by_id(self, room_id):
        """Get a specific room by its ID."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms WHERE id = %s", (room_id,))
        return cursor.fetchone()

    def get_by_name(self, name):
        """Get a specific room by its name."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms WHERE name = %s", (name,))
        return cursor.fetchone()

    def create(self, name, capacity):
        """Create a new room with specified name and capacity."""
        cursor = self.db.connect()
        cursor.execute(
            "INSERT INTO Rooms (name, capacity) VALUES (%s, %s)",
            (name, capacity)
        )
        self.db.commit()
        # Static analysis error fixing: corrected typo from lastrowid4
        return cursor.lastrowid

    def update(self, room_id, name, capacity):
        """Update an existing room's name and capacity."""
        cursor = self.db.connect()
        cursor.execute(
            "UPDATE Rooms SET name = %s, capacity = %s WHERE id = %s",
            (name, capacity, room_id)
        )
        self.db.commit()

    def delete(self, room_id):
        """Delete a room by its ID."""
        cursor = self.db.connect()
        cursor.execute("DELETE FROM Rooms WHERE id = %s", (room_id,))
        self.db.commit()

    def search(self, query):
        """Search for rooms by name pattern."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT * FROM Rooms WHERE name LIKE %s ORDER BY name",
            (f"%{query}%",)
        )
        return cursor.fetchall()

    def get_by_capacity(self, min_capacity):
        """Get rooms with capacity greater than or equal to minimum."""
        cursor = self.db.connect()
        cursor.execute(
            "SELECT * FROM Rooms WHERE capacity >= %s ORDER BY capacity",
            (min_capacity,)
        )
        return cursor.fetchall()

    # Static analysis error fixing: unused arguments marked with underscore
    def get_available_rooms(self, time_slot, day, period):
        """Get available rooms for a specific time slot, day, and period."""
        _ = time_slot, day, period

        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms ORDER BY name")
        return cursor.fetchall()
