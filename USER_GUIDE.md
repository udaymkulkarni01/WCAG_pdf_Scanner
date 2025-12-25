# WCAG PDF Scanner - User Guide

This guide provides step-by-step instructions on how to use the WCAG PDF Scanner utility to validate and inspect PDF documents for accessibility compliance.

---

## 1. Launching the Application
Run the `main.py` script to start the application. On launch, you will see the main dashboard in Light Mode by default.

### The Dashboard
The dashboard is your central hub for selecting files and starting scans.
![Main Dashboard](real_dashboard.png)

---

## 2. Scanning PDF Documents

### Step 2.1: Select Files or Folders
- Click **"Browse Files"** to select individual PDF documents.
- Click **"Browse Folder"** to automatically discover all PDFs within a directory (including subfolders).

### Step 2.2: Start the Scan
Once files are selected, click the green **"Start Scan"** button. The progress bar will update as VeraPDF validates each document.

---

## 3. Dark Mode Support
For a more comfortable viewing experience, you can toggle the theme using the **"Toggle Theme"** button in the header.

![Dark Mode Dashboard](real_dark_dashboard.png)

---

## 4. Inspecting Results
After the scan completes, your results will appear in the **Scan Results** table.

### Detailed Inspection
To look closer at a specific document, select it and click **"Inspect In-App"**.

![Inspection View](real_inspection.png)

### Key Features in Inspection:
1.  **Compliance Errors (Left)**: View a list of all WCAG violations. Click any error to highlight it on the PDF.
2.  **PDF Viewer (Middle)**: Real-time visualization of the document with translucent overlays on selected errors.
3.  **Logical Structure (Right)**: Inspect the physical "tags" (H1, P, Table) of the PDF. Click a tag to jump to its location on the page.

---

## 5. Exporting Reports
You can export your findings in two formats:
- **HTML Report**: A clean, interactive summary that opens in your browser.
- **Excel Report**: A detailed spreadsheet containing exact rule IDs, clauses, and failed check counts for every violation.
