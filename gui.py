# gui.py

import sys
import copy 
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTableWidget, QTableWidgetItem, 
    QAction, QFileDialog, QMessageBox, QVBoxLayout, QAbstractItemView,
    QLabel, QTabWidget, QHBoxLayout, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# Import core logic
try:
    from Configuration import Configuration
    from Algorithm import Algorithm 
    from Schedule import Schedule 
except ImportError as e:
    # A standard Python environment may not have these modules.
    # It's better to let the program start and handle the error gracefully.
    # For now, we will assume they are available if the user provided them.
    QMessageBox.critical(None, "Import Error", f"Failed to import core modules: {e}")
    sys.exit(1)


class Example(QMainWindow):
    PROF_COLORS = [
        QColor(255, 153, 153), QColor(153, 255, 153), QColor(153, 153, 255), 
        QColor(255, 255, 153), QColor(153, 255, 255), QColor(255, 153, 255), 
        QColor(255, 204, 153), QColor(204, 153, 255), QColor(153, 255, 204),
        QColor(255, 102, 102), QColor(102, 255, 102), QColor(102, 102, 255)
    ]

    STATUS_COLORS = {
        'RED': QColor(255, 100, 100),  
        'GREEN': QColor(150, 255, 150), 
        'YELLOW': QColor(255, 255, 150)
    }

    def __init__(self, config_instance):
        super().__init__()
        self.config = config_instance
        self.best_chromosome = None
        self.is_solved = False
        
        self.START_HOUR = 8  
        self.DAY_HOURS = 10 
        
        self.validation_data = [] 
        
        if hasattr(Schedule, 'DAY_HOURS') and Schedule.DAY_HOURS != self.DAY_HOURS:
            QMessageBox.warning(self, "Warning", "Schedule.DAY_HOURS does not match GUI. Time calculation may be wrong.")

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Simplified Timetable - Genetic Algorithm')
        self.setGeometry(100, 100, 1400, 700) 

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        self.timetable_widget = QWidget()
        self.timetable_layout = QVBoxLayout(self.timetable_widget)
        self.tableWidget = QTableWidget()
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.timetable_layout.addWidget(self.tableWidget)
        self.tab_widget.addTab(self.timetable_widget, "Generated Timetable")
        
        self.validation_widget = QWidget()
        self.validation_layout = QVBoxLayout(self.validation_widget)
        self.validationTable = QTableWidget()
        self.validationTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.validation_layout.addWidget(self.validationTable)
        self.tab_widget.addTab(self.validation_widget, "Session Tally & Validation")

        self.createMenus()
        # Ensure validation data is initialized before drawing
        self.validation_data = self.config.GenerateCourseRequirementsTable()
        self.drawValidationTable()
        self.drawTimetable()
        self.show()

    def createMenus(self):
        fileMenu = self.menuBar().addMenu('File')
        
        loadAction = QAction('Load Config...', self)
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
        times = []
        for h in range(self.START_HOUR, self.START_HOUR + self.DAY_HOURS):
            # Format time correctly
            if h < 12:
                times.append(f"{h}:00 AM")
            elif h == 12:
                times.append("12:00 PM")
            else: 
                times.append(f"{h-12}:00 PM")
                
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        # Accessing private attribute _rooms is generally discouraged, 
        # but is necessary if a public getter is unavailable.
        rooms = list(self.config._rooms.values())
        NUM_ROOMS = len(rooms)
        
        self.tableWidget.setRowCount(self.DAY_HOURS)
        self.tableWidget.setColumnCount(len(days))
        self.tableWidget.setVerticalHeaderLabels(times)
        self.tableWidget.setHorizontalHeaderLabels(days)
        
        # Set row/column sizes for better visual appeal
        for row in range(self.DAY_HOURS):
             self.tableWidget.setRowHeight(row, 120) 
        for col in range(len(days)):
             self.tableWidget.setColumnWidth(col, 220) 
        
        # Clear existing content
        for row in range(self.DAY_HOURS):
            for col in range(len(days)):
                item = QTableWidgetItem("")
                item.setBackground(QColor(240, 240, 240))
                self.tableWidget.setItem(row, col, item)
                self.tableWidget.setCellWidget(row, col, None)

        if self.is_solved and self.best_chromosome and hasattr(self.best_chromosome, 'classes') and self.best_chromosome.classes:
            
            daySize = NUM_ROOMS * self.DAY_HOURS 
            all_classes = self.config.GetCourseClasses()
            # schedule_map: [Time Index][Day Index] = list of classes
            schedule_map = [[[] for _ in range(len(days))] for _ in range(self.DAY_HOURS)]

            for class_id, pos in self.best_chromosome.classes.items():
                
                cc = all_classes.get(class_id)
                if not cc: continue

                day_index = pos // daySize
                time_room = pos % daySize
                
                if NUM_ROOMS == 0: continue 
                
                # The position encoding is Day * DaySlotsTotal + RoomIndex * DAY_HOURS + StartHour
                room_index = (time_room % daySize) // self.DAY_HOURS
                start_time_index = (time_room % daySize) % self.DAY_HOURS 
                
                duration = cc.GetDuration()
                
                if room_index < 0 or room_index >= len(rooms): continue 
                room_name = rooms[room_index].GetName()
                prof = cc.GetProfessor()
                
                if day_index >= len(days) or start_time_index >= self.DAY_HOURS:
                    continue
                
                # Populate the schedule map for the entire duration
                for i in range(duration):
                    current_time_index = start_time_index + i
                    if current_time_index < self.DAY_HOURS:
                        schedule_map[current_time_index][day_index].append({
                            'cc': cc, 
                            'room_name': room_name, 
                            'prof_id': prof.GetId(),
                            'is_start': (i == 0) # Flag for the starting hour of a multi-hour class
                        })

            # Draw the populated schedule
            for row in range(self.DAY_HOURS):
                for col in range(len(days)):
                    classes_in_slot = schedule_map[row][col]
                    
                    if not classes_in_slot:
                        continue 

                    combined_html = ""
                    # Sort classes by Group name for stable visualization
                    classes_in_slot.sort(key=lambda x: x['cc'].GetGroup().GetName()) 
                    
                    for class_data in classes_in_slot:
                        cc = class_data['cc']
                        is_start = class_data['is_start']
                        prof_id = class_data['prof_id']
                        
                        prof_color = self.PROF_COLORS[prof_id % len(self.PROF_COLORS)].name()
                        
                        if is_start:
                            class_type_tag = " (LAB)" if cc.IsLabRequired() else " (Theory)"
                            
                            text = (
                                f"<span style='font-weight:bold; color:black;'>{cc.GetCourse().GetName()} ({cc.GetGroup().GetName()}){class_type_tag}</span><br>"
                                f"<span style='color:#333;'>Room: {class_data['room_name']}, Prof: {cc.GetProfessor().GetName()}</span>"
                            )
                        else:
                            text = f"<span style='color:gray;'>{cc.GetCourse().GetName()} (Cont.)</span> in {class_data['room_name']}"
                        
                        combined_html += (
                            f"<div style='background-color:{prof_color}; width:95%; padding: 4px; border: 1px solid #999; margin-bottom: 2px;'>"
                            f"{text}</div>"
                        )
                        
                    label = QLabel()
                    label.setTextFormat(Qt.RichText) 
                    label.setText(combined_html)
                    label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                    label.setWordWrap(True) 

                    self.tableWidget.setCellWidget(row, col, label)


            self.tableWidget.resizeColumnsToContents()
            self.tableWidget.resizeRowsToContents()
            self.tableWidget.horizontalHeader().setStretchLastSection(True)


    def drawValidationTable(self):
        headers = ['Year', 'Group', 'Course Name', 'Professor', 'Type', 'Required', 'Scheduled', 'Status']
        self.validationTable.setColumnCount(len(headers))
        self.validationTable.setHorizontalHeaderLabels(headers)
        
        self.validationTable.setRowCount(len(self.validation_data))
        
        for row_index, row_data in enumerate(self.validation_data):
            # Status check for row coloring
            required = row_data.get('Required', 0)
            
            # Extract scheduled value (X from 'X/Y Done' or the integer value)
            scheduled_val = row_data.get('Scheduled')
            scheduled = 0
            if isinstance(scheduled_val, str):
                 try:
                     scheduled = int(scheduled_val.split('/')[0].strip())
                 except ValueError:
                     pass
            elif isinstance(scheduled_val, int):
                 scheduled = scheduled_val
            
            
            if scheduled < required:
                color = self.STATUS_COLORS['RED']
                tooltip = f"Under-scheduled! Only {scheduled} of {required} sessions scheduled."
            elif scheduled > required:
                color = self.STATUS_COLORS['YELLOW']
                tooltip = "Over-scheduled."
            else:
                color = self.STATUS_COLORS['GREEN']
                tooltip = "Requirement met."

            # Set items and apply row color
            # Use data_keys corresponding to the dictionary keys
            data_keys = ['Year', 'Group', 'CourseName', 'Professor', 'Type', 'Required', 'Scheduled'] 
            
            for col_index, key in enumerate(data_keys):
                # The 'Scheduled' key should display the 'X/Y Done' string if available
                if key == 'Scheduled' and isinstance(row_data.get('Status'), str):
                     value = row_data.get('Status')
                else:
                    value = str(row_data.get(key, 'N/A'))
                    
                item = QTableWidgetItem(value)
                item.setBackground(color)
                
                self.validationTable.setItem(row_index, col_index, item)
            
            # Add Status column with the final status text
            status_item = QTableWidgetItem(f"{scheduled}/{required}")
            status_item.setBackground(color)
            status_item.setToolTip(tooltip)
            self.validationTable.setItem(row_index, len(data_keys), status_item) 

        self.validationTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.validationTable.horizontalHeader().setStretchLastSection(True)
        self.validationTable.resizeRowsToContents()


    def showDialog(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open Configuration File', '.', 'Config Files (*.cfg)')
        
        if fname:
            try:
                config_instance = Configuration.getInstance()
                config_instance.ReadConfiguration(fname) 
                
                self.config = config_instance
                self.best_chromosome = None
                self.is_solved = False
                
                self.validation_data = self.config.GenerateCourseRequirementsTable()
                
                QMessageBox.information(self, "Success", f"Configuration file '{fname}' loaded successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Configuration Load Error", f"Failed to load configuration from '{fname}'.\nError: {e}")
                return
            
            self.drawTimetable()
            self.drawValidationTable()
            
    def solveSchedule(self):
        # --- FIX APPLIED HERE ---
        # Changed GetNumberOfCourseClasses() to len(self.config.GetCourseClasses())
        if not self.config or len(self.config.GetCourseClasses()) == 0: 
            QMessageBox.warning(self, "Warning", "Configuration not loaded or has no classes.")
            return
            
        try:
            # Use consistent parameters for Algorithm initialization if needed,
            # but for simplicity, we rely on the default constructor here.
            algorithm = Algorithm(self.config) 
            best_result = algorithm.Run() 
                    
            final_fitness = getattr(best_result, 'fitness', 0.0)
            
            if best_result is not None and final_fitness >= 1.5: # Use a reasonable threshold
                self.best_chromosome = copy.deepcopy(best_result)
                self.is_solved = True
                QMessageBox.information(self, "Success", f"Timetable generated! Fittest Score: {final_fitness:.4f}")
            else:
                self.best_chromosome = None
                self.is_solved = False
                QMessageBox.warning(self, "Failure", f"Genetic Algorithm failed. Fittest Score: {final_fitness:.4f}. Check constraints/input.cfg.")
            
            self.updateScheduledTally(self.best_chromosome)
            self.drawTimetable()
            self.drawValidationTable()
            
        except Exception as e:
            QMessageBox.critical(self, "Algorithm Error", f"An error occurred during algorithm execution:\n{e}")
            # Do not re-raise the exception if running in a GUI context unless necessary
            # raise 

    def updateScheduledTally(self, schedule):
        if schedule is None:
            for row in self.validation_data:
                row['Scheduled'] = 0
                row['Status'] = f"0/{row['Required']} Done"
            return
            
        # Create a map to link CourseClass objects to the correct validation row
        # Key: (Course Name, Group Name, Professor Name, Type)
        req_map = {}
        for row in self.validation_data:
            # Keys match the Configuration.py output
            key = (row['CourseName'], row['Group'], row['Professor'], row['Type'])
            req_map[key] = row
            # Reset scheduled count
            row['Scheduled'] = 0
            
        # Tally the scheduled sessions (occurrences)
        for class_id, pos in schedule.classes.items():
            cc_obj = self.config.GetCourseClasses().get(class_id)
            if cc_obj is None:
                continue

            # We rely on the GA to place the class; we just count *if* it was placed.

            course_name = cc_obj.GetCourse().GetName()
            group_name = cc_obj.GetGroup().GetName()
            prof_name = cc_obj.GetProfessor().GetName()
            session_type = 'Lab' if cc_obj.IsLabRequired() else 'Theory'
            
            key = (course_name, group_name, prof_name, session_type)
            
            if key in req_map:
                # FIX: Count the session (occurrence), not the duration.
                # Since all sessions in the new config are 1hr or 2hr (Lab), 
                # each CourseClass object represents *one* session occurrence.
                req_map[key]['Scheduled'] += 1 
        
        # Update Status string
        for row in self.validation_data:
            scheduled = row['Scheduled']
            required = row['Required']
            row['Status'] = f"{scheduled}/{required} Done"

# --- Application Startup ---
if __name__ == '__main__':
    # Initialize Configuration and start the GUI
    app = QApplication(sys.argv)
    default_file = 'input.cfg'
    config_instance = None
    
    try:
        # Configuration is initialized as a Singleton
        config_instance = Configuration(default_file) 
        
        # Manually trigger the initial read for display at startup, 
        # as the GUI expects config data to draw the validation table.
        config_instance.ReadConfiguration(default_file) 
        
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", 
                             f"CRITICAL: Configuration could not be loaded at startup from '{default_file}'.\nDetails: {e}")
        sys.exit(1)

    ex = Example(config_instance)
    sys.exit(app.exec_())
