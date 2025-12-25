"""
veraPDF CLI wrapper with comprehensive logging
Handles PDF validation through veraPDF command-line interface
"""
import subprocess
import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from utils.logger import setup_logger, log_separator
import config

logger = setup_logger(__name__)


class VeraPDFNotFoundError(Exception):
    """Raised when veraPDF executable is not found"""
    pass


class ValidationError(Exception):
    """Raised when PDF validation fails"""
    pass


def find_verapdf_executable() -> Optional[str]:
    """
    Find veraPDF executable on the system.
    Checks PATH and common installation locations.
    
    Returns:
        Path to veraPDF executable or None if not found
    """
    logger.info("Searching for veraPDF installation...")
    
    # Check if veraPDF is in PATH
    verapdf_cmd = 'verapdf.bat' if config.VERAPDF_EXECUTABLE == 'verapdf' else config.VERAPDF_EXECUTABLE
    
    found_path = shutil.which(verapdf_cmd)
    if found_path:
        logger.info(f"✓ Found veraPDF in PATH: {found_path}")
        return verapdf_cmd
    
    # Check common Windows installation paths
    common_paths = [
        r'C:\Program Files\veraPDF\verapdf.bat',
        r'C:\Program Files (x86)\veraPDF\verapdf.bat',
        r'C:\veraPDF\verapdf.bat',
        Path.home() / 'veraPDF' / 'verapdf.bat',
    ]
    
    logger.debug(f"Checking common installation paths: {common_paths}")
    
    for path in common_paths:
        path_obj = Path(path) if not isinstance(path, Path) else path
        if path_obj.exists():
            logger.info(f"✓ Found veraPDF at: {path_obj}")
            return str(path_obj)
    
    logger.error("✗ veraPDF not found in PATH or common installation locations")
    return None


