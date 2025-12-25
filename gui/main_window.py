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
from gui.pdf_viewer_frame import PDFViewerFrame
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
        
        # NOTE: View Errors and Inspect buttons are now per-result in the scrollable list below
        
        # Results scrollable area
        self.results_list = ctk.CTkScrollableFrame(
            results_frame,
            fg_color="transparent"
        )
        self.results_list.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
    
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
        for widget in self.results_list.winfo_children():
            widget.destroy()
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
        """Display scan results in scrollable list"""
        # Clear existing
        for widget in self.results_list.winfo_children():
            widget.destroy()
            
        # Summary Header
        summary_frame = ctk.CTkFrame(self.results_list, fg_color=("gray90", "gray15"))
        summary_frame.pack(fill="x", padx=10, pady=(10, 20))
        
        ctk.CTkLabel(
            summary_frame, 
            text=f"Total: {job.total_files} | Compliant: {job.compliant_count} | Non-Compliant: {job.non_compliant_count} | Success: {job.success_rate:.1f}%",
            font=("Segoe UI", 14, "bold")
        ).pack(side="left", padx=20, pady=15)

        # Individual Results
        for result in job.results:
            self._add_result_row(result)

    def _add_result_row(self, result: PDFResult):
        """Add a single result row to the scrollable frame"""
        row = ctk.CTkFrame(self.results_list, fg_color=("white", "gray20"))
        row.pack(fill="x", padx=10, pady=5)
        
        # Status Icon/Label
        status_color = "green" if result.compliant else "red"
        status_text = "✓" if result.compliant else "✗"
        
        status_lbl = ctk.CTkLabel(
            row, 
            text=status_text, 
            text_color=status_color,
            font=("Segoe UI", 20, "bold"),
            width=40
        )
        status_lbl.pack(side="left", padx=(10, 5))
        
        # Filename and Violation count
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        ctk.CTkLabel(
            info_frame, 
            text=result.filename,
            font=("Segoe UI", 13, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(5, 0))
        
        violation_text = f"{result.total_violations} Violations" if not result.compliant else "Full Compliance"
        if result.error:
            violation_text = f"Error: {result.error}"
            
        ctk.CTkLabel(
            info_frame, 
            text=violation_text,
            font=("Segoe UI", 11),
            text_color="gray",
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        # Action Buttons
        if not result.compliant and result.violations:
            btn_view = ctk.CTkButton(
                row,
                text="👁 View Annotations",
                command=lambda r=result: self._view_errors(r),
                width=140,
                height=32,
                fg_color="orange",
                hover_color="darkorange"
            )
            btn_view.pack(side="right", padx=5, pady=10)
            
        btn_inspect = ctk.CTkButton(
            row,
            text="🔍 Inspect In-App",
            command=lambda r=result: self._inspect_pdf(r),
            width=140,
            height=32,
            fg_color="#00695c",
            hover_color="#004d40"
        )
        btn_inspect.pack(side="right", padx=(5, 15), pady=10)
    
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
    
    def _view_errors(self, target_result: PDFResult):
        """Annotate and view errors in PDF for a specific result"""
        if not target_result:
            return
            
        try:
            self._update_status(f"Generating annotations for {target_result.filename}...")
            
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
    
    def _inspect_pdf(self, target: PDFResult):
        """Open integrated PDF viewer for a specific result"""
        if not target:
            return
            
        # Hide main frame, show viewer
        self.main_frame.grid_remove()
        
        # Create viewer if needed
        if not hasattr(self, 'pdf_viewer') or self.pdf_viewer is None:
            self.pdf_viewer = PDFViewerFrame(self, close_callback=self._close_viewer)
        
        self.pdf_viewer.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.pdf_viewer.load_document(target)
        self._update_status(f"Inspecting: {target.filename}")

    def _close_viewer(self):
        """Close viewer and show results"""
        if hasattr(self, 'pdf_viewer') and self.pdf_viewer:
            self.pdf_viewer.grid_remove()
        self.main_frame.grid()
        self._update_status("Ready")
    
    def _update_status(self, message: str):
        """Update status bar"""
        self.statusbar.configure(text=message)
        logger.info(f"Status: {message}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
