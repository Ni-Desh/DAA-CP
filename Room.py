# Room.py (FINAL Definitive Code - Robust ID Management)

class Room:
    
    nextRoomId = 0

    def __init__(self, name, lab, numberOfSeats):
        # Assign the sequential ID from the class counter (0, 1, 2, ...)
        self.id = Room.nextRoomId

        self.name = name
        
        # Robust check for 'lab' property (handles 'true', '1', 'false', '0', etc.)
        if str(lab).lower() in ['true', '1']:
            self.lab = True
        else:
            self.lab = False
        
        # Ensure seats is an integer
        self.numberOfSeats = int(numberOfSeats)
        
        # Increment the counter for the next room
        Room.nextRoomId = Room.nextRoomId + 1

    def GetId(self):
        return self.id

    def GetName(self):
        return self.name

    def IsLab(self):
        return self.lab

    def GetNumberOfSeats(self):
        return self.numberOfSeats

    @staticmethod
    def RestartIDs():
        # CRITICAL: Ensures the counter is reset before reading a new config file
        Room.nextRoomId = 0
        
    def __eq__(self, rhs):
        if isinstance(rhs, Room):
            return self.id == rhs.id
        return False
        
    def __ne__(self, rhs):
        return not self.__eq__(rhs)