def validate_pdf(
    pdf_path: str,
    flavour: str = None,
    include_success: bool = False
) -> Dict[str, Any]:
    """
    Validate a single PDF file using veraPDF.
    
    Args:
        pdf_path: Path to PDF file to validate
        flavour: PDF standard to validate against (default: from config)
        include_success: Include successful checks in output
        
    Returns:
        Dictionary containing validation results
        
    Raises:
        VeraPDFNotFoundError: If veraPDF is not found
        ValidationError: If validation fails
    """
    flavour = flavour or config.VERAPDF_FLAVOUR
    pdf_path = Path(pdf_path)
    
    log_separator(logger, f"Validating PDF: {pdf_path.name}")
    logger.info(f"File: {pdf_path}")
    logger.info(f"Size: {pdf_path.stat().st_size / 1024:.2f} KB")
    logger.info(f"Standard: PDF/{flavour.upper()}")
    
    # Find veraPDF executable
    verapdf_exe = find_verapdf_executable()
    if not verapdf_exe:
        raise VeraPDFNotFoundError(
            "veraPDF not found. Please install veraPDF and ensure it's in your PATH."
        )
    
    # Build command
    cmd = [
        verapdf_exe,
        '--format', config.VERAPDF_OUTPUT_FORMAT,
        '--flavour', flavour,
        '--maxfailuresdisplayed', str(config.MAX_FAILURES_DISPLAYED),
    ]
    
    if include_success:
        cmd.append('--success')
    
    cmd.append(str(pdf_path))
    
    logger.info(f"Executing command: {' '.join(cmd)}")
    
    # Execute validation
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.SCAN_TIMEOUT,
            shell=True  # Required for .BAT files on Windows
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✓ veraPDF completed in {duration:.2f} seconds")
        logger.info(f"Exit code: {result.returncode}")
        
        # Log stdout and stderr
        if result.stdout:
            logger.debug(f"STDOUT length: {len(result.stdout)} characters")
            logger.debug(f"STDOUT preview: {result.stdout[:200]}...")
        
        if result.stderr:
            logger.warning(f"STDERR: {result.stderr}")
        
        # Check for errors
        # Note: veraPDF returns exit code 1 for non-compliant PDFs, not errors
        # Only treat as error if there's actual error content in stderr
        if result.returncode != 0 and result.returncode != 1:
            logger.error(f"veraPDF execution failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"Error output: {result.stderr}")
            raise ValidationError(f"veraPDF failed: {result.stderr}")
        
        # If exit code is 1 but no JSON output, that's an actual error
        if not result.stdout or not result.stdout.strip():
            logger.error("No output from veraPDF")
            raise ValidationError("veraPDF produced no output")
        
        # Parse JSON output
        logger.info("Parsing JSON output...")
        try:
            output_data = json.loads(result.stdout)
            logger.debug("✓ JSON parsing successful")
            
            # Log the full JSON structure for debugging
            logger.info("=" * 80)
            logger.info("FULL veraPDF JSON OUTPUT:")
            logger.info("=" * 80)
            logger.info(json.dumps(output_data, indent=2))
            logger.info("=" * 80)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output: {e}")
            logger.debug(f"Raw output: {result.stdout}")
            raise ValidationError(f"Invalid JSON output from veraPDF: {e}")
        
        # Extract validation results
        parsed_result = parse_validation_output(output_data, pdf_path.name)
        
        logger.info(f"Compliance status: {'COMPLIANT' if parsed_result['compliant'] else 'NON-COMPLIANT'}")
        logger.info(f"Violations found: {len(parsed_result['violations'])}")
        
        if parsed_result['violations']:
            logger.debug("Violation summary:")
            for v in parsed_result['violations'][:5]:  # Log first 5
                logger.debug(f"  - {v['rule_id']}: {v['description'][:80]}")
            if len(parsed_result['violations']) > 5:
                logger.debug(f"  ... and {len(parsed_result['violations']) - 5} more")
        
        return parsed_result
        
    except subprocess.TimeoutExpired:
        logger.error(f"✗ Validation timed out after {config.SCAN_TIMEOUT} seconds")
        raise ValidationError(f"Validation timed out after {config.SCAN_TIMEOUT}s")
        
    except FileNotFoundError as e:
        logger.error(f"✗ File not found: {e}")
        raise ValidationError(f"File not found: {e}")
        
    except Exception as e:
        logger.error(f"✗ Unexpected error during validation: {e}", exc_info=True)
        raise ValidationError(f"Validation error: {e}")


def parse_validation_output(json_data: Dict, filename: str) -> Dict[str, Any]:
    """
    Parse veraPDF JSON output into structured format.
    
    Args:
        json_data: Raw JSON output from veraPDF
        filename: Name of the PDF file
        
    Returns:
        Parsed validation results
    """
    logger.debug(f"Parsing validation results for: {filename}")
    
    try:
        # Navigate JSON structure
        report = json_data.get('report', {})
        jobs = report.get('jobs', [])
        
        if not jobs:
            logger.warning("No validation jobs found in output")
            return {
                'filename': filename,
                'compliant': False,
                'profile': 'Unknown',
                'violations': [],
                'error': 'No validation data'
            }
        
        job = jobs[0]
        
        # veraPDF returns 'validationResult' as an array, not 'validationReport'
        validation_results = job.get('validationResult', [])
        
        if not validation_results:
            logger.warning("No validation results found in job")
            return {
                'filename': filename,
                'compliant': False,
                'profile': 'Unknown',
                'violations': [],
                'error': 'No validation results'
            }
        
        # Get the first validation result
        validation_report = validation_results[0]
        
        # Extract basic info
        compliant = validation_report.get('compliant', False)
        profile = validation_report.get('profileName', 'Unknown')
        statement = validation_report.get('statement', '')
        
        logger.debug(f"Profile: {profile}, Compliant: {compliant}")
        logger.debug(f"Statement: {statement}")
        
        # Log the validation report structure
        logger.info(f"Validation Report Keys: {validation_report.keys()}")
        logger.info(f"Has 'details' key: {'details' in validation_report}")
        
        # Extract violations
        violations = []
        details = validation_report.get('details', {})
        
        logger.info(f"Details keys: {details.keys() if details else 'No details'}")
        
        rule_summaries = details.get('ruleSummaries', [])
        
        logger.debug(f"Found {len(rule_summaries)} rule summaries")
        logger.info(f"Rule summaries type: {type(rule_summaries)}")
        
        if rule_summaries:
            logger.info("First rule summary sample:")
            logger.info(json.dumps(rule_summaries[0] if rule_summaries else {}, indent=2))
        
        for rule in rule_summaries:
            if rule.get('status') == 'failed' or rule.get('failedChecks', 0) > 0:
                violation = {
                    'rule_id': rule.get('ruleId', 'Unknown'),
                    'specification': rule.get('specification', ''),
                    'clause': rule.get('clause', ''),
                    'description': rule.get('description', ''),
                    'failed_checks': rule.get('failedChecks', 0),
                    'passed_checks': rule.get('passedChecks', 0),
                }
                violations.append(violation)
                logger.debug(f"Violation: {violation['rule_id']} - {violation['failed_checks']} failures")
        
        result = {
            'filename': filename,
            'compliant': compliant,
            'profile': profile,
            'statement': statement,
            'violations': violations,
            'total_violations': len(violations)
        }
        
        logger.info(f"✓ Parsed {len(violations)} violations from validation report")
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing validation output: {e}", exc_info=True)
        return {
            'filename': filename,
            'compliant': False,
            'profile': 'Error',
            'violations': [],
            'error': str(e)
        }


def validate_multiple_pdfs(
    pdf_paths: List[str],
    flavour: str = None,
    progress_callback=None
) -> List[Dict[str, Any]]:
    """
    Validate multiple PDF files sequentially.
    
    Args:
        pdf_paths: List of paths to PDF files
        flavour: PDF standard to validate against
        progress_callback: Optional callback function(current, total, filename)
        
    Returns:
        List of validation results
    """
    log_separator(logger, f"Starting batch validation of {len(pdf_paths)} PDFs")
    
    results = []
    total = len(pdf_paths)
    
    for idx, pdf_path in enumerate(pdf_paths, 1):
        logger.info(f"Processing {idx}/{total}: {Path(pdf_path).name}")
        
        if progress_callback:
            progress_callback(idx, total, Path(pdf_path).name)
        
        try:
            result = validate_pdf(pdf_path, flavour)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to validate {pdf_path}: {e}")
            results.append({
                'filename': Path(pdf_path).name,
                'compliant': False,
                'profile': 'Error',
                'violations': [],
                'error': str(e)
            })
    
    log_separator(logger, "Batch validation complete")
    logger.info(f"Total PDFs processed: {total}")
    logger.info(f"Compliant: {sum(1 for r in results if r.get('compliant'))}")
    logger.info(f"Non-compliant: {sum(1 for r in results if not r.get('compliant'))}")
    
    return results


if __name__ == "__main__":
    # Test veraPDF wrapper
    print("Testing veraPDF wrapper...")
    print("-" * 50)
    
    try:
        verapdf = find_verapdf_executable()
        if verapdf:
            print(f"✓ Found veraPDF: {verapdf}")
        else:
            print("✗ veraPDF not found")
    except Exception as e:
        print(f"Error: {e}")
