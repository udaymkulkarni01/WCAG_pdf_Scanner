# veraPDF Integration Guide

This document explains how veraPDF is integrated into the PDF Compliance Scanner application.

## Overview

The PDF Compliance Scanner uses **veraPDF** (a free, open-source PDF/A validator) to check PDF documents against WCAG accessibility standards. veraPDF is integrated via its command-line interface (CLI), which our Python application calls using the `subprocess` module.

## Prerequisites

### 1. Java Runtime Environment
- **Required**: Java 8 or higher (JRE or JDK)
- **Why**: veraPDF is a Java application and requires Java to run
- **Check**: Run `java -version` in command prompt
- **Download**: https://www.java.com/download/

### 2. veraPDF Installation
- **Download**: https://verapdf.org/software/
- **Installation Options**:
  - **Installer** (Recommended): Use the Windows installer which adds veraPDF to PATH
  - **ZIP Archive**: Extract and manually add to PATH or specify full path in config

## Integration Architecture

```
Python Application
       ↓
subprocess.run()
       ↓
veraPDF CLI (verapdf.bat)
       ↓
JSON Output
       ↓
Python Parser
       ↓
Report Generator
```

## Command-Line Usage

### Basic Validation Command
```batch
verapdf --format json --flavour ua1 document.pdf
```

### Command Options
- `--format json`: Output results in JSON format for parsing
- `--flavour ua1`: Validate against PDF/UA-1 standard (WCAG accessibility)
- `--success`: Include passing checks in output (default: only failures)
- `--maxfailuresdisplayed 100`: Limit number of failures shown per rule
- `--processes 4`: Enable parallel processing for multiple files

### Supported PDF Standards
- `ua1` - PDF/UA-1 (Universal Accessibility) - **Default for WCAG**
- `1a`, `1b` - PDF/A-1a, PDF/A-1b
- `2a`, `2b`, `2u` - PDF/A-2 variants
- `3a`, `3b`, `3u` - PDF/A-3 variants

## JSON Output Format

veraPDF outputs a structured JSON response:

```json
{
  "report": {
    "buildInformation": {...},
    "jobs": [{
      "item": {
        "name": "document.pdf"
      },
      "validationReport": {
        "profileName": "PDF/UA-1",
        "statement": "PDF file is not compliant",
        "compliant": false,
        "details": {
          "ruleSummaries": [{
            "ruleId": "ISO_14289-1:2014_7.1",
            "specification": "ISO 14289-1:2014",
            "clause": "7.1",
            "testNumber": 1,
            "status": "failed",
            "passedChecks": 0,
            "failedChecks": 3,
            "description": "Tagged PDF"
          }],
          "checks": [{
            "status": "failed",
            "context": "root/document",
            "errorMessage": "StructTreeRoot missing"
          }]
        }
      }
    }]
  }
}
```

## Python Integration Implementation

### 1. veraPDF Detection
```python
def find_verapdf():
    # Check if veraPDF is in PATH
    if shutil.which('verapdf'):
        return 'verapdf'
    
    # Check common installation paths on Windows
    common_paths = [
        r'C:\Program Files\veraPDF\verapdf.bat',
        r'C:\verapDF\verapdf.bat',
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None
```

### 2. Execute Validation
```python
def validate_pdf(pdf_path, flavour='ua1'):
    cmd = [
        verapdf_path,
        '--format', 'json',
        '--flavour', flavour,
        '--maxfailuresdisplayed', '100',
        pdf_path
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    return json.loads(result.stdout)
```

### 3. Parse Results
```python
def parse_validation_result(json_output):
    job = json_output['report']['jobs'][0]
    validation = job['validationReport']
    
    return {
        'filename': job['item']['name'],
        'compliant': validation['compliant'],
        'profile': validation['profileName'],
        'violations': parse_violations(validation['details'])
    }
```

## Logging Implementation

The application logs every step of the veraPDF integration:

### Log Events
1. **veraPDF Detection**
   ```
   INFO: Searching for veraPDF installation
   INFO: Found veraPDF at: C:\Program Files\veraPDF\verapdf.bat
   ```

2. **Command Execution**
   ```
   INFO: Executing: verapdf --format json --flavour ua1 document.pdf
   INFO: Process started with PID: 12345
   ```

3. **Process Completion**
   ```
   INFO: veraPDF completed in 2.34 seconds
   INFO: Exit code: 0
   DEBUG: STDOUT: {"report": {...}}
   ```

4. **Error Handling**
   ```
   ERROR: veraPDF execution failed with exit code: 1
ERROR: STDERR: Invalid PDF structure
   ```

5. **JSON Parsing**
   ```
   INFO: Parsing validation results for:document.pdf
   INFO: Found 3 rule violations
   DEBUG: Violations: ISO 14289-1:2014 7.1, 7.2, 7.3
   ```

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `verapdf not found` | Not installed or not in PATH | Install veraPDF or set `VERAPDF_PATH` in config |
| `Java not found` | Java not installed | Install Java 8+ |
| `Invalid PDF` | Corrupted PDF file | Check PDF file integrity |
| `Timeout` | Large PDF taking too long | Increase `SCAN_TIMEOUT` in config |
| `JSON parse error` | Unexpected veraPDF output | Check veraPDF version compatibility |

### Error Handling Strategy
```python
try:
    result = validate_pdf(pdf_path)
except FileNotFoundError:
    logger.error("veraPDF executable not found")
    raise VeraPDFNotFoundError()
except subprocess.TimeoutExpired:
    logger.error(f"Validation timeout after {timeout}s")
    raise ValidationTimeoutError()
except json.JSONDecodeError:
    logger.error("Failed to parse veraPDF output")
    raise InvalidOutputError()
```

## Performance Optimization

### Parallel Processing
For multiple PDFs, use parallel execution:
```python
with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(validate_pdf, pdf_files)
```

### Typical Performance
- Small PDF (< 1 MB): 1-2 seconds
- Medium PDF (1-10 MB): 2-5 seconds
- Large PDF (> 10 MB): 5-30 seconds

## Configuration

### config.py Settings
```python
# veraPDF executable path (auto-detected if not set)
VERAPDF_EXECUTABLE = os.environ.get('VERAPDF_PATH', 'verapdf')

# Validation profile
VERAPDF_FLAVOUR = 'ua1'  # PDF/UA-1 for WCAG

# Processing settings
MAX_FAILURES_DISPLAYED = 100
SCAN_TIMEOUT = 300  # seconds
PARALLEL_PROCESSES = 4
```

## Troubleshooting

### veraPDF Not Detected
1. Verify installation: `verapdf --version`
2. Check PATH environment variable
3. Set explicit path in `config.py`

### Java Issues
1. Verify Java: `java -version`
2. Ensure Java 8+ is installed
3. Check JAVA_HOME environment variable

### Validation Failures
1. Check log file for detailed error messages
2. Try validating PDF manually: `verapdf document.pdf`
3. Verify PDF is not encrypted or corrupted

## References

- **veraPDF Documentation**: https://docs.verapdf.org/
- **veraPDF CLI Reference**: https://docs.verapdf.org/cli/
- **PDF/UA Standard**: ISO 14289-1:2014
- **WCAG Guidelines**: https://www.w3.org/WAI/standards-guidelines/wcag/
