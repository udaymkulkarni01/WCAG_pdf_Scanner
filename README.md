# PDF Compliance Scanner

A Windows desktop application that scans PDF documents for WCAG accessibility compliance using veraPDF, providing detailed reports with HTML and Excel export capabilities.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## Features

- ✅ **Batch PDF Scanning**: Scan single files or entire directories
- 📊 **Compliance Reporting**: Detailed violation reports with ISO standard references
- 📄 **HTML Export**: Beautiful, styled HTML reports ready for sharing
- 📈 **Excel Export**: Comprehensive Excel workbooks with charts and summaries
- 🎨 **Modern UI**: Clean, intuitive Windows desktop interface with dark/light themes
- 📝 **Comprehensive Logging**: Detailed logs of every operation for troubleshooting
- ⚡ **Fast Processing**: Efficient scanning with progress tracking

## Screenshots

### Main Interface
Upload PDFs through file browser or drag-and-drop

### Results Dashboard
View compliance status and detailed violation reports

### Excel Reports
Comprehensive reports with statistics and violation details

## Requirements

### System Requirements
- **Operating System**: Windows 10/11
- **Python**: 3.8 or higher (for development)
- **Java**: Java 8 or higher (JRE or JDK)
  - Download from: https://www.java.com/download/
  - Or OpenJDK from: https://adoptium.net/

### Dependencies
- **veraPDF**: PDF validation engine
  - Download from: https://verapdf.org/software/
  - Follow installation instructions and add to PATH

## Installation

### Option 1: Running from Source

1. **Clone or download this repository**
   ```bash
   cd WCAG_Document_PDF_Scanner
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure Java is installed**
   ```bash
   java -version
   ```
   Should show version 1.8.0 or higher

4. **Install veraPDF**
   - Download from https://verapdf.org/software/
   - Run the installer
   - Verify installation:
     ```bash
     verapdf --version
     ```

5. **Run the application**
   ```bash
   python main.py
   ```

### Option 2: Standalone Executable (Coming Soon)

A standalone `.exe` file will be provided that bundles all Python dependencies.
You'll still need Java and veraPDF installed.

## Usage

1. **Launch the application**
   - Run `python main.py` or double-click the executable

2. **Select PDFs to scan**
   - Click **Browse Files** to select individual PDF files
   - Click **Browse Folder** to scan an entire directory
   - Multiple files can be selected

3. **Start scanning**
   - Click **Start Scan** button
   - Watch progress in real-time
   - Wait for scan to complete

4. **View results**
   - Results appear in the main text area
   - See summary statistics and detailed violations
   - Scroll through per-file results

5. **Export reports**
   - Click **Export HTML** for a shareable web report
   - Click **Export Excel** for a detailed spreadsheet
   - Choose save location and filename

## Configuration

Edit `config.py` to customize settings:

```python
# veraPDF settings
VERAPDF_FLAVOUR = 'ua1'  # PDF/UA-1 for WCAG compliance
# Options: 'ua1', '1a', '1b', '2a', '2b', '3a', '3b'

# Processing
PARALLEL_PROCESSES = 4  # Number of parallel scans
SCAN_TIMEOUT = 300  # Timeout per PDF in seconds

# UI Theme
THEME_MODE = "dark"  # "dark" or "light"
```

## PDF Standards

The scanner validates against PDF/UA-1 by default, which targets WCAG accessibility:

- **PDF/UA-1**: Universal Accessibility (recommended for WCAG)
- **PDF/A-1a/1b**: Long-term archival
- **PDF/A-2a/2b/2u**: Extended archival features
- **PDF/A-3a/3b/3u**: Embedded files support

Change the standard in `config.py` by modifying `VERAPDF_FLAVOUR`.

## Logging

All operations are logged to `logs/scanner.log` with detailed information:

- veraPDF command execution
- Process start/end times
- JSON parsing results
- Error messages and stack traces
- Scan statistics

Log files rotate automatically at 10MB with 5 backup files kept.

## Troubleshooting

### "Java Not Found" Error
- Ensure Java 8+ is installed
- Verify with `java -version` in Command Prompt
- Add Java to PATH environment variable
- Restart the application after installing Java

### "veraPDF Not Found" Error
- Install veraPDF from https://verapdf.org/software/
- Add veraPDF to PATH or set `VERAPDF_PATH` environment variable
- Try full path in `config.py`: `VERAPDF_EXECUTABLE = r'C:\Program Files\veraPDF\verapdf.bat'`

### Scan Timeout
- Increase `SCAN_TIMEOUT` in `config.py` for large PDFs
- Check `scanner.log` for details
- Verify PDF is not corrupted

### Import Errors
- Ensure all Python dependencies are installed: `pip install -r requirements.txt`
- Use Python 3.8 or higher

## veraPDF Integration

See [VERAPDF_INTEGRATION.md](VERAPDF_INTEGRATION.md) for detailed documentation on:
- How veraPDF is integrated
- Command-line options
- JSON output format
- Error handling
- Performance tips

## Building Standalone .exe

To create a standalone executable:

```bash
pyinstaller --onefile --windowed --name "PDF_Compliance_Scanner" main.py
```

The `.exe` will be in the `dist/` folder.

**Note**: Users will still need Java and veraPDF installed.

## Project Structure

```
WCAG_Document_PDF_Scanner/
├── main.py                    # Application entry point
├── config.py                  # Configuration
├── gui/
│   └── main_window.py         # Main GUI window
├── services/
│   ├── java_checker.py        # Java verification
│   ├── pdf_scanner.py         # PDF scanning service
│   └── report_generator.py    # Report generation
├── utils/
│   ├── logger.py              # Logging utility
│   └── verapdf_wrapper.py     # veraPDF integration
├── models/
│   └── scan_result.py         # Data models
├── reports/                   # Generated reports
├── logs/                      # Application logs
└── README.md                  # This file
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- **veraPDF**: https://verapdf.org/ - PDF validation engine
- **CustomTkinter**: https://github.com/TomSchimansky/CustomTkinter - Modern UI framework
- **WCAG Guidelines**: https://www.w3.org/WAI/standards-guidelines/wcag/

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review `logs/scanner.log` for error details
3. Consult [VERAPDF_INTEGRATION.md](VERAPDF_INTEGRATION.md)
4. Open an issue on GitHub

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Author**: PDF Compliance Scanner Team
