import sys
import os
import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
import logging

from .ui.main_window import InSeis

def setup_logging():
    """Set up logging configuration."""
    log_dir = os.path.join(os.path.expanduser("~"), "Documents", "InSeis", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "inseis.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    try:
        """Main function to start the InSeis application."""
        # Setup logging first
        setup_logging()
        

        
        logging.info("Starting InSeis application")
        app = QApplication(sys.argv)
        app.setStyle("windowsvista")
        app.setFont(QFont("Segoe UI", 10))

        # Create and show main window 
        window = InSeis()
        window.setWindowTitle('InSeis')
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        pos_x = int(screen_width * 0.05)
        pos_y = int(screen_height * 0.05)
        window_width= int(screen_width * 0.6)
        window_height = int(screen_height * 0.8)
        window.setGeometry(pos_x, pos_y, window_width, window_height)

        window.show()

        
        sys.exit(app.exec())

    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


