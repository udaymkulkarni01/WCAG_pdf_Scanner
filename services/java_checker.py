"""
Java installation checker for PDF Compliance Scanner
Ensures Java 8+ is installed before running veraPDF
"""
import subprocess
import re
from typing import Tuple, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


def check_java_installation() -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Check if Java is installed and meets minimum version requirement.
    
    Returns:
        Tuple of (is_installed, version_string, major_version)
        Example: (True, "1.8.0_292", 8)
    """
    logger.info("Checking for Java installation...")
    
    try:
        # Run java -version command
        result = subprocess.run(
            ['java', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Java outputs version info to stderr
        output = result.stderr
        
        logger.debug(f"Java command output: {output}")
        
        # Parse version string
        # Format varies: "1.8.0_292", "11.0.12", "17.0.1"
        version_match = re.search(r'"?(\d+\.?\d*\.?\d*[._]\d+)"?', output)
        
        if not version_match:
            # Try alternate format (Java 9+)
            version_match = re.search(r'version "(\d+)', output)
        
        if not version_match:
            logger.warning("Could not parse Java version from output")
            return False, None, None
        
        version_string = version_match.group(1)
        
        # Extract major version
        # Java 8 and earlier: "1.8.0" -> 8
        # Java 9+: "11.0.12" -> 11
        if version_string.startswith('1.'):
            major_version = int(version_string.split('.')[1])
        else:
            major_version = int(version_string.split('.')[0])
        
        logger.info(f"Found Java version: {version_string} (major version: {major_version})")
        
        return True, version_string, major_version
        
    except FileNotFoundError:
        logger.error("Java executable not found. Java is not installed or not in PATH.")
        return False, None, None
        
    except subprocess.TimeoutExpired:
        logger.error("Java version check timed out")
        return False, None, None
        
    except Exception as e:
        logger.error(f"Error checking Java installation: {e}")
        return False, None, None


def verify_java_version(min_version: int = 8) -> bool:
    """
    Verify that Java meets minimum version requirement.
    
    Args:
        min_version: Minimum required Java major version
        
    Returns:
        True if Java is installed and meets requirement
    """
    is_installed, version_string, major_version = check_java_installation()
    
    if not is_installed:
        logger.error(f"Java {min_version}+ is required but Java is not installed")
        return False
    
    if major_version < min_version:
        logger.error(
            f"Java version {major_version} found, but Java {min_version}+ is required. "
            f"Please upgrade Java."
        )
        return False
    
    logger.info(f"✓ Java {major_version} meets minimum requirement (Java {min_version}+)")
    return True


def get_java_install_instructions() -> str:
    """
    Get user-friendly instructions for installing Java.
    
    Returns:
        Formatted instruction string
    """
    return """
Java Installation Required
==========================

This application requires Java 8 or higher to run veraPDF.

To install Java:
1. Visit: https://www.java.com/download/
2. Download and install the latest Java Runtime Environment (JRE)
3. Restart this application after installation

To verify Java installation:
- Open Command Prompt
- Type: java -version
- You should see version 1.8.0 or higher

Alternative: Download OpenJDK from https://adoptium.net/
"""


if __name__ == "__main__":
    # Test Java installation check
    print("Testing Java installation check...")
    print("-" * 50)
    
    is_installed, version, major = check_java_installation()
    
    if is_installed:
        print(f"✓ Java is installed: {version}")
        print(f"✓ Major version: {major}")
        
        if verify_java_version(8):
            print("✓ Java version meets requirements")
        else:
            print("✗ Java version does not meet requirements")
            print(get_java_install_instructions())
    else:
        print("✗ Java is not installed")
        print(get_java_install_instructions())
