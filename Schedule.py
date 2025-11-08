# Schedule.py

import random
from Configuration import Configuration as ConfigurationClass
import copy 
from collections import defaultdict
import sys 

class Schedule:
    
    # Constants required by Algorithm.py
    DAY_HOURS = 10  # 8:00 AM to 6:00 PM (10 slots)
    START_CLOCK_HOUR = 8  # Start time 8 AM
    DAYS_PER_WEEK = 5 # Monday to Friday
    
    # Soft Constraint Weights
    PROF_LOAD_WEIGHT = 0.5
    GROUP_GAP_WEIGHT = 0.5 
    PROF_CONSECUTIVE_WEIGHT = 0.5 
    LUNCH_BREAK_WEIGHT = 0.5 
    LATE_LONG_CLASS_WEIGHT = 0.5
    SAME_SUBJECT_CONSECUTIVE_WEIGHT = 1.0 
    
    # --- Class Initialization ---
    def __init__(self, crossover_points, mutation_size, crossover_prob, mutation_prob):
        
        try:
            self.config = ConfigurationClass.getInstance()
        except Exception:
            print("CRITICAL: Configuration is not initialized before Schedule.")
            sys.exit(1)
            
        self.crossover_points = crossover_points
        self.mutation_size = mutation_size
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        
        # 'classes' maps CourseClass ID to its starting position (pos) in the timetable array
        self.classes = {}
        self.fitness = 0.0
        
        # Hard Constraint Metrics
        self.hard_ratio = 0.0
        self.total_hard_score = 0.0
        self.max_hard_score = 0.0
        
        # Penalties reset
        self.prof_penalty = 0
        self.gap_penalty = 0
        self.consecutive_penalty = 0
        self.lunch_penalty = 0 
        self.late_long_class_penalty = 0
        self.same_subject_consecutive_penalty = 0

    # --- Core GA Methods ---

    def copy(self):
        """Creates a shallow copy of the Schedule."""
        new_schedule = Schedule(self.crossover_points, self.mutation_size, self.crossover_prob, self.mutation_prob)
        new_schedule.classes = self.classes.copy() 
        new_schedule.fitness = self.fitness
        new_schedule.hard_ratio = self.hard_ratio
        new_schedule.total_hard_score = self.total_hard_score
        new_schedule.max_hard_score = self.max_hard_score
        return new_schedule
        
    def __deepcopy__(self, memo):
        """Creates a deep copy for use with copy.deepcopy"""
        new_schedule = Schedule(self.crossover_points, self.mutation_size, self.crossover_prob, self.mutation_prob)
        new_schedule.classes = self.classes.copy()
        new_schedule.fitness = self.fitness
        new_schedule.hard_ratio = self.hard_ratio
        new_schedule.total_hard_score = self.total_hard_score
        new_schedule.max_hard_score = self.max_hard_score
        return new_schedule
        
    def _get_compatible_rooms(self, cc):
        """Helper to filter rooms based on Lab/Theory requirement and capacity."""
        compatible_rooms = []
        for room_id, room in self.config.GetRooms().items():
            # HC3 Check: Lab required matches room type, AND HC1 Check: Capacity is sufficient
            if cc.IsLabRequired() == room.IsLab() and cc.GetGroup().GetSize() <= room.GetSize():
                compatible_rooms.append(room_id)
        return compatible_rooms


    def MakeNewFromPrototype(self):
        """Initializes a new schedule with a random valid placement for all classes, respecting HC3 and HC1."""
        new_schedule = self.copy() # Start with an empty copy
        
        num_hours = self.DAY_HOURS
        num_days = self.DAYS_PER_WEEK
        new_schedule.classes = {} 

        for class_id, cc in self.config.GetCourseClasses().items():
            duration = cc.GetDuration()
            
            # --- NEW LOGIC: Filter compatible rooms first ---
            compatible_room_ids = self._get_compatible_rooms(cc)
            
            if not compatible_room_ids:
                 # If no room is compatible (e.g., all too small), assign 0 and let HC1 or HC3 penalize it
                 new_schedule.classes[class_id] = 0
                 continue
            
            # 1. Select a random compatible room index
            room_id = random.choice(compatible_room_ids)
            # This is the INDEX of the selected room among ALL rooms (0 to N-1)
            room_index = list(self.config.GetRooms().keys()).index(room_id) 

            # 2. Determine max possible time index a class can *start* at
            max_start_time_index = num_hours - duration
            if max_start_time_index < 0:
                 # Class is too long for the day, let HC2 penalize it, but assign a default pos
                 max_start_time_index = 0

            # 3. Choose a random day (0 to DAYS_PER_WEEK-1) and start time (0 to max_start_time_index)
            random_day = random.randrange(num_days)
            random_time = random.randrange(max_start_time_index + 1)
            
            # Total slots per day (Num_Rooms * Num_Hours)
            day_slots = self.config.GetNumberOfRooms() * num_hours
            
            # Calculate the final position: (Day * Slots_Per_Day) + (Room_Index * Num_Hours) + Time_Index
            random_pos = (random_day * day_slots) + (room_index * num_hours) + random_time
            
            new_schedule.classes[class_id] = random_pos

        return new_schedule


    def Crossover(self, parent2):
        """Performs multi-point crossover."""
        child = self.copy()
        
        class_ids = list(child.classes.keys())
        random.shuffle(class_ids)
        
        split_points = sorted(random.sample(range(len(class_ids)), self.crossover_points))
        
        use_parent2 = False
        for i, class_id in enumerate(class_ids):
            if i in split_points:
                use_parent2 = not use_parent2
            
            if use_parent2:
                if class_id in parent2.classes:
                    child.classes[class_id] = parent2.classes[class_id]
        
        return child

    def Mutation(self):
        """Performs simple random class reassignment mutation, respecting HC3 and HC1."""
        num_hours = self.DAY_HOURS
        num_days = self.DAYS_PER_WEEK
        day_slots = self.config.GetNumberOfRooms() * num_hours
        
        class_ids = list(self.classes.keys())
        if not class_ids: return

        for class_id in random.sample(class_ids, min(self.mutation_size, len(class_ids))):
            cc = self.config.GetCourseClasses()[class_id]
            duration = cc.GetDuration()
            
            # --- NEW LOGIC: Filter compatible rooms first ---
            compatible_room_ids = self._get_compatible_rooms(cc)
            
            if not compatible_room_ids:
                 # Cannot place this class anywhere valid due to capacity/type. Leave it to be penalized.
                 continue

            # 1. Select a random compatible room index
            room_id = random.choice(compatible_room_ids)
            room_index = list(self.config.GetRooms().keys()).index(room_id) 

            # 2. Determine max possible time index
            max_start_time_index = num_hours - duration
            if max_start_time_index < 0:
                 max_start_time_index = 0

            # 3. Choose a random day and start time
            random_day = random.randrange(num_days)
            random_time = random.randrange(max_start_time_index + 1)
            
            # Calculate the final position
            random_pos = (random_day * day_slots) + (room_index * num_hours) + random_time
            
            self.classes[class_id] = random_pos


    # --- Fitness Calculation ---
    def CalculateFitness(self):
        config = self.config
        
        # Constants
        num_rooms = config.GetNumberOfRooms()
        num_days = self.DAYS_PER_WEEK
        num_hours = self.DAY_HOURS 
        day_slots = num_rooms * num_hours
        cloned_classes = config.GetCourseClasses()
        
        slot_map = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))
        
        # Trackers for Soft Constraints
        prof_day_hours = defaultdict(lambda: defaultdict(int))
        group_day_slots = defaultdict(lambda: defaultdict(list)) 
        prof_consecutive_tracker = defaultdict(lambda: defaultdict(list)) 
        
        # Penalties reset
        self.prof_penalty = 0
        self.gap_penalty = 0
        self.consecutive_penalty = 0
        self.lunch_penalty = 0 
        self.late_long_class_penalty = 0
        self.same_subject_consecutive_penalty = 0

        total_hard_score = 0
        LUNCH_SLOT_INDEX = 4 
        LATE_START_HOUR_INDEX = 7 
        
        
        # --- HARD CONSTRAINT CHECKING AND SOFT CONSTRAINT TRACKING LOOP ---
        for class_id, start_pos in self.classes.items():
            cc = cloned_classes[class_id]
            duration = cc.GetDuration()
            current_class_score = 5.0
            
            day = start_pos // day_slots
            time_room = start_pos % day_slots
            room_index = time_room // num_hours
            start_time = time_room % num_hours
            
            room_id = room_index
            room = config.GetRooms().get(room_id)
            group = cc.GetGroup()
            
            failure_reason = ""
            
            # HC1: Room Check - ensures room exists and capacity
            if room is None or group.GetSize() > room.GetSize():
                 current_class_score = 0.0
                 failure_reason = "HC1: Room/Capacity Mismatch"
                 # DEBUG REMOVED: if self.hard_ratio < 1.0 and failure_reason: print(...)
                 continue
                 
            # HC3: Lab Check - only lab classes in lab rooms, only theory in theory rooms
            if cc.IsLabRequired() != room.IsLab():
                 current_class_score = 0.0
                 failure_reason = "HC3: Lab/Theory Mismatch"
                 # DEBUG REMOVED: if self.hard_ratio < 1.0 and failure_reason: print(...)
                 continue
                 
            # --- HC2 & HC4: Time Overlap/Boundary Check (Pre-check) ---
            is_valid_placement = True 
            
            # HC2 Time Boundary Check (Class runs off the end of the day)
            if start_time + duration > num_hours:
                is_valid_placement = False
                failure_reason = "HC2: Time Boundary (End of Day)"
                
            # HC2 Time Window Check (outside the group's availability)
            window_start_index = group.GetAvailableStartTime() - self.START_CLOCK_HOUR
            window_end_index = group.GetAvailableEndTime() - self.START_CLOCK_HOUR 
            if start_time < window_start_index or start_time + duration > window_end_index:
                is_valid_placement = False
                failure_reason = "HC2: Group Time Window"
                
            if not is_valid_placement:
                current_class_score = 0.0 
                # DEBUG REMOVED: if self.hard_ratio < 1.0 and failure_reason: print(...)
                continue


            # Check overlaps for all slots in the duration
            for i in range(duration):
                current_time = start_time + i
                
                # Check Overlap (Room, Professor, Group)
                if day < num_days and current_time < num_hours:
                    
                    # 1. Room Overlap Check
                    if slot_map[day][current_time][room_id] is not None:
                         current_class_score = 0.0
                         failure_reason = "HC4: Room Overlap"
                         break 
                        
                    # 2. Professor and Group Overlap Check
                    for other_room_id, other_cc in slot_map[day][current_time].items():
                         if other_cc is None: continue
                         
                         if cc.GetProfessor().GetId() == other_cc.GetProfessor().GetId():
                              current_class_score = 0.0
                              failure_reason = "HC4: Professor Overlap"
                              break 
                         
                         if cc.GetGroup().GetId() == other_cc.GetGroup().GetId():
                              current_class_score = 0.0
                              failure_reason = "HC4: Group Overlap"
                              break 
                            
                    if current_class_score == 0.0: break 
                    
                    # If valid, book the slot for soft constraint tracking
                    slot_map[day][current_time][room_id] = cc
                    
                    # Soft Constraint Tracking (Only for valid slots)
                    prof_day_hours[cc.GetProfessor().GetId()][day] += 1
                    group_day_slots[group.GetId()][day].append(current_time)
                    prof_consecutive_tracker[cc.GetProfessor().GetId()][day].append(current_time)
                    
                    # SC4: Lunch Break Penalty
                    if current_time == LUNCH_SLOT_INDEX:
                         self.lunch_penalty += 1 
                        
                    # SC5: Late Long Class Penalty (Applied only to the START of the class)
                    if i == 0 and start_time >= LATE_START_HOUR_INDEX and duration > 1:
                         self.late_long_class_penalty += 1
                
            # If the class passed all hard checks for its entire duration:
            if current_class_score > 0.0:
                 total_hard_score += 5.0
            else:
                 total_hard_score += 0.0 
                 # DEBUG REMOVED: if self.hard_ratio < 1.0 and failure_reason: print(...)

        # --- SOFT CONSTRAINT CALCULATIONS (Post-processing) ---
        
        # SC1: Penalize Professor Overload (> 5 hours/day)
        for prof_id, days in prof_day_hours.items():
            for day, hours in days.items():
                if hours > 5:
                    self.prof_penalty += (hours - 5)
                    
        # SC2: Penalize Group Gaps (Large gaps between classes)
        for group_id, days in group_day_slots.items():
            for day, slots in days.items():
                if len(slots) > 1:
                    slots.sort()
                    for i in range(len(slots) - 1):
                        gap = slots[i+1] - slots[i]
                        if gap > 1:
                            self.gap_penalty += (gap - 1)
                            
        # SC3: Penalize Professor Consecutive Classes (More than 3 consecutive)
        for prof_id, days in prof_consecutive_tracker.items():
            for day, slots in days.items():
                slots.sort()
                consecutive_count = 0
                if slots:
                    consecutive_count = 1
                    for i in range(len(slots) - 1):
                        if slots[i+1] == slots[i] + 1:
                            consecutive_count += 1
                        else:
                            consecutive_count = 1
                            
                        if consecutive_count > 3:
                            self.consecutive_penalty += 1
        
        # SC6: Penalize same-subject/group consecutive THEORY classes (1-hour sessions only)
        for day in range(num_days):
             for time_index in range(num_hours - 1): 
                 current_slot_classes = [slot_map[day][time_index][r_id] for r_id in slot_map[day][time_index] if slot_map[day][time_index][r_id]]
                 next_slot_classes = [slot_map[day][time_index + 1][r_id] for r_id in slot_map[day][time_index + 1] if slot_map[day][time_index + 1][r_id]]

                 for current_cc in current_slot_classes:
                      if current_cc.IsLabRequired() or current_cc.GetDuration() != 1: 
                           continue
                          
                      current_group_id = current_cc.GetGroup().GetId()
                      current_course_id = current_cc.GetCourse().GetId()
                          
                      for next_cc in next_slot_classes:
                           if next_cc.IsLabRequired() or next_cc.GetDuration() != 1:
                               continue
                               
                           if (next_cc.GetGroup().GetId() == current_group_id and 
                               next_cc.GetCourse().GetId() == current_course_id):
                               self.same_subject_consecutive_penalty += 1

        # --- FINAL FITNESS CALCULATION ---
        
        MAX_RAW_PENALTY = 10 
        
        scaled_prof_score = self.PROF_LOAD_WEIGHT * max(0, 1 - (self.prof_penalty / MAX_RAW_PENALTY))
        scaled_gap_score = self.GROUP_GAP_WEIGHT * max(0, 1 - (self.gap_penalty / MAX_RAW_PENALTY))
        scaled_consec_score = self.PROF_CONSECUTIVE_WEIGHT * max(0, 1 - (self.consecutive_penalty / MAX_RAW_PENALTY))
        scaled_lunch_score = self.LUNCH_BREAK_WEIGHT * max(0, 1 - (self.lunch_penalty / MAX_RAW_PENALTY))
        scaled_late_long_score = self.LATE_LONG_CLASS_WEIGHT * max(0, 1 - (self.late_long_class_penalty / MAX_RAW_PENALTY))
        scaled_same_subject_consec_score = self.SAME_SUBJECT_CONSECUTIVE_WEIGHT * max(0, 1 - (self.same_subject_consecutive_penalty / MAX_RAW_PENALTY))
        
        total_soft_score = (scaled_prof_score + scaled_gap_score + scaled_consec_score + 
                             scaled_lunch_score + scaled_late_long_score + scaled_same_subject_consec_score)
        
        # Hard Score Normalization
        max_hard_score = len(config.GetCourseClasses()) * 5.0
        
        if max_hard_score == 0:
            self.fitness = 0.0
            self.hard_ratio = 0.0
            self.total_hard_score = 0.0
            self.max_hard_score = 0.0
            return
            
        hard_ratio = total_hard_score / max_hard_score
        
        # Store hard constraint metrics
        self.hard_ratio = hard_ratio
        self.total_hard_score = total_hard_score
        self.max_hard_score = max_hard_score
        
        self.fitness = hard_ratio + total_soft_score
