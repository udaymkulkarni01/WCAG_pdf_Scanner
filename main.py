"""
Main desktop application entry point
PDF Compliance Scanner - Windows Desktop Application
"""
import customtkinter as ctk
from tkinter import messagebox
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger, log_separator
from services.java_checker import verify_java_version, get_java_install_instructions
from utils.verapdf_wrapper import find_verapdf_executable
from gui.main_window import MainWindow
import config

logger = setup_logger(__name__)


def check_dependencies() -> bool:
    """
    Check if all required dependencies are installed.
    
    Returns:
        True if all dependencies are met
    """
    log_separator(logger, "Checking Dependencies")
    
    # Check Java
    logger.info("Checking Java installation...")
    if not verify_java_version(config.MIN_JAVA_VERSION):
        logger.error("Java check failed")
        messagebox.showerror(
            "Java Not Found",
            get_java_install_instructions()
        )
        return False
    
    # Check veraPDF
    logger.info("Checking veraPDF installation...")
    verapdf = find_verapdf_executable()
    if not verapdf:
        logger.error("veraPDF not found")
        messagebox.showerror(
            "veraPDF Not Found",
            "veraPDF is required but was not found.\n\n"
            "Please install veraPDF from:\n"
            "https://verapdf.org/software/\n\n"
            "Make sure to add veraPDF to your system PATH\n"
            "or set VERAPDF_PATH environment variable."
        )
        return False
    
    logger.info("✓ All dependencies verified")
    return True


def main():
    """Main application entry point"""
    log_separator(logger, "PDF Compliance Scanner Starting")
    logger.info(f"Application starting...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {Path.cwd()}")
    
    try:
        # Set appearance mode and theme
        ctk.set_appearance_mode(config.THEME_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)
        
        logger.info(f"UI Theme: {config.THEME_MODE}/{config.COLOR_THEME}")
        
        # Check dependencies
        if not check_dependencies():
            logger.error("Dependency check failed. Exiting.")
            return 1
        
        # Create and run main window
        logger.info("Creating main window...")
        app = MainWindow()
        
        logger.info("Starting GUI event loop...")
        app.mainloop()
        
        logger.info("Application closed normally")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        messagebox.showerror(
            "Application Error",
            f"A fatal error occurred:\n\n{str(e)}\n\n"
            f"Check logs for details: {config.LOG_FILE}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
