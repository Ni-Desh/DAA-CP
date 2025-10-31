import random
from Configuration import Configuration as ConfigurationClass
import copy 
from collections import defaultdict

class Schedule:
    
    # Global Time Frame: 8:00 AM (Hour 8) to 6:00 PM (Hour 18 - exclusive)
    DAY_HOURS = 10 
    START_CLOCK_HOUR = 8 
    DAY_COUNT = 5 
    
    # Soft Constraint Weights
    PROF_LOAD_WEIGHT = 0.5
    GROUP_GAP_WEIGHT = 0.5 
    PROF_CONSECUTIVE_WEIGHT = 0.5 
    # NEW SOFT CONSTRAINT WEIGHTS
    LUNCH_BREAK_WEIGHT = 0.5 
    LATE_LONG_CLASS_WEIGHT = 0.5

    def __init__(self, crossover_points, mutation_size, crossover_prob, mutation_prob):
        self.config = ConfigurationClass.getInstance()
        self.crossover_points = crossover_points
        self.mutation_size = mutation_size
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        
        self.classes = {}
        self.fitness = 0.0
        # Initialize instance variables to hold raw penalties for debugging
        self.prof_penalty = 0
        self.gap_penalty = 0
        self.consecutive_penalty = 0
        # NEW SOFT CONSTRAINT PENALTIES
        self.lunch_penalty = 0 
        self.late_long_class_penalty = 0


    def MakeNewFromPrototype(self):
        new_schedule = Schedule(
            self.crossover_points, 
            self.mutation_size, 
            self.crossover_prob, 
            self.mutation_prob
        )
        
        num_rooms = self.config.GetNumberOfRooms()
        day_slots_total = num_rooms * self.DAY_HOURS
        
        for class_id, cc in self.config.GetCourseClasses().items():
            duration = cc.GetDuration()
            group = cc.GetGroup()

            # --- Calculate Valid Start Positions based on Group Time Window ---
            
            window_start_index = group.GetTimeWindowStart() - self.START_CLOCK_HOUR
            window_end_index = group.GetTimeWindowEnd() - self.START_CLOCK_HOUR 
            
            window_start_index = max(0, window_start_index)
            window_end_index = min(self.DAY_HOURS, window_end_index)
            
            max_start_hour_index = window_end_index - duration
            
            valid_start_positions = []
            
            if max_start_hour_index >= window_start_index:
                 for day in range(self.DAY_COUNT):
                     for room_index in range(num_rooms):
                         for start_hour in range(window_start_index, max_start_hour_index + 1):
                             pos = day * day_slots_total + room_index * self.DAY_HOURS + start_hour
                             valid_start_positions.append(pos)
            
            if valid_start_positions:
                new_schedule.classes[class_id] = random.choice(valid_start_positions)
            else:
                # Use slot 0 as a default invalid position if no valid slot exists
                new_schedule.classes[class_id] = 0 
                
        new_schedule.CalculateFitness()
        return new_schedule


    def CalculateFitness(self):
        config = self.config
        
        num_rooms = config.GetNumberOfRooms()
        num_days = self.DAY_COUNT
        num_hours = self.DAY_HOURS 
        day_slots = num_rooms * num_hours
        
        cloned_classes = config.GetCourseClasses()
        time_slot_map = [[] for _ in range(num_days * day_slots)]
        
        # Data structures for Soft Constraints
        prof_day_hours = defaultdict(lambda: defaultdict(int))
        group_day_slots = defaultdict(lambda: defaultdict(list))
        prof_consecutive_tracker = defaultdict(lambda: defaultdict(list))
        
        # Tracking for NEW Soft Constraints
        prof_is_teaching_lunch = defaultdict(lambda: defaultdict(bool))
        
        total_hard_score = 0
        # Hard constraint violation log is kept ONLY to calculate the ratio
        hard_constraint_violation_log = []
        
        # LUNCH SLOT: 12:00 PM (Start Clock Hour 8) -> Index 4 (8->0, 9->1, 10->2, 11->3, 12->4)
        LUNCH_SLOT_INDEX = 4 
        # LATE START: 3:00 PM (Start Clock Hour 8) -> Index 7 (8->0, ..., 15->7)
        LATE_START_THRESHOLD = 7 
        
        for class_id, start_pos in self.classes.items():
            cc = cloned_classes[class_id]
            duration = cc.GetDuration()
            initial_class_score = 5.0
            current_class_score = initial_class_score
            
            # Slot calculations
            day = start_pos // day_slots
            time_room = start_pos % day_slots
            room_index = time_room // num_hours
            start_time = time_room % num_hours
            
            room = config.GetRoomById(room_index) 
            group = cc.GetGroup()
            
            
            # --- Hard Constraint 1: Room Checks (Capacity and Type Mismatch) ---
            if room is None:
                current_class_score -= 5.0 
                hard_constraint_violation_log.append(f"CLASS {class_id}: FAILED HC1 - Room not assigned/found (pos={start_pos}).")
            elif room.GetNumberOfSeats() < group.GetNumberOfStudents():
                current_class_score -= 5.0 
                hard_constraint_violation_log.append(f"CLASS {class_id}: FAILED HC1 - Capacity mismatch (Req: {group.GetNumberOfStudents()}, Got: {room.GetNumberOfSeats()}).")
            elif cc.IsLabRequired() and not room.IsLab():
                current_class_score -= 5.0 
                hard_constraint_violation_log.append(f"CLASS {class_id}: FAILED HC1 - Lab required, but Room {room_index} is not a Lab.")
            elif room.IsLab() and not cc.IsLabRequired():
                current_class_score -= 5.0 
                hard_constraint_violation_log.append(f"CLASS {class_id}: FAILED HC1 - Lab not required, but Room {room_index} is a Lab (wasteful/penalty).")

            is_valid_time_boundary = True
            
            for i in range(duration):
                current_time = start_time + i
                
                # --- Hard Constraint 2a: Check Global 6 PM Boundary ---
                if current_time >= num_hours:
                    current_class_score -= 5.0
                    is_valid_time_boundary = False
                    hard_constraint_violation_log.append(f"CLASS {class_id}: FAILED HC2a - Runs past 6 PM boundary (Hour {current_time+self.START_CLOCK_HOUR}).")
                    break 

                # --- Hard Constraint 2b: Check Group Time Window ---
                window_start_index = group.GetTimeWindowStart() - self.START_CLOCK_HOUR
                window_end_index = group.GetTimeWindowEnd() - self.START_CLOCK_HOUR 
                if current_time < window_start_index or current_time >= window_end_index:
                    current_class_score -= 5.0 
                    is_valid_time_boundary = False 
                    hard_constraint_violation_log.append(f"CLASS {class_id}: FAILED HC2b - Outside Group Window (Day {day+1}, Hour {current_time+self.START_CLOCK_HOUR}).")
                    break
                
                # If valid so far, perform Overlap Checks and tracking for this hour slot
                if is_valid_time_boundary:
                    slot_index = day * day_slots + room_index * num_hours + current_time
                    
                    # --- Hard Constraint 4: Overlap Check ---
                    if slot_index < len(time_slot_map):
                        
                        for other_cc in time_slot_map[slot_index]: 
                            if cc.ProfessorOverlaps(other_cc):
                                current_class_score -= 5.0 
                                hard_constraint_violation_log.append(f"CLASS {class_id}: FAILED HC4 - Professor Overlap with {other_cc.GetId()} (Day {day+1}, Hour {current_time+self.START_CLOCK_HOUR}).")
                            if cc.GroupsOverlap(other_cc):
                                current_class_score -= 5.0 
                                hard_constraint_violation_log.append(f"CLASS {class_id}: FAILED HC4 - Group Overlap with {other_cc.GetId()} (Day {day+1}, Hour {current_time+self.START_CLOCK_HOUR}).")
                                
                        time_slot_map[slot_index].append(cc) 
                        
                        # Soft Constraint Tracking (Existing)
                        prof_day_hours[cc.GetProfessor().GetId()][day] += 1
                        group_day_slots[group.GetId()][day].append(current_time)
                        prof_consecutive_tracker[cc.GetProfessor().GetId()][day].append(current_time)
                        
                        # Soft Constraint Tracking (NEW SC4: Professor Lunch Break Preference)
                        if current_time == LUNCH_SLOT_INDEX:
                            prof_is_teaching_lunch[cc.GetProfessor().GetId()][day] = True
            
            # --- Hard Constraint 3: Professor Availability (Only needs to be checked at the start time) ---
            if not cc.GetProfessor().IsAvailable(day, start_time):
                current_class_score -= 5.0 
                hard_constraint_violation_log.append(f"CLASS {class_id}: FAILED HC3 - Professor is unavailable at start time (Day {day+1}, Hour {start_time+self.START_CLOCK_HOUR}).")
                
            # --- NEW SOFT CONSTRAINT 5: Minimize Long-Duration Classes Late in the Day ---
            if duration >= 3 and start_time >= LATE_START_THRESHOLD:
                self.late_long_class_penalty += 1
                
            # Cap score at 0 if multiple penalties occurred
            if current_class_score < 0:
                current_class_score = 0

            total_hard_score += current_class_score
        
        # --- SOFT CONSTRAINT CALCULATIONS ---
        
        # SC1 & SC2 & SC3 
        self.prof_penalty = sum((hours - 4) for day_data in prof_day_hours.values() for hours in day_data.values() if hours > 4)
        
        self.gap_penalty = 0
        for day_data in group_day_slots.values():
            for hours_list in day_data.values():
                if len(hours_list) > 1:
                    hours_list = sorted(list(set(hours_list)))
                    self.gap_penalty += sum(max(0, hours_list[i] - hours_list[i-1] - 2) for i in range(1, len(hours_list))) 

        self.consecutive_penalty = 0
        MAX_CONSECUTIVE_HOURS = 3
        
        for day_data in prof_consecutive_tracker.values():
            for hours_list in day_data.values():
                if not hours_list: continue
                sorted_hours = sorted(list(set(hours_list)))
                current_consecutive = 1
                for i in range(1, len(sorted_hours)):
                    if sorted_hours[i] == sorted_hours[i-1] + 1:
                        current_consecutive += 1
                    else:
                        self.consecutive_penalty += max(0, current_consecutive - MAX_CONSECUTIVE_HOURS)
                        current_consecutive = 1
                self.consecutive_penalty += max(0, current_consecutive - MAX_CONSECUTIVE_HOURS)
                
        # --- NEW SOFT CONSTRAINT 4: Professor Lunch Break Preference ---
        self.lunch_penalty = sum(1 for day_data in prof_is_teaching_lunch.values() for is_teaching in day_data.values() if is_teaching)
        
        # Scaling and Final Soft Score Calculation
        MAX_RAW_PENALTY = 10 
        
        scaled_prof_score = self.PROF_LOAD_WEIGHT * max(0, 1 - (self.prof_penalty / MAX_RAW_PENALTY))
        scaled_gap_score = self.GROUP_GAP_WEIGHT * max(0, 1 - (self.gap_penalty / MAX_RAW_PENALTY))
        scaled_consec_score = self.PROF_CONSECUTIVE_WEIGHT * max(0, 1 - (self.consecutive_penalty / MAX_RAW_PENALTY))
        # NEW SCALED SOFT SCORES
        scaled_lunch_score = self.LUNCH_BREAK_WEIGHT * max(0, 1 - (self.lunch_penalty / MAX_RAW_PENALTY))
        scaled_late_long_score = self.LATE_LONG_CLASS_WEIGHT * max(0, 1 - (self.late_long_class_penalty / MAX_RAW_PENALTY))
        
        total_soft_score = scaled_prof_score + scaled_gap_score + scaled_consec_score + scaled_lunch_score + scaled_late_long_score
        
        # --- FINAL FITNESS CALCULATION ---
        max_hard_score = len(config.GetCourseClasses()) * 5.0
        
        if max_hard_score == 0:
            self.fitness = 0.0
            return
            
        hard_ratio = total_hard_score / max_hard_score
            
        self.fitness = hard_ratio + total_soft_score
        
        # --- Print hard constraint score regardless of the ratio ---
        if self.fitness > 0: # Ensure we only print for actual schedules, not during initialization checks
             print(f"hard constraints fitness score={hard_ratio:.4f}")
             
             # Optionally, you can include the soft score, but I'll remove the soft penalty details
             # and just keep the Total Soft Score if you want minimal output.
             print(f"Total Soft Score: {total_soft_score:.4f}") 
             print("---------------------------------------------")


    def Crossover(self, other):
        offspring = self.copy() 
        class_ids = list(self.classes.keys())
        p1 = random.randrange(len(class_ids))
        p2 = random.randrange(len(class_ids))
        if p1 > p2: p1, p2 = p2, p1 
        for i in range(p1, p2):
            class_id = class_ids[i]
            offspring.classes[class_id] = other.classes[class_id]
        offspring.CalculateFitness()
        return offspring

    def Mutation(self):
        num_rooms = self.config.GetNumberOfRooms()
        day_slots_total = num_rooms * self.DAY_HOURS
        class_ids = list(self.classes.keys())
        if not class_ids: return

        classes_to_mutate = random.sample(class_ids, min(self.mutation_size, len(class_ids)))
        
        for class_id in classes_to_mutate:
            cc = self.config.GetCourseClasses()[class_id]
            duration = cc.GetDuration()
            group = cc.GetGroup()
            
            # Recalculate valid positions (Group Time Window)
            window_start_index = group.GetTimeWindowStart() - self.START_CLOCK_HOUR
            window_end_index = group.GetTimeWindowEnd() - self.START_CLOCK_HOUR
            
            window_start_index = max(0, window_start_index)
            window_end_index = min(self.DAY_HOURS, window_end_index)
            
            max_start_hour_index = window_end_index - duration 
            
            valid_start_positions = []
            if max_start_hour_index >= window_start_index:
                 for day in range(self.DAY_COUNT):
                     for room_index in range(num_rooms):
                         for start_hour in range(window_start_index, max_start_hour_index + 1):
                             pos = day * day_slots_total + room_index * self.DAY_HOURS + start_hour
                             valid_start_positions.append(pos)
            
            if valid_start_positions:
                self.classes[class_id] = random.choice(valid_start_positions)
            else:
                self.classes[class_id] = 0 

        self.CalculateFitness()

    def copy(self):
        return copy.deepcopy(self) 

    def __deepcopy__(self, memo):
        new_schedule = Schedule(
            self.crossover_points, 
            self.mutation_size, 
            self.crossover_prob, 
            self.mutation_prob
        )
        memo[id(self)] = new_schedule 
        new_schedule.classes = copy.deepcopy(self.classes, memo) 
        new_schedule.fitness = self.fitness
        new_schedule.prof_penalty = self.prof_penalty
        new_schedule.gap_penalty = self.gap_penalty
        new_schedule.consecutive_penalty = self.consecutive_penalty
        new_schedule.lunch_penalty = self.lunch_penalty
        new_schedule.late_long_class_penalty = self.late_long_class_penalty
        return new_schedule