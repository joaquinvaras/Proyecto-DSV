from db import DatabaseConnection
import csv
import io

class ScheduleService:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_available_periods(self):
        cursor = self.db.connect()
        cursor.execute("SELECT DISTINCT period FROM Instances ORDER BY period DESC")
        periods = [row['period'] for row in cursor.fetchall()]
        return periods
    
    def get_rooms(self):
        cursor = self.db.connect()
        cursor.execute("SELECT * FROM Rooms ORDER BY name")
        return cursor.fetchall()
    
    def get_sections_by_period(self, period):
        cursor = self.db.connect()
        cursor.execute("""
            SELECT s.id, s.number, s.professor_id, s.weight_or_percentage, 
                   c.id AS course_id, c.name AS course_name, c.credits, c.nrc,
                   i.id AS instance_id, i.period,
                   u.name AS professor_name, u.email AS professor_email
            FROM Sections s
            JOIN Instances i ON s.instance_id = i.id
            JOIN Courses c ON i.course_id = c.id
            JOIN Users u ON s.professor_id = u.id
            WHERE i.period = %s
            ORDER BY c.name, s.number
        """, (period,))
        return cursor.fetchall()
    
    def generate_schedule_csv(self, period):
        sections = self.get_sections_by_period(period)
        rooms = self.get_rooms()
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        morning_blocks = ["9-10", "10-11", "11-12", "12-13"]
        afternoon_blocks = ["14-15", "15-16", "16-17", "17-18"]
        time_blocks = morning_blocks + afternoon_blocks
        
        schedule = {}
        for day in days:
            schedule[day] = {}
            for time_block in time_blocks:
                schedule[day][time_block] = {"rooms": {}}
                for room in rooms:
                    schedule[day][time_block]["rooms"][room['name']] = None
        
        for section in sections:
            credits = section['credits']
            
            assigned = False
            
            for day in days:
                if assigned:
                    break
                
                for i in range(len(morning_blocks) - credits + 1):
                    if assigned:
                        break
                    
                    for room in rooms:
                        room_available = True
                        for j in range(credits):
                            time_block = morning_blocks[i + j]
                            if schedule[day][time_block]["rooms"][room['name']] is not None:
                                room_available = False
                                break
                        
                        if room_available:
                            professor_available = True
                            for j in range(credits):
                                time_block = morning_blocks[i + j]
                                for r_name in schedule[day][time_block]["rooms"]:
                                    if (schedule[day][time_block]["rooms"][r_name] is not None and 
                                        schedule[day][time_block]["rooms"][r_name]["professor_id"] == section['professor_id']):
                                        professor_available = False
                                        break
                            
                            if professor_available:
                                for j in range(credits):
                                    time_block = morning_blocks[i + j]
                                    schedule[day][time_block]["rooms"][room['name']] = {
                                        "section_id": section['id'],
                                        "section_number": section['number'],
                                        "course_name": section['course_name'],
                                        "course_nrc": section['nrc'],
                                        "professor_name": section['professor_name'],
                                        "professor_email": section['professor_email'],
                                        "professor_id": section['professor_id'],
                                        "credits": section['credits']
                                    }
                                assigned = True
                                break
                
                if not assigned:
                    for i in range(len(afternoon_blocks) - credits + 1):
                        if assigned:
                            break
                        
                        for room in rooms:
                            room_available = True
                            for j in range(credits):
                                time_block = afternoon_blocks[i + j]
                                if schedule[day][time_block]["rooms"][room['name']] is not None:
                                    room_available = False
                                    break
                            
                            if room_available:
                                professor_available = True
                                for j in range(credits):
                                    time_block = afternoon_blocks[i + j]
                                    for r_name in schedule[day][time_block]["rooms"]:
                                        if (schedule[day][time_block]["rooms"][r_name] is not None and 
                                            schedule[day][time_block]["rooms"][r_name]["professor_id"] == section['professor_id']):
                                            professor_available = False
                                            break
                                
                                if professor_available:
                                    for j in range(credits):
                                        time_block = afternoon_blocks[i + j]
                                        schedule[day][time_block]["rooms"][room['name']] = {
                                            "section_id": section['id'],
                                            "section_number": section['number'],
                                            "course_name": section['course_name'],
                                            "course_nrc": section['nrc'],
                                            "professor_name": section['professor_name'],
                                            "professor_email": section['professor_email'],
                                            "professor_id": section['professor_id'],
                                            "credits": section['credits']
                                        }
                                    assigned = True
                                    break
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        header = ["Day", "Time Block"]
        for room in rooms:
            header.append(f"Room: {room['name']} (Capacity: {room['capacity']})")
        writer.writerow(header)
        
        for day in days:
            for time_block in time_blocks:
                row = [day, time_block]
                for room in rooms:
                    if schedule[day][time_block]["rooms"][room['name']] is not None:
                        section_info = schedule[day][time_block]["rooms"][room['name']]
                        cell_content = f"{section_info['course_name']} (Section {section_info['section_number']})\nProf: {section_info['professor_name']}"
                        row.append(cell_content)
                    else:
                        row.append("")
                writer.writerow(row)
        
        return output.getvalue()