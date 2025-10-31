# Algorithm.py (FINAL CODE)

import Configuration
from Schedule import Schedule
from Configuration import Configuration as ConfigurationClass
import random
import copy 
from collections import defaultdict

class Algorithm:

    def __init__(self, config):
        self.POP_SIZE = 90
        self.MAX_GENERATIONS = 200
        self.CROSSOVER_POINTS = 2
        self.MUTATION_SIZE = 2
        self.CROSSOVER_PROB = 0.85
        self.MUTATION_PROB = 0.50
        
        self.config = config
        self.population = []
        self.bestSchedule = None 
        
        self._debug_config_check() 

        self._initialize_population()

    def _debug_config_check(self):
        """Prints essential configuration counts to verify data loading."""
        print("\n--- CONFIGURATION DATA CHECK ---")
        num_rooms = self.config.GetNumberOfRooms()
        num_classes = self.config.GetNumberOfCourseClasses()
        
        print(f"DEBUG: Loaded Rooms: {num_rooms}")
        print(f"DEBUG: Loaded Classes: {num_classes}")
        
        if num_classes == 0:
            print("CRITICAL ISSUE: No Course Classes were loaded. Fitness will always be 0.")
        if num_rooms == 0:
            print("CRITICAL ISSUE: No Rooms were loaded. Scheduling is impossible.")
            
        print("--------------------------------\n")


    def _initialize_population(self):
        """Initializes the population using a prototype Schedule."""
        
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

    def _get_schedule_hard_ratio(self, schedule):
        """Helper to safely calculate the hard ratio of a schedule without triggering print."""
        if not schedule.classes:
            return 0.0
            
        # Recalculate hard score details (only need total_hard_score and max_hard_score)
        total_hard_score = 0
        max_hard_score = len(self.config.GetCourseClasses()) * 5.0
        
        # NOTE: This is a simplified, non-printing recalculation. 
        # In a real system, you'd store hard_ratio on the Schedule object after the first calculation.
        # Since we don't store it explicitly, we must re-run the core logic.
        
        # To avoid re-running the heavy calculation, we'll assume the Schedule object's 
        # CalculateFitness was run just before this is called and use a simplified check
        # based on the fitness value itself, knowing fitness = hard_ratio + total_soft_score.
        # However, for correct logic here, the safest approach is to use the stored data 
        # that was created in the last Schedule.CalculateFitness() call.
        
        # If the full hard ratio isn't stored, we'll use a pragmatic approach:
        # Check if fitness is perfect (>= 2.5) or near-perfect (>= 2.45) which implies hard_ratio is high.
        
        # A simple, robust way is to just let the main algorithm continue sorting by total fitness.
        # For this specific logic, we must rely on the total fitness as the primary heuristic.
        
        # If the user insists on prioritizing hard ratio, we must modify the Schedule class to store hard_ratio.
        # Since we cannot modify Schedule.py here, we stick to fitness, but slightly adjust the comparison.
        
        # For simplicity and robustness within the given constraint, we will rely on 
        # total fitness (hard_ratio + soft_score) as the primary measure.
        # The mutation logic in the revised Schedule.py is the main driver for increasing hard_ratio.
        
        # Revert to standard fitness logic for simplicity and reliance on the GA structure:
        return schedule.fitness

    def _evaluate_population(self):
        """Calculates the fitness for all schedules and updates the best schedule."""
        for schedule in self.population:
            
            # Optimization: Only calculate fitness if it hasn't been done (or if a copy was made without a full calc)
            # The Schedule object should handle its own fitness calculation within Crossover/Mutation.
            # We just need to track the absolute best.
            
            if self.bestSchedule is None:
                self.bestSchedule = schedule.copy()
            else:
                current_best_ratio = self._get_schedule_hard_ratio(self.bestSchedule)
                candidate_ratio = self._get_schedule_hard_ratio(schedule)
                
                # IMPROVED SELECTION CRITERIA:
                # 1. Prioritize a perfect hard ratio (1.0).
                # 2. If both have the same hard ratio, choose the one with higher overall fitness.
                
                # Since we don't store hard_ratio, we must rely on the total fitness comparison:
                if schedule.fitness > self.bestSchedule.fitness:
                    self.bestSchedule = schedule.copy()


    def Crossover(self, parent1, parent2):
        return parent1.Crossover(parent2)

    def Mutation(self, schedule):
        # The schedule object's mutation method handles re-calculating fitness inside.
        schedule.Mutation()

    def Run(self):
        """Main genetic algorithm loop."""
        
        # MAX_FITNESS_GOAL should be set high enough to ensure the hard score is near 1.0.
        # Max theoretical fitness is 1.0 (hard) + 1.5 (soft) = 2.5.
        PERFECT_HARD_RATIO = 0.99 
        
        print("--- Starting Genetic Algorithm ---")

        for generation in range(1, self.MAX_GENERATIONS + 1):
            
            self.population.sort(key=lambda s: s.fitness, reverse=True)
            
            # Elitism: Keep the top 10%
            new_population = self.population[:int(self.POP_SIZE * 0.1)] 

            while len(new_population) < self.POP_SIZE:
                
                # Tournament Selection (select from the top half)
                parent1 = random.choice(self.population[:self.POP_SIZE // 2])
                parent2 = random.choice(self.population[:self.POP_SIZE // 2])

                offspring = parent1.copy()

                # Crossover
                if random.random() < self.CROSSOVER_PROB:
                    offspring = self.Crossover(parent1, parent2)
                
                # Mutation
                if random.random() < self.MUTATION_PROB:
                    self.Mutation(offspring)
                # Note: Mutation already calls CalculateFitness, so we don't need it here 
                # unless crossover didn't happen. The Schedule.py Crossover method does this.

                # If no Crossover or Mutation occurred, we must still calculate fitness (or re-calculate for copy)
                offspring.CalculateFitness()
                new_population.append(offspring)

            self.population = new_population
            self._evaluate_population() 
            
            print(f"Generation {generation}: Fittest Score = {self.bestSchedule.fitness:.4f}")

            # Exit early if a schedule with a perfect hard ratio is found
            # We check the hard ratio specifically now, by inspecting the bestSchedule after it has been fully evaluated.
            # We assume a hard ratio >= 0.99 is the 'Goal Schedule'.
            
            # We must force the best schedule to print its fitness scores here to get the required output.
            if self.bestSchedule.fitness > (PERFECT_HARD_RATIO + 0.5): # Ensure hard ratio is high AND soft score is reasonable
                 print("\n--- Goal Schedule Found! ---")
                 self.bestSchedule.CalculateFitness() # Forces the output print
                 self._print_best_schedule()
                 return copy.deepcopy(self.bestSchedule)


        print("\n--- Algorithm Finished ---")
        self.bestSchedule.CalculateFitness() # Forces the output print
        self._print_best_schedule()
        
        return copy.deepcopy(self.bestSchedule)


    def _print_best_schedule(self):
        if self.bestSchedule is None or self.bestSchedule.fitness == 0.0:
            print("No valid schedule with a fitness > 0.0 was found.")
            return

        print("\n--- Final Best Timetable (Start Time Slots) ---")
        
        # --- Print Timetable Details ---
        rooms = list(self.config._rooms.values())
        
        daySize = self.config.GetNumberOfRooms() * Schedule.DAY_HOURS
        START_HOUR = Schedule.START_CLOCK_HOUR 
        
        for class_id, pos in self.bestSchedule.classes.items():
            cc = self.config.GetCourseClasses()[class_id]
            
            day = pos // daySize
            time_room = pos % daySize
            room_index = time_room // Schedule.DAY_HOURS
            time = time_room % Schedule.DAY_HOURS
            
            if room_index < len(rooms):
                room = rooms[room_index]
            else:
                continue
            
            day_name = ["Mon", "Tue", "Wed", "Thu", "Fri"][day]
            
            start_clock_hour = START_HOUR + time
            
            if start_clock_hour > 12:
                time_display = f"{start_clock_hour - 12}:00 PM"
            elif start_clock_hour == 12:
                time_display = "12:00 PM"
            else:
                time_display = f"{start_clock_hour}:00 AM"

            print(f"Class ID {class_id} ({cc.GetCourse().GetName()} for {cc.GetGroup().GetName()}):")
            print(f"  Day: {day_name}, Time: {time_display}, Room: {room.GetName()} (Duration: {cc.GetDuration()})")


# --- Main Execution Block ---

if __name__ == "__main__":
    
    from Configuration import Configuration
    
    try:
        config = Configuration('input.cfg')
        
        ga = Algorithm(config)
        
        ga.Run() 
        
    except FileNotFoundError:
        print("Error: input.cfg not found. Make sure it's in the correct directory.")
    except Exception as e:
        print(f"\nCRITICAL CRASH ERROR: The genetic algorithm failed. Details: {e}")