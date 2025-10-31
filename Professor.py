class Professor:
    nextProfessorId = 0 # Added for consistency

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.courseClasses = []
        # New Feature: Store unavailable time slots as a set of (day, hour) tuples
        self.unavailableSlots = set()

    def GetId(self):
        return self.id

    def GetName(self):
        return self.name

    def AddCourseClass(self, courseClass):
        self.courseClasses.append(courseClass)

    def GetCourseClasses(self):
        return self.courseClasses
    
    # New Feature: Add an unavailable slot (Used by Configuration)
    def AddUnavailableSlot(self, day, hour):
        self.unavailableSlots.add((day, hour))

    # New Feature: Checks if professor is available at a specific (day, hour)
    def IsAvailable(self, day, hour):
        return (day, hour) not in self.unavailableSlots
    
    @staticmethod
    def RestartIDs():
        Professor.nextProfessorId = 0 
    
    def __eq__(self, rhs):
        if isinstance(rhs, Professor):
            return self.id == rhs.id
        return False