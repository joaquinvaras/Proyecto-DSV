"""Schedule Service module for generating academic schedules.

This module provides functionality to generate course schedules with automatic
room and time assignment, avoiding conflicts between professors and rooms.
"""

import csv
import io
from db import DatabaseConnection


class ScheduleService:
    """Service class for generating and managing academic schedules."""

    def __init__(self):
        """Initialize the schedule service with database connection."""
        self.db = DatabaseConnection()
        self.last_schedule = []

    def _fetch_periods_from_database(self):
        """Command: Execute database operations to fetch periods."""
        cursor = self.db.connect()
        cursor.execute("SELECT DISTINCT period FROM Instances "
                       "ORDER BY period DESC")
        return cursor.fetchall()

    def get_available_periods(self):
        """Query: Return the list of available periods."""
        rows = self._fetch_periods_from_database()
        periods = [row['period'] for row in rows]
        return periods

    def get_rooms(self):
        """Get all available rooms for scheduling."""
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms ORDER BY name")
        return cursor.fetchall()

    def get_sections_by_period(self, period):
        """Get all sections for a specific period with course information."""
        cursor = self.db.connect()
        cursor.execute("""
            SELECT s.id AS section_id, s.number, s.professor_id,
                   c.id AS course_id, c.name AS course_name, c.credits, c.nrc,
                   i.id AS instance_id, i.period,
                   u.name AS professor_name
            FROM Sections s
            JOIN Instances i ON s.instance_id = i.id
            JOIN Courses c ON i.course_id = c.id
            JOIN Users u ON s.professor_id = u.id
            WHERE i.period = %s
            ORDER BY c.credits DESC, c.name, s.number
        """, (period,))
        return cursor.fetchall()

    def _initialize_schedule_data(self, period):
        """Initialize basic data needed for schedule generation."""
        sections = sorted(self.get_sections_by_period(period),
                          key=lambda x: -x['credits'])
        rooms = self.get_rooms()
        hours = list(range(9, 18))
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        return sections, rooms, hours, days

    def _initialize_occupancy_structures(self, rooms, hours, days):
        """Create initial occupancy tracking structures."""
        room_occupancy = {room['id']: {day: {h: False for h in hours}
                                       for day in days} for room in rooms}
        teacher_occupancy = {}
        schedule = []

        return room_occupancy, teacher_occupancy, schedule

    def _is_valid_time_block(self, time_block):
        """Validate if a time block is valid for scheduling."""
        if any(h == 13 for h in time_block):
            return False
        if time_block[-1] > 17:
            return False
        return True

    def _is_time_slot_available(self, **slot_data):
        """Check if a time slot is available for both room and teacher."""
        room_id = slot_data['room_id']
        prof_id = slot_data['prof_id']
        day = slot_data['day']
        time_block = slot_data['time_block']
        room_occupancy = slot_data['room_occupancy']
        teacher_occupancy = slot_data['teacher_occupancy']

        room_available = all(not room_occupancy[room_id][day][h]
                             for h in time_block)
        teacher_available = all(not teacher_occupancy[prof_id][day][h]
                                for h in time_block)

        return room_available and teacher_available

    def _mark_time_slot_occupied(self, **slot_data):
        """Mark a time slot as occupied for both room and teacher."""
        room_id = slot_data['room_id']
        prof_id = slot_data['prof_id']
        day = slot_data['day']
        time_block = slot_data['time_block']
        room_occupancy = slot_data['room_occupancy']
        teacher_occupancy = slot_data['teacher_occupancy']

        for h in time_block:
            room_occupancy[room_id][day][h] = True
            teacher_occupancy[prof_id][day][h] = True

    def _create_schedule_entry(self, section, time_block, day, room):
        """Create a schedule entry object."""
        return {
            'course_name': section['course_name'],
            'nrc': section['nrc'],
            'number': section['number'],
            'professor_name': section['professor_name'],
            'credits': section['credits'],
            'period': section['period'],
            'start': time_block[0],
            'end': time_block[-1] + 1,
            'day': day,
            'room_name': room['name'],
            'room_capacity': room['capacity']
        }

    def _try_assign_section_to_slot(self, section, room, day, hours,
                                     **occupancy_data):
        """Attempt to assign a section to a specific room and day."""
        room_occupancy = occupancy_data['room_occupancy']
        teacher_occupancy = occupancy_data['teacher_occupancy']
        schedule = occupancy_data['schedule']

        course_credits = section['credits']
        prof_id = section['professor_id']

        for i in range(len(hours) - course_credits + 1):
            time_block = hours[i:i+course_credits]

            if not self._is_valid_time_block(time_block):
                continue

            slot_available = self._is_time_slot_available(
                room_id=room['id'],
                prof_id=prof_id,
                day=day,
                time_block=time_block,
                room_occupancy=room_occupancy,
                teacher_occupancy=teacher_occupancy
            )

            if slot_available:
                self._mark_time_slot_occupied(
                    room_id=room['id'],
                    prof_id=prof_id,
                    day=day,
                    time_block=time_block,
                    room_occupancy=room_occupancy,
                    teacher_occupancy=teacher_occupancy
                )

                schedule_entry = self._create_schedule_entry(section,
                                                             time_block,
                                                             day, room)
                schedule.append(schedule_entry)

                return True

        return False

    def _assign_section_to_schedule(self, section, days, rooms, hours,
                                     **occupancy_data):
        """Attempt to assign a section to the schedule."""
        room_occupancy = occupancy_data['room_occupancy']
        teacher_occupancy = occupancy_data['teacher_occupancy']
        schedule = occupancy_data['schedule']

        prof_id = section['professor_id']

        if prof_id not in teacher_occupancy:
            teacher_occupancy[prof_id] = {day: {h: False for h in hours}
                                          for day in days}

        for day in days:
            for room in rooms:
                assignment_successful = self._try_assign_section_to_slot(
                    section, room, day, hours,
                    room_occupancy=room_occupancy,
                    teacher_occupancy=teacher_occupancy,
                    schedule=schedule
                )
                if assignment_successful:
                    return True

        return False

    def generate_schedule(self, period):
        """Generate a complete schedule for the given period."""
        sections, rooms, hours, days = self._initialize_schedule_data(period)
        room_occupancy, teacher_occupancy, schedule = (
            self._initialize_occupancy_structures(rooms, hours, days))

        for section in sections:
            assignment_successful = self._assign_section_to_schedule(
                section, days, rooms, hours,
                room_occupancy=room_occupancy,
                teacher_occupancy=teacher_occupancy,
                schedule=schedule
            )
            if not assignment_successful:
                return None

        self.last_schedule = schedule
        return schedule
    # ----- solution ONE LEVEL OF ABSTRACTION error ---

    def create_csv(self, period):
        """Create CSV content for the schedule.
        
        Args:
            period: The period for the schedule (currently unused but kept
                   for future compatibility)
        """
        _ = period

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow([
            'Course name', 'Code', 'Section number', 'Professor name',
            'Credits', 'Period', 'Schedule', 'Day', 'Room', 'Capacity'
        ])

        for s in self.last_schedule:
            start = f"{s['start']}:00"
            end = f"{s['end']}:00"
            writer.writerow([
                s['course_name'],
                s['nrc'],
                s['number'],
                s['professor_name'],
                s['credits'],
                s['period'],
                f"{start}-{end}",
                s['day'],
                s['room_name'],
                s['room_capacity']
            ])

        return output.getvalue()
