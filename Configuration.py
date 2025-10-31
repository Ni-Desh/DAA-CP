from Professor import Professor
from Course import Course
from Room import Room
from StudentsGroup import StudentsGroup # Ensure this is the updated class
from CourseClass import CourseClass
import copy 

class Configuration:
    _instance = None 

    def __init__(self, filename='input.cfg'):
        # 1. Singleton Check
        if Configuration._instance is not None:
            raise Exception("Configuration is a singleton. Use Configuration.getInstance() to access it.")
            
        Configuration._instance = self

        # 2. Initialize core data dictionaries
        self._professors = {}
        self._courses = {}
        self._rooms = {}
        self._studentGroups = {}
        self._courseClasses = {}

        # 3. Load data upon creation
        self.ReadConfiguration(filename)
    
    @staticmethod
    def getInstance():
        if Configuration._instance is None:
            raise RuntimeError("Configuration has not been initialized. Call Configuration('input.cfg') first.")
        return Configuration._instance

    def ReadConfiguration(self, filename):
        # Reset IDs before loading new data
        Professor.RestartIDs()
        Room.RestartIDs()
        CourseClass.RestartIDs()

        # Clear existing data structures
        self._professors = {}
        self._courses = {}
        self._rooms = {}
        self._studentGroups = {}
        self._courseClasses = {}

        current_block = None
        data = {}
        line_num = 0

        with open(filename, 'r') as f:
            for line in f:
                line_num += 1
                raw_line = line.strip()
                
                # Skip blank lines and comments
                if not raw_line or (raw_line.startswith('#') and not raw_line.startswith(('#prof', '#course', '#room', '#group', '#class', '#end'))):
                    continue

                # 2. Handle block end
                if raw_line == '#end':
                    
                    # --- Block Commit Logic ---
                    if current_block == 'prof':
                        p = Professor(int(data['id']), data['name'])
                        self._professors[p.GetId()] = p
                    
                    elif current_block == 'course':
                        c = Course(int(data['id']), data['name'])
                        self._courses[c.GetId()] = c
                        
                    elif current_block == 'room':
                        r = Room(
                            name=data['name'], 
                            lab=data['lab'].lower() in ('true', '1'), 
                            numberOfSeats=int(data['size'])
                        )
                        self._rooms[r.GetId()] = r
                        
                    elif current_block == 'group':
                        # >>> UPDATED GROUP LOADING LOGIC <<<
                        # Default to global schedule bounds (8 AM to 6 PM) if 'start' or 'end' are missing
                        start_time = int(data.get('start', 8)) 
                        end_time = int(data.get('end', 18))   
                        
                        g = StudentsGroup(
                            int(data['id']), 
                            data['name'], 
                            int(data['size']), 
                            timeWindowStart=start_time, # NEW PARAMETER
                            timeWindowEnd=end_time      # NEW PARAMETER
                        ) 
                        self._studentGroups[g.GetId()] = g
                        # >>> END UPDATED GROUP LOADING LOGIC <<<
                        
                    elif current_block == 'class':
                        try:
                            prof_id = int(data['professor'])
                            course_id = int(data['course'])
                            group_id = int(data['group'])
                            
                            prof = self._professors[prof_id]
                            course = self._courses[course_id]
                            group = self._studentGroups[group_id]

                            duration = int(data['duration']) 
                            is_lab = data.get('lab', 'false').lower() in ('true', '1')

                            cc = CourseClass(
                                professor=prof,
                                course=course,
                                duration=duration, 
                                group=group,
                                lab_required=is_lab
                            )
                            self._courseClasses[cc.GetId()] = cc
                            
                        except KeyError as e:
                            print(f"ERROR (Key): Class block skipped at line {line_num} due to missing ID/Key: {e} in block data: {data}")
                        except ValueError as e:
                            print(f"ERROR (Value): Class block skipped at line {line_num} due to VALUE ERROR: {e}. Check if IDs/Duration are numbers: {data}")
                        except Exception as e:
                            print(f"CRITICAL ERROR: Unexpected exception at line {line_num} while loading class: {e}")
                            
                    # --- End Block Commit Logic ---

                    # Reset block status
                    current_block = None
                    data = {}
                    continue 

                # 3. Handle block start
                if raw_line.startswith('#'):
                    current_block = raw_line[1:].strip()
                
                # 4. Handle data line
                elif current_block:
                    if '=' in raw_line:
                        key, value = raw_line.split('=', 1)
                        data[key.strip()] = value.strip()
                    else:
                        pass
        
        # FINAL CHECK: If the file ended without an #end
        if current_block is not None:
            print(f"FINAL WARNING: File ended without an '#end' marker for the last block: #{current_block}. Data was lost.")

        # New Feature Setup (Hardcoded Unavailable Slots) - Example setup
        if 1 in self._professors:
            self._professors[1].AddUnavailableSlot(0, 9) 
        if 2 in self._professors:
            self._professors[2].AddUnavailableSlot(1, 1) 
            
    # Getter methods 
    def GetNumberOfRooms(self):
        return len(self._rooms)
    
    def GetNumberOfCourseClasses(self):
        return len(self._courseClasses)

    def GetCourseClasses(self):
        return self._courseClasses

    def GetRoomById(self, id):
        return self._rooms.get(id)

    def GetProfessorById(self, id):
        return self._professors.get(id)