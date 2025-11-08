# Algorithm.py

import Configuration
from Schedule import Schedule
from Configuration import Configuration as ConfigurationClass
import random
import copy 
import sys 

class Algorithm:

    def __init__(self, config):
        # --- AGGRESSIVE PARAMETERS (Optimized for Exploration) ---
        self.POP_SIZE = 250              
        self.MAX_GENERATIONS = 500       # Increased for deeper search to find 1.0 Hard Ratio
        self.CROSSOVER_POINTS = 2
        self.MUTATION_SIZE = 8           
        self.CROSSOVER_PROB = 0.85
        self.MUTATION_PROB = 0.80        
        # -----------------------------------------------------------
        
        self.config = config
        self.population = []
        self.bestSchedule = None 
        
        # Ensure Schedule class has necessary constants or assume defaults 
        if not hasattr(Schedule, 'DAY_HOURS'):
             Schedule.DAY_HOURS = 10 
        if not hasattr(Schedule, 'START_CLOCK_HOUR'):
             Schedule.START_CLOCK_HOUR = 8 
        if not hasattr(Schedule, 'DAYS_PER_WEEK'):
             Schedule.DAYS_PER_WEEK = 5 

        # self._debug_config_check() was removed to clean up startup output

        self._initialize_population()
        
    # The _debug_config_check method has been removed.

    def _initialize_population(self):
        
        prototype = Schedule(
            self.CROSSOVER_POINTS, 
            self.MUTATION_SIZE, 
            self.CROSSOVER_PROB, 
            self.MUTATION_PROB
        )

        for _ in range(self.POP_SIZE):
            new_schedule = prototype.MakeNewFromPrototype()
            self.population.append(new_schedule)

        self._evaluate_population()

    def _evaluate_population(self):
        for schedule in self.population:
            schedule.CalculateFitness() 
            
            if self.bestSchedule is None or schedule.fitness > self.bestSchedule.fitness:
                self.bestSchedule = copy.deepcopy(schedule)


    def Crossover(self, parent1, parent2):
        return parent1.Crossover(parent2)

    def Mutation(self, schedule):
        schedule.Mutation()

    def Run(self):
        
        GOAL_FITNESS = 4.4 
        
        print("--- Starting Genetic Algorithm ---")
        

        for generation in range(1, self.MAX_GENERATIONS + 1):
            
            self.population.sort(key=lambda s: s.fitness, reverse=True)
            
            # Elitism: Keep the top 10%
            elite_count = int(self.POP_SIZE * 0.1)
            new_population = self.population[:elite_count] 

            while len(new_population) < self.POP_SIZE:
                
                # Truncation Selection: Select parents from the top 50%
                selection_pool = self.population[:self.POP_SIZE // 2]
                if not selection_pool: 
                    break
                    
                parent1 = random.choice(selection_pool)
                parent2 = random.choice(selection_pool)

                offspring = parent1.copy() 
                if random.random() < self.CROSSOVER_PROB:
                    offspring = self.Crossover(parent1, parent2)
                
                if random.random() < self.MUTATION_PROB:
                    self.Mutation(offspring)
                        
                offspring.CalculateFitness() 
                new_population.append(offspring)

            self.population = new_population
            self._evaluate_population() 
            
            # Print generation status
            print(f"Generation {generation}: Fittest Score = {self.bestSchedule.fitness:.4f}")

            if self.bestSchedule.fitness >= GOAL_FITNESS: 
                     print("\n--- Goal Schedule Found! ---")
                     self._print_best_schedule()
                     return copy.deepcopy(self.bestSchedule)


        print("\n--- Algorithm Finished (Max Generations Reached) ---")
        self.bestSchedule.CalculateFitness() 
        self._print_best_schedule()
        
        return copy.deepcopy(self.bestSchedule)


    def _print_best_schedule(self):
        if self.bestSchedule is None:
            print("No schedule found.")
            return

        # Ensure fitness calculation (and thus hard_ratio storage) is done once
        self.bestSchedule.CalculateFitness() 
        
        print(f"\n--- Final Best Timetable (Fitness: {self.bestSchedule.fitness:.4f}) ---")
        
        # PRINT THE FINAL HARD CONSTRAINT SCORE
        print(f"Hard Constraint Score (Ratio): {self.bestSchedule.hard_ratio:.4f} ({self.bestSchedule.total_hard_score:.1f}/{self.bestSchedule.max_hard_score:.1f})")
        print("------------------------------------------------------------------")
        
        rooms = list(self.config.GetRooms().values()) 
        num_rooms = self.config.GetNumberOfRooms()
        
        DAY_HOURS = Schedule.DAY_HOURS
        START_HOUR = Schedule.START_CLOCK_HOUR 
        DAYS_PER_WEEK = Schedule.DAYS_PER_WEEK
        
        daySize = num_rooms * DAY_HOURS
        
        if num_rooms == 0 or daySize == 0:
            print("Cannot print schedule: No rooms or time slots available.")
            return
            
        sorted_classes = sorted(self.bestSchedule.classes.items(), key=lambda item: item[1])
        
        for class_id, pos in sorted_classes:
            cc = self.config.GetCourseClasses().get(class_id)
            if not cc: continue
            
            day = pos // daySize
            time_room = pos % daySize
            
            if DAY_HOURS == 0: continue
            room_index = time_room // DAY_HOURS
            time = time_room % DAY_HOURS
            
            if room_index < len(rooms):
                room = rooms[room_index]
            else:
                continue 
            
            day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day % DAYS_PER_WEEK]
            start_clock_hour = START_HOUR + time
            
            if start_clock_hour >= 12 and start_clock_hour < 13:
                time_display = "12:00 PM"
            elif start_clock_hour >= 13:
                time_display = f"{start_clock_hour - 12}:00 PM"
            else:
                time_display = f"{start_clock_hour}:00 AM"

            class_type = " (Lab)" if cc.IsLabRequired() else " (Theory)"
            
            print(f"[{day_name}, {time_display}] R:{room.GetName()} | {cc.GetCourse().GetName()}{class_type} for {cc.GetGroup().GetName()} (Prof: {cc.GetProfessor().GetName()}, Duration: {cc.GetDuration()})")


# --- Main Execution Block ---

if __name__ == "__main__":
    
    try:
        filename = 'input.cfg'
        # Instantiate ConfigurationClass. 
        config = ConfigurationClass(filename) 
        
        # We assume the constructor handles reading the file.
        
        ga = Algorithm(config)
        ga.Run() 
        
    except FileNotFoundError:
        print(f"Error: {filename} not found. Make sure it's in the correct directory.")
    except Exception as e:
        print(f"\nCRITICAL CRASH ERROR: The genetic algorithm failed. Details: {e}")
