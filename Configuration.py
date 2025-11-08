# Configuration.py

import copy

# --- Helper Classes (Standard Timetabling Models) ---

class Room:
    def __init__(self, name, size, is_lab):
        self._name = name
        self._size = size
        self._is_lab = is_lab

    def GetName(self): return self._name
    def GetSize(self): return self._size
    def IsLab(self): return self._is_lab
    
    # Required for list/dict operations
    def __repr__(self):
        return f"Room('{self._name}', {self._size}, Lab: {self._is_lab})"

class Group:
    # Assuming start and end are hour integers (e.g., 8 to 18)
    _next_id = 1 

    def __init__(self, name, size, start_hour, end_hour):
        self._id = Group._next_id
        Group._next_id += 1
        self._name = name
        self._size = size
        self._start_hour = start_hour
        self._end_hour = end_hour
        
    def GetId(self): return self._id
    def GetName(self): return self._name
    def GetSize(self): return self._size
    def GetAvailableStartTime(self): return self._start_hour
    def GetAvailableEndTime(self): return self._end_hour

class Course:
    _next_id = 1000 # Use a high ID to avoid conflict with cfg file IDs

    def __init__(self, id_or_dummy, name):
        # Allow use of provided ID from placeholder, but ensure unique if needed
        self._id = id_or_dummy 
        self._name = name

    def GetId(self): return self._id
    def GetName(self): return self._name

class Professor:
    _next_id = 5000 # Use a high ID to avoid conflict with cfg file IDs

    def __init__(self, id_or_dummy, name):
        self._id = id_or_dummy 
        self._name = name

    def GetId(self): return self._id
    def GetName(self): return self._name

class CourseClass:
    # A single teaching occurrence (e.g., a 1-hour Theory class or a 2-hour Lab block)
    def __init__(self, id, group, course, professor, duration, is_lab):
        self._id = id
        self._group = group
        self._course = course
        self._professor = professor
        self._duration = duration # in hours
        self._is_lab = is_lab

    def GetId(self): return self._id
    def GetGroup(self): return self._group
    def GetCourse(self): return self._course
    def GetProfessor(self): return self._professor
    def GetDuration(self): return self._duration
    def IsLabRequired(self): return self._is_lab
    
    # Added for debugging
    def __repr__(self):
        return f"Class(ID:{self._id}, {self._course.GetName()} for {self._group.GetName()}, {self._duration}h, Lab: {self._is_lab})"

