# CourseClass.py (FINAL Corrected Code)
import Course
import Professor
import StudentsGroup

class CourseClass:
    
    nextClassId = 0
    
    def __init__(self, professor, course, duration, group, lab_required=False):
        self.id = CourseClass.nextClassId
        self.professor = professor
        self.course = course
        self.duration = int(duration)
        self.group = group
        self.lab_required = lab_required
        
        CourseClass.nextClassId += 1

    def GetId(self):
        return self.id

    def GetCourse(self):
        return self.course

    def GetProfessor(self):
        return self.professor

    def GetGroup(self):
        return self.group

    def GetDuration(self):
        return self.duration

    def IsLabRequired(self):
        return self.lab_required

    @staticmethod
    def RestartIDs():
        CourseClass.nextClassId = 0

    # CRITICAL LOGIC CHECK 1: Professor Overlap
    def ProfessorOverlaps(self, other_cc):
        """Checks if two CourseClasses have the same professor."""
        # They overlap if their professor objects have the same ID
        if self.professor.GetId() == other_cc.GetProfessor().GetId():
            return True
        return False
        
    # CRITICAL LOGIC CHECK 2: Group Overlap
    def GroupsOverlap(self, other_cc):
        """Checks if two CourseClasses have the same student group."""
        # They overlap if their student group objects have the same ID
        if self.group.GetId() == other_cc.GetGroup().GetId():
            return True
        return False

    def __eq__(self, rhs):
        if isinstance(rhs, CourseClass):
            return self.id == rhs.id
        return False
        
    def __ne__(self, rhs):
        return not self.__eq__(rhs)