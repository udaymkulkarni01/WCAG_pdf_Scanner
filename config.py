"""
Configuration settings for PDF Compliance Scanner
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Upload settings
UPLOAD_FOLDER = BASE_DIR / 'uploads'
REPORTS_FOLDER = BASE_DIR / 'reports'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'pdf'}

# veraPDF settings
VERAPDF_EXECUTABLE = os.environ.get('VERAPDF_PATH', 'verapdf')  # Use 'verapdf.bat' on Windows if not in PATH
VERAPDF_FLAVOUR = 'ua1'  # PDF/UA-1 for WCAG accessibility compliance
# Other options: '1a', '1b', '2a', '2b', '2u', '3a', '3b', '3u', 'ua1'
MAX_FAILURES_DISPLAYED = 100
VERAPDF_OUTPUT_FORMAT = 'json'

# Processing settings
PARALLEL_PROCESSES = 4  # Number of parallel PDF validations
SCAN_TIMEOUT = 300  # Timeout in seconds for single PDF scan

# Java settings
MIN_JAVA_VERSION = 8

# Logging settings
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = BASE_DIR / 'logs' / 'scanner.log'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# GUI settings
WINDOW_TITLE = "PDF Compliance Scanner"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
THEME_MODE = "dark"  # "dark" or "light"
COLOR_THEME = "blue"  # "blue", "green", "dark-blue"

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
REPORTS_FOLDER.mkdir(parents=True, exist_ok=True)
(BASE_DIR / 'logs').mkdir(parents=True, exist_ok=True)
