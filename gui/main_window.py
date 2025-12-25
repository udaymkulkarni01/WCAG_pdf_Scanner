"""
Main application window for PDF Compliance Scanner
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path
from typing import List, Optional

from utils.logger import setup_logger
from services.pdf_scanner import PDFScanner, discover_pdfs
from services.report_generator import generate_html_report, generate_excel_report
from services.report_generator import generate_html_report, generate_excel_report
from services.pdf_annotator import PDFAnnotator
from models.scan_result import ScanJob
import config
import webbrowser
import os

logger = setup_logger(__name__)


class MainWindow(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title(config.WINDOW_TITLE)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        # Initialize services
        self.scanner = PDFScanner()
        self.annotator = PDFAnnotator()
        self.current_job: Optional[ScanJob] = None
        self.selected_files: List[str] = []
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create UI
        self._create_header()
        self._create_main_content()
        self._create_statusbar()
        
        logger.info("Main window initialized")
    
    def _create_header(self):
        """Create header with title and controls"""
        header = ctk.CTkFrame(self, fg_color=("gray85", "gray20"))
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            header,
            text="📄 PDF Compliance Scanner",
            font=("Segoe UI", 24, "bold")
        )
        title.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # Theme toggle
        theme_btn = ctk.CTkButton(
            header,
            text="🌙 Toggle Theme",
            command=self._toggle_theme,
            width=120
        )
        theme_btn.grid(row=0, column=1, padx=(10, 5), pady=15)
        
        # Open Logs button
        logs_btn = ctk.CTkButton(
            header,
            text="📝 Open Logs",
            command=self._open_logs,
            width=120,
            fg_color="gray50",
            hover_color="gray40"
        )
        logs_btn.grid(row=0, column=2, padx=(5, 20), pady=15)
    
    def _create_main_content(self):
        """Create main content area"""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        
        # Upload section
        self._create_upload_section()
        
        # Results section
        self._create_results_section()
    
    def _create_upload_section(self):
        """Create file upload section"""
        upload_frame = ctk.CTkFrame(self.main_frame)
        upload_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        upload_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            upload_frame,
            text="Select PDFs to Scan",
            font=("Segoe UI", 18, "bold")
        )
        title.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(upload_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10)
        
        btn_files = ctk.CTkButton(
            btn_frame,
            text="📁 Browse Files",
            command=self._browse_files,
            width=150,
            height=40
        )
        btn_files.pack(side="left", padx=5)
        
        btn_folder = ctk.CTkButton(
            btn_frame,
            text="📂 Browse Folder",
            command=self._browse_folder,
            width=150,
            height=40
        )
        btn_folder.pack(side="left", padx=5)
        
        btn_scan = ctk.CTkButton(
            btn_frame,
            text="🔍 Start Scan",
            command=self._start_scan,
            width=150,
            height=40,
            fg_color="green",
            hover_color="darkgreen"
        )
        btn_scan.pack(side="left", padx=5)
        
        # Selected files label
        self.files_label = ctk.CTkLabel(
            upload_frame,
            text="No files selected",
            font=("Segoe UI", 12)
        )
        self.files_label.grid(row=2, column=0, columnspan=2, padx=20, pady=10)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(upload_frame)
        self.progress_bar.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            upload_frame,
            text="",
            font=("Segoe UI", 10)
        )
        self.progress_label.grid(row=4, column=0, columnspan=2, padx=20, pady=(0, 20))
    
    def _create_results_section(self):
        """Create results display section"""
        results_frame = ctk.CTkFrame(self.main_frame)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        
        # Title and export buttons
        header_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            header_frame,
            text="Scan Results",
            font=("Segoe UI", 18, "bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        export_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        export_frame.grid(row=0, column=1, sticky="e")
        
        self.btn_export_html = ctk.CTkButton(
            export_frame,
            text="📄 Export HTML",
            command=self._export_html,
            width=120,
            state="disabled"
        )
        self.btn_export_html.pack(side="left", padx=5)
        
        self.btn_export_excel = ctk.CTkButton(
            export_frame,
            text="📊 Export Excel",
            command=self._export_excel,
            width=120,
            state="disabled"
        )
        self.btn_export_excel.pack(side="left", padx=5)
        
        self.btn_view_errors = ctk.CTkButton(
            export_frame,
            text="👁 View Errors",
            command=self._view_errors,
            width=120,
            state="disabled",
            fg_color="orange",
            hover_color="darkorange"
        )
        self.btn_view_errors.pack(side="left", padx=5)
        
        # Results text area
        self.results_text = ctk.CTkTextbox(
            results_frame,
            font=("Consolas", 11)
        )
        self.results_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
    
    def _create_statusbar(self):
        """Create status bar"""
        self.statusbar = ctk.CTkLabel(
            self,
            text="Ready",
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.statusbar.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
    
    def _open_logs(self):
        """Open the log file in default editor"""
        log_file = config.LOGS_FOLDER / "scanner.log"
        if log_file.exists():
            try:
                os.startfile(log_file)
                logger.info("Opened log file")
            except Exception as e:
                logger.error(f"Failed to open log file: {e}")
                messagebox.showerror("Error", f"Could not open log file:\n{e}")
        else:
            messagebox.showinfo("Info", "Log file does not exist yet.")

    def _toggle_theme(self):
        """Toggle between dark and light theme"""
        current = ctk.get_appearance_mode()
        new_theme = "Light" if current.lower() == "dark" else "Dark"
        ctk.set_appearance_mode(new_theme)
        logger.info(f"Theme changed from {current} to {new_theme}")
    
    def _browse_files(self):
        """Browse for individual PDF files"""
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        
        if files:
            self.selected_files = list(files)
            self._update_files_label()
            logger.info(f"Selected {len(self.selected_files)} files")
    
    def _browse_folder(self):
        """Browse for folder containing PDFs"""
        folder = filedialog.askdirectory(title="Select Folder Containing PDFs")
        
        if folder:
            self.selected_files = discover_pdfs(folder, recursive=True)
            self._update_files_label()
            logger.info(f"Found {len(self.selected_files)} PDF files in folder")
    
    def _update_files_label(self):
        """Update the selected files label"""
        count = len(self.selected_files)
        if count == 0:
            self.files_label.configure(text="No files selected")
        elif count == 1:
            self.files_label.configure(text=f"1 file selected: {Path(self.selected_files[0]).name}")
        else:
            self.files_label.configure(text=f"{count} files selected")
    
    def _start_scan(self):
        """Start scanning selected PDFs"""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select PDF files to scan first.")
            return
        
        logger.info(f"Starting scan of {len(self.selected_files)} files")
        
        # Clear results
        self.results_text.delete("1.0", "end")
        self.current_job = None
        
        # Disable export buttons
        self.btn_export_html.configure(state="disabled")
        self.btn_export_excel.configure(state="disabled")
        
        # Start scan in background thread
        thread = threading.Thread(target=self._scan_thread, daemon=True)
        thread.start()
    
    def _scan_thread(self):
        """Background thread for scanning"""
        try:
            self._update_status("Scanning PDFs...")
            
            # Perform scan
            job = self.scanner.scan_files(
                self.selected_files,
                progress_callback=self._on_progress
            )
            
            self.current_job = job
            
            # Update UI
            self.after(0, self._display_results, job)
            self.after(0, self._update_status, "Scan complete!")
            self.after(0, lambda: self.btn_export_html.configure(state="normal"))
            self.after(0, lambda: self.btn_export_excel.configure(state="normal"))
            self.after(0, lambda: self.btn_view_errors.configure(state="normal"))
            
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            self.after(0, self._update_status, f"Scan failed: {e}")
            self.after(0, messagebox.showerror, "Scan Error", f"Scan failed:\n\n{str(e)}")
    
    def _on_progress(self, current: int, total: int, filename: str):
        """Progress callback from scanner"""
        progress = current / total
        self.after(0, self.progress_bar.set, progress)
        self.after(0, self.progress_label.configure, 
                  text=f"Scanning {current}/{total}: {filename}")
        self.after(0, self._update_status, f"Scanning: {filename}")
    
    def _display_results(self, job: ScanJob):
        """Display scan results in text area"""
        self.results_text.delete("1.0", "end")
        
        # Summary
        self.results_text.insert("end", "=" * 80 + "\n")
        self.results_text.insert("end", "SCAN RESULTS SUMMARY\n")
        self.results_text.insert("end", "=" * 80 + "\n\n")
        self.results_text.insert("end", f"Total PDFs Scanned: {job.total_files}\n")
        self.results_text.insert("end", f"Compliant: {job.compliant_count}\n")
        self.results_text.insert("end", f"Non-Compliant: {job.non_compliant_count}\n")
        self.results_text.insert("end", f"Errors: {job.error_count}\n")
        self.results_text.insert("end", f"Success Rate: {job.success_rate:.1f}%\n")
        self.results_text.insert("end", f"Duration: {job.duration_seconds:.2f} seconds\n\n")
        
        # Details
        self.results_text.insert("end", "=" * 80 + "\n")
        self.results_text.insert("end", "DETAILED RESULTS\n")
        self.results_text.insert("end", "=" * 80 + "\n\n")
        
        for result in job.results:
            self.results_text.insert("end", f"File: {result.filename}\n")
            self.results_text.insert("end", f"Status: {result.status}\n")
            self.results_text.insert("end", f"Profile: {result.profile}\n")
            self.results_text.insert("end", f"Violations: {result.total_violations}\n")
            
            if result.violations:
                self.results_text.insert("end", "\nViolations:\n")
                for v in result.violations[:5]:
                    self.results_text.insert("end", f"  - {v.rule_id}: {v.description}\n")
                    self.results_text.insert("end", f"    ({v.failed_checks} failed checks)\n")
                if len(result.violations) > 5:
                    self.results_text.insert("end", f"  ... and {len(result.violations) - 5} more\n")
            
            if result.error:
                self.results_text.insert("end", f"Error: {result.error}\n")
            
            self.results_text.insert("end", "\n" + "-" * 80 + "\n\n")
    
    def _export_html(self):
        """Export results to HTML and open in browser"""
        if not self.current_job:
            return
        
        try:
            # Generate HTML in temp directory
            import tempfile
            temp_dir = tempfile.gettempdir()
            filename = f"pdf_scan_report_{self.current_job.job_id}.html"
            filepath = os.path.join(temp_dir, filename)
            
            # Generate and open report
            generate_html_report(self.current_job, filepath)
            self._update_status(f"Opening HTML report in browser...")
            webbrowser.open(filepath)
            self._update_status(f"HTML report opened in browser")
            logger.info(f"HTML report generated: {filepath}")
                
        except Exception as e:
            logger.error(f"Failed to export HTML: {e}", exc_info=True)
            messagebox.showerror("Export Error", f"Failed to export HTML:\n\n{str(e)}")
    
    def _export_excel(self):
        """Export results to Excel"""
        if not self.current_job:
            return
        
        try:
            filepath = filedialog.asksaveasfilename(
                title="Save Excel Report",
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")]
            )
            
            if filepath:
                generate_excel_report(self.current_job, filepath)
                self._update_status(f"Excel report saved: {filepath}")
                
                if messagebox.askyesno("Success", "Excel report saved!\n\nOpen file?"):
                    os.startfile(filepath)
                
        except Exception as e:
            logger.error(f"Failed to export Excel: {e}", exc_info=True)
            messagebox.showerror("Export Error", f"Failed to export Excel:\n\n{str(e)}")
    
    def _view_errors(self):
        """Annotate and view errors in PDF"""
        if not self.current_job or not self.current_job.results:
            return
            
        # Find first non-compliant result for now
        # In a full app, we'd let user select which file
        target_result = None
        for result in self.current_job.results:
            if not result.compliant and result.violations:
                target_result = result
                break
        
        if not target_result:
            messagebox.showinfo("Info", "No violations found to visualize.")
            return
            
        try:
            self._update_status(f"Generatign annotations for {target_result.filename}...")
            
            # Run in thread to not freeze UI
            def run_annotate():
                try:
                    output_path = self.annotator.annotate_pdf(
                        target_result.filepath,
                        target_result.violations
                    )
                    self.after(0, lambda: self._update_status(f"Opening annotated PDF: {Path(output_path).name}"))
                    self.after(0, lambda: os.startfile(output_path))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", f"Failed to annotate PDF:\n{e}"))
                    self.after(0, lambda: self._update_status("Annotation failed"))
            
            thread = threading.Thread(target=run_annotate, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.error(f"Failed to initiate annotation: {e}")
            messagebox.showerror("Error", str(e))
    
    def _update_status(self, message: str):
        """Update status bar"""
        self.statusbar.configure(text=message)
        logger.info(f"Status: {message}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
