import sys
import os
import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
import logging

from .ui.main_window import InSeis  # Updated class name


def main():
    try:
        """Main function to start the InSeis application."""
        logging.info("Starting InSeis application")
        app = QApplication(sys.argv)


        """
        work_dir = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(work_dir, "ui", "theme.qss")
        
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
        """

        # Create and show main window 
        window = InSeis()  # Using updated class name
        window.setWindowTitle('InSeis')
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        pos_x = int(screen_width * 0.05)
        pos_y = int(screen_height * 0.05)
        window_width= int(screen_width * 0.6)
        window_height = int(screen_height * 0.8)
        window.setGeometry(pos_x, pos_y, window_width, window_height)

        app.setStyle("windowsvista")
        app.setFont(QFont("Segoe UI", 10))

        window.show()

        sys.exit(app.exec())

    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