# --- Configuration Singleton ---
class Configuration:
    
    __instance = None
    
    @staticmethod
    def getInstance():
        if Configuration.__instance == None:
            raise Exception("Configuration not initialized. Call Configuration('file.cfg') first.")
        return Configuration.__instance

    def __init__(self, filename):
        if Configuration.__instance != None:
            raise Exception("Configuration is a Singleton. Use getInstance() to retrieve it.")
        
        Configuration.__instance = self
        
        # Initialize internal storage maps
        self._rooms = {} 
        self._course_classes = {} 
        self._groups = {}
        self._courses = {}
        self._professors = {}
        
    # Public Accessors (needed by Algorithm.py and Schedule.py)
    def GetRooms(self): return self._rooms
    def GetNumberOfRooms(self): return len(self._rooms)
    def GetCourseClasses(self): return self._course_classes
    def GetGroups(self): return self._groups
    def GetCourses(self): return self._courses
    def GetProfessors(self): return self._professors


    def ReadConfiguration(self, filename): 
        """
        Loads all configuration data (Rooms, Classes, etc.) from the specified file.
        NOTE: This version uses the hardcoded placeholder data provided.
        """
        print(f"Loading configuration from {filename} (using internal placeholder data)...")
        
        try:
            # --- Placeholder Data Initialization (All Requirements Applied) ---
            
            # Reset ID counters for consistency if needed (important for Group/Course/Professor)
            Group._next_id = 1 

            # Rooms (ID: 0, 1, 2, 3)
            self._rooms = {
                0: Room("R48", 24, False), 1: Room("R51", 60, False), 
                2: Room("R52", 60, False), 3: Room("R54", 60, False),
                4: Room("R53", 60, True), 5: Room("R50", 60, True),
                6: Room("R13", 60, True),
            }
            
            # Helper objects (Groups use auto-incrementing IDs starting from 1)
            g1 = Group('TY/1', 19, 8, 18) # Group ID 1
            g2 = Group('TY/2', 19, 8, 18) # Group ID 2
            g3 = Group('SY/3', 19, 8, 18) # Group ID 3
            g4 = Group('SY/4', 19, 8, 18) # Group ID 4
            
            # Courses (Use IDs 1-11 from config for consistency)
            c_dsa = Course(1, "DSA"); c_os = Course(2, "OS"); c_daa = Course(3, "DAA"); 
            c_mam = Course(4, "MAM"); c_cc = Course(5, "CC"); c_dbms = Course(6, "DBMS"); 
            c_oops = Course(7, "OOPS"); c_sp = Course(8, "SP"); c_sdam = Course(9, "SDAM"); 
            c_cn = Course(10, "CN"); c_dt = Course(11, "DT")

            # Professors (Use IDs 1-13 from config for consistency)
            p_bailke = Professor(1, "Bailke"); p_kunekar = Professor(2, "Kunekar"); 
            p_joglekar = Professor(3, "Joglekar"); p_cholke = Professor(4, "Cholke"); 
            p_amune = Professor(5, "Amune"); p_vayadande = Professor(6, "Vayadande"); 
            p_sawant = Professor(7, "Sawant"); p_dange = Professor(8, "Dange"); 
            p_deshpande = Professor(9, "Deshpande"); p_joshi = Professor(10, "Joshi"); 
            p_jadhav = Professor(11, "Jadhav"); p_sultanpure = Professor(12, "Sultanpure"); 
            p_ghdadekar = Professor(13, "Ghdadekar")
            
            self._groups = {g.GetId(): g for g in [g1, g2, g3, g4]}
            self._courses = {c.GetId(): c for c in [c_dsa, c_os, c_daa, c_mam, c_cc, c_dbms, c_oops, c_sp, c_sdam, c_cn, c_dt]}
            self._professors = {p.GetId(): p for p in [p_bailke, p_kunekar, p_joglekar, p_cholke, p_amune, p_vayadande, p_sawant, p_dange, p_deshpande, p_joshi, p_jadhav, p_sultanpure, p_ghdadekar]}

            # Course Classes: Total of 20 classes/sessions after correction
            self._course_classes = {
                # TY/1 
                1: CourseClass(1, g1, c_dbms, p_cholke, 2, True), # DBMS Lab (2h)
                2: CourseClass(2, g1, c_cc, p_joglekar, 1, False), # CC Theory (1h)
                3: CourseClass(3, g1, c_cc, p_joglekar, 1, False), # CC Theory (1h)
                4: CourseClass(4, g1, c_dbms, p_cholke, 1, False), # DBMS Theory (1h)
                5: CourseClass(5, g1, c_dbms, p_cholke, 1, False), # DBMS Theory (1h)
                
                # TY/2 
                6: CourseClass(6, g2, c_mam, p_cholke, 2, True), # MAM Lab (2h)
                7: CourseClass(7, g2, c_os, p_joglekar, 1, False), # OS Theory (1h)
                8: CourseClass(8, g2, c_sp, p_joshi, 1, False),  # SP Theory (1h)
                9: CourseClass(9, g2, c_sp, p_joshi, 2, True), # SP Lab (2h)
                
                # SY/3 
                10: CourseClass(10, g3, c_daa, p_joglekar, 1, False), # DAA Theory (1h)
                11: CourseClass(11, g3, c_daa, p_joglekar, 1, False), # DAA Theory (1h)
                12: CourseClass(12, g3, c_sdam, p_sawant, 1, False), # SDAM Theory (1h)
                13: CourseClass(13, g3, c_sdam, p_sawant, 1, False), # SDAM Theory (1h)
                14: CourseClass(14, g3, c_oops, p_amune, 2, True), # OOPS Lab (2h)
                
                # SY/4 
                15: CourseClass(15, g4, c_dsa, p_kunekar, 1, False), # DSA Theory (1h)
                16: CourseClass(16, g4, c_dsa, p_kunekar, 2, True), # DSA Lab (2h)
                
                # *** FIX: CN Theory split into two 1-hour sessions ***
                17: CourseClass(17, g4, c_cn, p_deshpande, 1, False),# CN Theory (1h - Session 1)
                20: CourseClass(20, g4, c_cn, p_deshpande, 1, False),# CN Theory (1h - Session 2)
                
                18: CourseClass(18, g4, c_dt, p_sawant, 1, False), # DT Theory (1h)
                19: CourseClass(19, g4, c_dt, p_sawant, 1, False) # DT Theory (1h)
            }
            
            print("Configuration loaded successfully. The configuration is now using a hardcoded, clean data set.")
            
        except Exception as e:
            print(f"Error during configuration loading. Check your helper class definitions: {e}")
            raise # Re-raise the exception to stop execution

    # The GenerateCourseRequirementsTable method remains correct for tallying the provided data.
    def GenerateCourseRequirementsTable(self):
        """
        Generates data for the GUI's Session Tally table by AGGREGATING 
        requirements by (Group, Course, Type) and COUNTING sessions (occurrences).
        """
        aggregated_requirements = {}
        
        for class_id, cc in self._course_classes.items():
            group = cc.GetGroup()
            course = cc.GetCourse()
            professor = cc.GetProfessor()
            
            # Group name is the ID here (e.g., 'TY/1')
            group_name = group.GetName() 
            session_type = 'Lab' if cc.IsLabRequired() else 'Theory'
            
            # Use a tuple (Group Name, Course Name, Type) as the unique key
            # NOTE: We exclude Professor here to aggregate all sessions for a course/group/type.
            key = (group_name, course.GetName(), session_type)
            
            if key not in aggregated_requirements:
                # Use first part of the group name for 'Year' column (e.g., 'TY' or 'SY')
                year_name = group_name.split('/')[0] if '/' in group_name else group_name
                
                # Use the professor name from the *first* class found for this group/course/type
                # This is okay since professors are fixed for a course, but aggregation should be on the key without prof.
                aggregated_requirements[key] = {
                    'Year': year_name,
                    'Group': group_name,
                    'CourseName': course.GetName(),
                    'Professor': professor.GetName(), 
                    'Type': session_type,
                    'Required': 0, # Will count sessions
                    'Scheduled': 0 # Will be updated in GUI
                }
            
            # Count the session (1) for each CourseClass object
            aggregated_requirements[key]['Required'] += 1 
            
        # Re-format Scheduled/Status for initial display
        for key in aggregated_requirements:
             req = aggregated_requirements[key]['Required']
             aggregated_requirements[key]['Scheduled'] = 0 # Reset to 0 for initial GUI display
             aggregated_requirements[key]['Status'] = f"0/{req} Done"


        table_data = list(aggregated_requirements.values())
        return table_data
