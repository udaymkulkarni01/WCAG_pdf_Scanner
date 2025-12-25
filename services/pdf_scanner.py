"""
PDF scanner service with logging
Handles directory scanning and batch processing of PDFs
"""
from pathlib import Path
from typing import List, Callable, Optional
import uuid
from datetime import datetime

from utils.logger import setup_logger, log_separator
from utils.verapdf_wrapper import validate_pdf
from models.scan_result import ScanJob, PDFResult, RuleViolation
import config

logger = setup_logger(__name__)


class PDFScanner:
    """Main PDF scanning service"""
    
    def __init__(self):
        self.current_job: Optional[ScanJob] = None
    
    def scan_files(
        self,
        pdf_files: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> ScanJob:
        """
        Scan a list of PDF files for compliance.
        
        Args:
            pdf_files: List of PDF file paths
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            ScanJob with all results
        """
        job_id = f"scan_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        log_separator(logger, f"Starting Scan Job: {job_id}")
        logger.info(f"Total PDFs to scan: {len(pdf_files)}")
        
        # Create  scan job
        job = ScanJob(
            job_id=job_id,
            start_time=datetime.now(),
            total_files=len(pdf_files)
        )
        self.current_job = job
        
        # Scan each PDF
        for idx, pdf_path in enumerate(pdf_files, 1):
            pdf_file = Path(pdf_path)
            logger.info(f"Scanning {idx}/{len(pdf_files)}: {pdf_file.name}")
            
            if progress_callback:
                progress_callback(idx, len(pdf_files), pdf_file.name)
            
            try:
                # Validate PDF
                validation_result = validate_pdf(str(pdf_file))
                
                # Convert to PDFResult
                violations = [
                    RuleViolation.from_dict(v)
                    for v in validation_result.get('violations', [])
                ]
                
                result = PDFResult(
                    filename=pdf_file.name,
                    filepath=str(pdf_file),
                    compliant=validation_result.get('compliant', False),
                    profile=validation_result.get('profile', 'Unknown'),
                    statement=validation_result.get('statement', ''),
                    violations=violations,
                    error=validation_result.get('error'),
                    scan_time=datetime.now()
                )
                
                job.add_result(result)
                logger.info(f"✓ Completed: {pdf_file.name} - {result.status}")
                
            except Exception as e:
                logger.error(f"✗ Failed to scan {pdf_file.name}: {e}")
                
                # Add error result
                error_result = PDFResult(
                    filename=pdf_file.name,
                    filepath=str(pdf_file),
                    compliant=False,
                    profile='Error',
                    error=str(e),
                    scan_time=datetime.now()
                )
                job.add_result(error_result)
        
        # Complete the job
        job.complete()
        
        log_separator(logger, f"Scan Job Complete: {job_id}")
        logger.info(f"Duration: {job.duration_seconds:.2f} seconds")
        logger.info(f"Total files: {job.total_files}")
        logger.info(f"Compliant: {job.compliant_count}")
        logger.info(f"Non-compliant: {job.non_compliant_count}")
        logger.info(f"Errors: {job.error_count}")
        logger.info(f"Success rate: {job.success_rate:.1f}%")
        
        # Save job results
        self._save_job_results(job)
        
        self.current_job = None
        return job
    
    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> ScanJob:
        """
        Scan all PDFs in a directory.
        
        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            ScanJob with all results
        """
        dir_path = Path(directory)
        
        logger.info(f"Scanning directory: {dir_path}")
        logger.info(f"Recursive: {recursive}")
        
        # Find all PDF files
        if recursive:
            pdf_files = list(dir_path.rglob('*.pdf'))
        else:
            pdf_files = list(dir_path.glob('*.pdf'))
        
        pdf_paths = [str(f) for f in pdf_files]
        
        logger.info(f"Found {len(pdf_paths)} PDF files")
        
        if not pdf_paths:
            logger.warning("No PDF files found in directory")
        
        return self.scan_files(pdf_paths, progress_callback)
    
    def _save_job_results(self, job: ScanJob):
        """Save scan job results to disk"""
        try:
            output_file = config.REPORTS_FOLDER / f"{job.job_id}.json"
            job.to_json(str(output_file))
            logger.info(f"✓ Saved scan results to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save scan results: {e}")


def discover_pdfs(path: str, recursive: bool = True) -> List[str]:
    """
    Discover all PDF files in a path.
    
    Args:
        path: File or directory path
        recursive: Whether to scan subdirectories
        
    Returns:
        List of PDF file paths
    """
    path_obj = Path(path)
    
    if path_obj.is_file():
        if path_obj.suffix.lower() == '.pdf':
            logger.info(f"Single PDF file: {path_obj}")
            return [str(path_obj)]
        else:
            logger.warning(f"File is not a PDF: {path_obj}")
            return []
    
    elif path_obj.is_dir():
        logger.info(f"Discovering PDFs in: {path_obj}")
        
        if recursive:
            pdfs = list(path_obj.rglob('*.pdf'))
        else:
            pdfs = list(path_obj.glob('*.pdf'))
        
        pdf_paths = [str(f) for f in pdfs]
        logger.info(f"Found {len(pdf_paths)} PDF files")
        
        return pdf_paths
    
    else:
        logger.error(f"Path does not exist: {path_obj}")
        return []


if __name__ == "__main__":
    #Test PDF scanner
    print("Testing PDF Scanner...")
    print("-" * 50)
    
    scanner = PDFScanner()
    print("✓ PDF Scanner initialized")
