class Course:

    def __init__(self, id, name):
        self.id = id
        self.name = name
    
    def GetId(self):
        return self.id

    def GetName(self):
        return self.name

    def __eq__(self, rhs):
        if isinstance(rhs, Course):
            return self.id == rhs.id
        return False
