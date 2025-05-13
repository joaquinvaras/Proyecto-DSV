from db import DatabaseConnection
import csv
import io

class ScheduleService:
    def __init__(self):
        self.db = DatabaseConnection()
        self.last_schedule = []
    
    def get_available_periods(self):
        cursor = self.db.connect()
        cursor.execute("SELECT DISTINCT period FROM Instances ORDER BY period DESC")
        periods = [row['period'] for row in cursor.fetchall()]
        return periods
    
    def get_rooms(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms ORDER BY name")
        #print(f"{cursor.fetchall()}")
        return cursor.fetchall()
    
    def get_sections_by_period(self, period):
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
            ORDER BY c.name, s.number
        """, (period,))
        return cursor.fetchall()
    
    def generate_schedule(self, period):
        sections = sorted(self.get_sections_by_period(period), key=lambda x: -x['credits'])
        rooms = self.get_rooms()

        hours = list(range(9, 18))
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        room_occupancy = {room['id']: {day: {h: False for h in hours} for day in days} for room in rooms}
        teacher_occupancy = {}
        schedule = []

        for section in sections:
            credits = section['credits']
            prof_id = section['professor_id']
            if prof_id not in teacher_occupancy:
                teacher_occupancy[prof_id] = {day: {h: False for h in hours} for day in days}

            assigned = False

            for day in days:
                for room in rooms:
                    for i in range(len(hours) - credits + 1):
                        time_block = hours[i:i+credits]
                        
                        if any(h == 13 for h in time_block):
                            continue
                        if time_block[-1] > 17:
                            continue
                        
                        if all(not room_occupancy[room['id']][day][h] for h in time_block) and \
                        all(not teacher_occupancy[prof_id][day][h] for h in time_block):

                            for h in time_block:
                                room_occupancy[room['id']][day][h] = True
                                teacher_occupancy[prof_id][day][h] = True

                            schedule.append({
                                'course_name': section['course_name'],
                                'nrc': section['nrc'],
                                'number': section['number'],
                                'professor_name': section['professor_name'],
                                'credits': credits,
                                'period': section['period'],
                                'start': time_block[0],
                                'end': time_block[-1] + 1,
                                'day': day,
                                'room_name': room['name'],
                                'room_capacity': room['capacity']
                            })
                            assigned = True
                            break
                    if assigned:
                        break
                if assigned:
                    break

            if not assigned:
                return None

        self.last_schedule = schedule
        return schedule


    def create_csv(self, period):
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow([
            'Course name', 'Code', 'Section number', 'Professor name', 'Credits',
            'Period', 'Schedule', 'Day', 'Room', 'Capacity'
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