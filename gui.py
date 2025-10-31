import sys
import copy 
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTableWidget, QTableWidgetItem, 
    QAction, QFileDialog, QMessageBox, QVBoxLayout, QAbstractItemView,
    QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# Import core logic
try:
    from Configuration import Configuration
    from Algorithm import Algorithm 
    from Schedule import Schedule 
except ImportError as e:
    QMessageBox.critical(None, "Import Error", f"Failed to import core modules: {e}")
    sys.exit(1)


class Example(QMainWindow):
    # Pastel colors for Professor assignment
    PROF_COLORS = [
        QColor(255, 153, 153), QColor(153, 255, 153), QColor(153, 153, 255), 
        QColor(255, 255, 153), QColor(153, 255, 255), QColor(255, 153, 255), 
        QColor(255, 204, 153), QColor(204, 153, 255), QColor(153, 255, 204),
        QColor(255, 102, 102), QColor(102, 255, 102), QColor(102, 102, 255)
    ]

    def __init__(self, config_instance):
        super().__init__()
        self.config = config_instance
        self.best_chromosome = None
        self.is_solved = False
        
        # 8:00 AM to 6:00 PM (10 slots: 8 to 17)
        self.START_HOUR = 8  
        self.DAY_HOURS = 10 
        
        # Ensure constant matches the value in Schedule.py (for safety)
        if hasattr(Schedule, 'DAY_HOURS') and Schedule.DAY_HOURS != self.DAY_HOURS:
            QMessageBox.warning(self, "Warning", "Schedule.DAY_HOURS does not match GUI. Time calculation may be wrong.")

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Simplified Timetable - Genetic Algorithm')
        self.setGeometry(100, 100, 1200, 600) 

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.tableWidget = QTableWidget()
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.main_layout.addWidget(self.tableWidget)
        
        self.createMenus()
        self.drawTimetable()
        self.show()

    def createMenus(self):
        fileMenu = self.menuBar().addMenu('File')
        
        loadAction = QAction('Load...', self)
        loadAction.triggered.connect(self.showDialog)
        fileMenu.addAction(loadAction)
        
        exitAction = QAction('Exit', self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        viewMenu = self.menuBar().addMenu('View')
        solveAction = QAction('Generate Timetable', self)
        solveAction.triggered.connect(self.solveSchedule)
        viewMenu.addAction(solveAction)

    def drawTimetable(self):
        # Time slots (8:00 AM to 5:00 PM)
        times = []
        for h in range(self.START_HOUR, self.START_HOUR + self.DAY_HOURS):
            if h < 12:
                times.append(f"{h}:00 AM")
            elif h == 12:
                times.append("12:00 PM")
            else: 
                times.append(f"{h-12}:00 PM")
                
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        rooms = list(self.config._rooms.values())
        NUM_ROOMS = len(rooms)
        
        # --- NEW STRUCTURE: Rows = Time Slots, Columns = Days ---
        self.tableWidget.setRowCount(self.DAY_HOURS)
        self.tableWidget.setColumnCount(len(days))
        self.tableWidget.setVerticalHeaderLabels(times) # Only time slots in the row header
        self.tableWidget.setHorizontalHeaderLabels(days)
        
        # Set row height for multiple classes per slot
        for row in range(self.DAY_HOURS):
             self.tableWidget.setRowHeight(row, 120) 
             
        # Set column width wider for better text fit
        for col in range(len(days)):
             self.tableWidget.setColumnWidth(col, 220) 
        
        # Clear existing content and set default background
        for row in range(self.DAY_HOURS):
            for col in range(len(days)):
                # We still need a dummy item in the cell for the table structure
                item = QTableWidgetItem("")
                item.setBackground(QColor(240, 240, 240))
                self.tableWidget.setItem(row, col, item)
                # Ensure no widget is left over from previous runs
                self.tableWidget.setCellWidget(row, col, None)


        # =================================================================
        # CRITICAL DRAWING LOGIC: Using QLabel to render HTML
        # =================================================================
        if self.is_solved and self.best_chromosome and hasattr(self.best_chromosome, 'classes') and self.best_chromosome.classes:
            
            daySize = NUM_ROOMS * self.DAY_HOURS 
            all_classes = self.config.GetCourseClasses()
            
            schedule_map = [[[] for _ in range(len(days))] for _ in range(self.DAY_HOURS)]

            for class_id, pos in self.best_chromosome.classes.items():
                
                cc = all_classes.get(class_id)
                if not cc: continue

                day_index = pos // daySize
                time_room = pos % daySize
                
                room_index = time_room // self.DAY_HOURS
                start_time_index = time_room % self.DAY_HOURS 
                
                duration = cc.GetDuration()
                room_name = rooms[room_index].GetName()
                prof = cc.GetProfessor()
                
                if day_index >= len(days) or start_time_index >= self.DAY_HOURS:
                    continue
                
                for i in range(duration):
                    current_time_index = start_time_index + i
                    if current_time_index < self.DAY_HOURS:
                        schedule_map[current_time_index][day_index].append({
                            'cc': cc, 
                            'room_name': room_name, 
                            'prof_id': prof.GetId(),
                            'is_start': (i == 0)
                        })

            # Now, populate the QTableWidget using the combined schedule_map
            for row in range(self.DAY_HOURS):
                for col in range(len(days)):
                    classes_in_slot = schedule_map[row][col]
                    
                    if not classes_in_slot:
                        continue 

                    combined_html = ""
                    for class_data in classes_in_slot:
                        cc = class_data['cc']
                        is_start = class_data['is_start']
                        prof_id = class_data['prof_id']
                        
                        prof_color = self.PROF_COLORS[prof_id % len(self.PROF_COLORS)].name()
                        
                        if is_start:
                            # --- MODIFICATION START ---
                            # Determine if it's Lab or Theory based on CourseClass.IsLabRequired()
                            class_type_text = " (LAB)" if cc.IsLabRequired() else " (Theory)"
                            
                            text = (
                                f"<span style='font-weight:bold; color:black;'>{cc.GetCourse().GetName()} ({cc.GetGroup().GetName()}){class_type_text}</span><br>"
                                f"<span style='color:#333;'>Room: {class_data['room_name']}, Prof: {cc.GetProfessor().GetName()}</span>"
                            )
                            # --- MODIFICATION END ---
                        else:
                            # For continuation slots, just show the course name and (Cont.)
                            text = f"<span style='color:gray;'>{cc.GetCourse().GetName()} (Cont.)</span> in {class_data['room_name']}"
                        
                        # Use a div to create the colored block
                        combined_html += (
                            f"<div style='background-color:{prof_color}; width:95%; padding: 4px; border: 1px solid #999; margin-bottom: 2px;'>"
                            f"{text}</div>"
                        )
                        
                    # --- CRITICAL FIX: Create and set the QLabel widget ---
                    label = QLabel()
                    # CRITICAL: Set the text format to RichText explicitly
                    label.setTextFormat(Qt.RichText) 
                    label.setText(combined_html)
                    label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                    # Enable word wrapping for long content
                    label.setWordWrap(True) 

                    # Set the QLabel as the cell widget
                    self.tableWidget.setCellWidget(row, col, label)


        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)


    def showDialog(self):
        """Handles File -> Load... action and loads a new configuration file."""
        fname, _ = QFileDialog.getOpenFileName(self, 'Open Configuration File', '.', 'Config Files (*.cfg)')
        
        if fname:
            try:
                config_instance = Configuration.getInstance()
                config_instance.ReadConfiguration(fname) 
                
                self.config = config_instance
                self.best_chromosome = None
                self.is_solved = False
                QMessageBox.information(self, "Success", f"Configuration file '{fname}' loaded successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Configuration Load Error", f"Failed to load configuration from '{fname}'.\nError: {e}")
                return
            
            self.drawTimetable()
            
    def solveSchedule(self):
        """Runs the Genetic Algorithm to generate the optimal schedule."""
        if not self.config or self.config.GetNumberOfCourseClasses() == 0:
            QMessageBox.warning(self, "Warning", "Configuration not loaded or has no classes.")
            return
            
        try:
            algorithm = Algorithm(self.config) 
            best_result = algorithm.Run() 
                    
            final_fitness = getattr(best_result, 'fitness', 0.0)
            
            # Use a threshold of 1.5, indicating a robust attempt to meet hard constraints
            if best_result is not None and final_fitness >= 1.5: 
                self.best_chromosome = copy.deepcopy(best_result)
                self.is_solved = True
                QMessageBox.information(self, "Success", f"Timetable generated! Fittest Score: {final_fitness:.4f}")
            else:
                self.best_chromosome = None
                self.is_solved = False
                QMessageBox.warning(self, "Failure", f"Genetic Algorithm failed. Fittest Score: {final_fitness:.4f}. Check constraints/input.cfg.")
                
            self.drawTimetable()
            
        except Exception as e:
            QMessageBox.critical(self, "Algorithm Error", f"An error occurred during algorithm execution:\n{e}")
            raise 
            
# --- Application Startup ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    default_file = 'input.cfg'
    config_instance = None
    
    try:
        config_instance = Configuration(default_file)
        
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", 
                             f"CRITICAL: Configuration could not be loaded at startup from '{default_file}'.\nDetails: {e}")
        sys.exit(1)

    ex = Example(config_instance)
    sys.exit(app.exec_())