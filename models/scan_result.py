"""
Data models for PDF scan results
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class RuleViolation:
    """Represents a single compliance rule violation"""
    rule_id: str
    specification: str
    clause: str
    description: str
    failed_checks: int
    passed_checks: int
    object_id: Optional[str] = None
    page: Optional[int] = None
    context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'rule_id': self.rule_id,
            'specification': self.specification,
            'clause': self.clause,
            'description': self.description,
            'failed_checks': self.failed_checks,
            'passed_checks': self.passed_checks,
            'object_id': self.object_id,
            'page': self.page,
            'context': self.context,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleViolation':
        """Create from dictionary"""
        return cls(
            rule_id=data.get('rule_id', ''),
            specification=data.get('specification', ''),
            clause=data.get('clause', ''),
            description=data.get('description', ''),
            failed_checks=data.get('failed_checks', 0),
            passed_checks=data.get('passed_checks', 0),
            object_id=data.get('object_id'),
            page=data.get('page'),
            context=data.get('context'),
        )


@dataclass
class PDFResult:
    """Represents scan result for a single PDF"""
    filename: str
    filepath: str
    compliant: bool
    profile: str
    statement: str = ""
    violations: List[RuleViolation] = field(default_factory=list)
    error: Optional[str] = None
    scan_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.scan_time is None:
            self.scan_time = datetime.now()
    
    @property
    def total_violations(self) -> int:
        """Total number of  violations"""
        return len(self.violations)
    
    @property
    def total_failed_checks(self) -> int:
        """Total number of failed checks across all violations"""
        return sum(v.failed_checks for v in self.violations)
    
    @property
    def status(self) -> str:
        """Human-readable status"""
        if self.error:
            return "ERROR"
        return "COMPLIANT" if self.compliant else "NON-COMPLIANT"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'filename': self.filename,
            'filepath': self.filepath,
            'compliant': self.compliant,
            'profile': self.profile,
            'statement': self.statement,
            'violations': [v.to_dict() for v in self.violations],
            'total_violations': self.total_violations,
            'total_failed_checks': self.total_failed_checks,
            'error': self.error,
            'scan_time': self.scan_time.isoformat() if self.scan_time else None,
            'status': self.status,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFResult':
        """Create from dictionary"""
        violations = [
            RuleViolation.from_dict(v) 
            for v in data.get('violations', [])
        ]
        
        scan_time = None
        if data.get('scan_time'):
            scan_time = datetime.fromisoformat(data['scan_time'])
        
        return cls(
            filename=data.get('filename', ''),
            filepath=data.get('filepath', ''),
            compliant=data.get('compliant', False),
            profile=data.get('profile', ''),
            statement=data.get('statement', ''),
            violations=violations,
            error=data.get('error'),
            scan_time=scan_time,
        )


@dataclass
class ScanJob:
    """Represents a complete scanning session"""
    job_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    results: List[PDFResult] = field(default_factory=list)
    total_files: int = 0
    
    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now()
    
    @property
    def is_complete(self) -> bool:
        """Check if scan job is complete"""
        return self.end_time is not None
    
    @property
    def duration_seconds(self) -> float:
        """Duration of scan in seconds"""
        if not self.end_time:
            return (datetime.now() - self.start_time).total_seconds()
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def compliant_count(self) -> int:
        """Number of compliant PDFs"""
        return sum(1 for r in self.results if r.compliant and not r.error)
    
    @property
    def non_compliant_count(self) -> int:
        """Number of non-compliant PDFs"""
        return sum(1 for r in self.results if not r.compliant and not r.error)
    
    @property
    def error_count(self) -> int:
        """Number of PDFs with errors"""
        return sum(1 for r in self.results if r.error)
    
    @property
    def success_rate(self) -> float:
        """Percentage of compliant PDFs"""
        if not self.results:
            return 0.0
        return (self.compliant_count / len(self.results)) * 100
    
    def add_result(self, result: PDFResult):
        """Add a PDF result to the job"""
        self.results.append(result)
    
    def complete(self):
        """Mark the scan job as complete"""
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'job_id': self.job_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_files': self.total_files,
            'results': [r.to_dict() for r in self.results],
            'compliant_count': self.compliant_count,
            'non_compliant_count': self.non_compliant_count,
            'error_count': self.error_count,
            'success_rate': self.success_rate,
            'duration_seconds': self.duration_seconds,
            'is_complete': self.is_complete,
        }
    
    def to_json(self, filepath: str):
        """Save scan job to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanJob':
        """Create from dictionary"""
        results = [
            PDFResult.from_dict(r) 
            for r in data.get('results', [])
        ]
        
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = None
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'])
        
        return cls(
            job_id=data.get('job_id', ''),
            start_time=start_time,
            end_time=end_time,
            results=results,
            total_files=data.get('total_files', 0),
        )
    
    @classmethod
    def from_json(cls, filepath: str) -> 'ScanJob':
        """Load scan job from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
