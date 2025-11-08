class StudentsGroup:

    def __init__(self, id, name, numberOfStudents, timeWindowStart=8, timeWindowEnd=18):
        self.id = id
        self.name = name
        self.numberOfStudents = int(numberOfStudents)
        
        # --- NEW: Group Time Window Fields ---
        self._timeWindowStart = timeWindowStart
        self._timeWindowEnd = timeWindowEnd
        # ------------------------------------
        
        self.courseClasses = []
        
    def AddClass(self, courseClass):
        self.courseClasses.append(courseClass)

    def GetId(self):
        return self.id

    def GetName(self):
        return str(self.name)

    def GetNumberOfStudents(self):
        return self.numberOfStudents

    def GetCourseClasses(self):
        return self.courseClasses
        
    # --- NEW: Group Time Window Getters ---
    def GetTimeWindowStart(self):
        """Returns the clock hour the group can start classes (e.g., 9 for 9 AM)."""
        return self._timeWindowStart

    def GetTimeWindowEnd(self):
        """Returns the clock hour the group must finish classes (e.g., 17 for 5 PM)."""
        return self._timeWindowEnd
    # ------------------------------------

    def __eq__(self, rhs):
        if isinstance(rhs, StudentsGroup):
            return self.id == rhs.id
        return False
