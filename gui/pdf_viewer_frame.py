import customtkinter as ctk
from tkinter import Canvas, NW
import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageDraw
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFViewerFrame(ctk.CTkFrame):
    """
    Frame for viewing PDF with error highlights and navigation tree.
    """
    def __init__(self, master, close_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.close_callback = close_callback
        
        self.doc: Optional[fitz.Document] = None
        self.current_page_idx = 0
        self.zoom_level = 1.0
        self.current_result: Any = None
        self.violations_by_page = {}
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0) # Right panel for structure
        self.grid_rowconfigure(0, weight=1)
        
        # --- Left Panel: Error Tree ---
        self.left_panel = ctk.CTkFrame(self, width=250, fg_color=("gray90", "gray20"))
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.left_panel.grid_rowconfigure(1, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        # Header
        header_left = ctk.CTkFrame(self.left_panel, height=40)
        header_left.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(header_left, text="Compliance Errors", font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)
        
        if self.close_callback:
            ctk.CTkButton(header_left, text="⬅ Back", width=60, command=self.close_callback, fg_color="gray50").pack(side="right", padx=5)
            
        # Error Tree area
        self.error_tree = ctk.CTkScrollableFrame(self.left_panel, label_text="Violations by Page")
        self.error_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # --- Middle Panel: PDF View ---
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        # Toolbar
        self.toolbar = ctk.CTkFrame(self.right_panel, height=40)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.lbl_page = ctk.CTkLabel(self.toolbar, text="Page: 0/0")
        self.lbl_page.pack(side="left", padx=10)
        
        ctk.CTkButton(self.toolbar, text="-", width=30, command=lambda: self.change_zoom(-0.1)).pack(side="right", padx=5)
        self.lbl_zoom = ctk.CTkLabel(self.toolbar, text="100%")
        self.lbl_zoom.pack(side="right", padx=5)
        ctk.CTkButton(self.toolbar, text="+", width=30, command=lambda: self.change_zoom(0.1)).pack(side="right", padx=5)
        
        ctk.CTkButton(self.toolbar, text="Prev", width=60, command=self.prev_page).pack(side="left", padx=5)
        ctk.CTkButton(self.toolbar, text="Next", width=60, command=self.next_page).pack(side="left", padx=5)
        
        # Scrollable Image Area
        # Using a Canvas inside a ScrollableFrame might be tricky for scrolling both directions.
        # Let's use a standard ScrollableFrame that contains a Label with the image.
        self.viewer_scroll = ctk.CTkScrollableFrame(self.right_panel)
        self.viewer_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.image_label = ctk.CTkLabel(self.viewer_scroll, text="")
        self.image_label.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Right Panel: Logical Structure Tree ---
        self.structure_panel = ctk.CTkFrame(self, width=250, fg_color=("gray90", "gray20"))
        self.structure_panel.grid(row=0, column=2, sticky="nsew", padx=0, pady=0)
        self.structure_panel.grid_rowconfigure(1, weight=1)
        self.structure_panel.grid_columnconfigure(0, weight=1)

        header_right = ctk.CTkFrame(self.structure_panel, height=40)
        header_right.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(header_right, text="Logical Structure", font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)

        self.struct_tree = ctk.CTkScrollableFrame(self.structure_panel, label_text="Document Tags")
        self.struct_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def load_document(self, result: Any):
        """Load a PDF document and results"""
        self.current_result = result
        try:
            if self.doc:
                self.doc.close()
            
            logger.info(f"Loading PDF for inspection: {result.filepath}")
            self.doc = fitz.open(result.filepath)
            
            # 1. Organize violations by page with robust resolution
            from utils.pdf_utils import build_xref_page_map, resolve_violation_page
            xref_map = build_xref_page_map(self.doc)
            
            self.violations_by_page = {}
            for v in result.violations:
                p_idx = resolve_violation_page(v, self.doc, xref_map)
                
                if p_idx is None:
                    p_idx = 0 # Default global to page 0 for display
                
                if p_idx not in self.violations_by_page:
                    self.violations_by_page[p_idx] = []
                self.violations_by_page[p_idx].append(v)
            
            # 2. Populate Trees
            self._populate_error_tree()
            self._populate_structure_tree()
            
            self.current_page_idx = 0
            self._render_page()
            
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}", exc_info=True)
            self.image_label.configure(text=f"Error loading PDF: {e}")

    def _populate_error_tree(self):
        """Populate the left sidebar with pages and errors"""
        # Clear existing
        for widget in self.error_tree.winfo_children():
            widget.destroy()
            
        if not self.doc:
            return

        # Add Global/Document errors first (Page 0/Unmapped)
        if 0 in self.violations_by_page:
             # Just checking if we have effectively global errors mapped to 0
             pass

        total_pages = len(self.doc)
        
        for p_idx in range(total_pages):
            # Page Header
            page_btn = ctk.CTkButton(
                self.error_tree, 
                text=f"Page {p_idx + 1}", 
                fg_color="transparent", 
                text_color=("gray10", "gray90"),
                anchor="w",
                command=lambda p=p_idx: self.go_to_page(p),
                height=28
            )
            page_btn.pack(fill="x", padx=2, pady=1)
            
            # Errors on this page
            if p_idx in self.violations_by_page:
                violations = self.violations_by_page[p_idx]
                for v in violations:
                    # Identifier for the error
                    rule = v.rule_id
                    desc = v.description[:40] + "..." if len(v.description) > 40 else v.description
                    
                    err_btn = ctk.CTkButton(
                        self.error_tree,
                        text=f"⚠ {rule}",
                        font=("Segoe UI", 11),
                        fg_color=("#ffeb3b", "#3e2723") if v.failed_checks > 1 else ("#ffebee", "#3e2723"),
                        text_color=("black", "white"), 
                        anchor="w",
                        height=24,
                        command=lambda p=p_idx, viol=v: self.focus_error(p, viol)
                    )
                    err_btn.pack(fill="x", padx=(15, 2), pady=1)

    def _populate_structure_tree(self):
        """Populate the right sidebar with logical tags or document outline"""
        for widget in self.struct_tree.winfo_children():
            widget.destroy()
            
        if not self.doc: return
        
        # 1. Try Pre-extracted Structure Tree (from Scanner)
        found_structure = False
        try:
            if hasattr(self.current_result, "structure_tree") and self.current_result.structure_tree:
                logger.info(f"Using {len(self.current_result.structure_tree)} pre-extracted structure nodes.")
                for node in self.current_result.structure_tree:
                    self._add_structure_node(node, 0)
                found_structure = True
            
            # 2. If not pre-extracted, try to extract on-the-fly (tier 2 fallback)
            if not found_structure:
                from utils.pdf_utils import get_logical_structure
                struct_tree = get_logical_structure(self.doc)
                if struct_tree:
                    logger.info("Extracted logical tags on-the-fly.")
                    for node in struct_tree:
                        self._add_structure_node(node, 0)
                    found_structure = True
        except Exception as e:
            logger.warning(f"Failed to load structure tree: {e}")

        # 2. Fallback to Document Outline (Bookmarks/TOC) if no tags found
        if not found_structure:
            try:
                outline = self.doc.get_outline_xrefs()
                if outline:
                    logger.info("Logical tags not found. Falling back to Document Outline (Bookmarks)...")
                    ctk.CTkLabel(
                        self.struct_tree, 
                        text="Tags not found. Showing Outline:", 
                        font=("Segoe UI", 11, "italic"),
                        text_color="gray"
                    ).pack(pady=(0, 5), fill="x")
                    self._add_outline_node(outline, 0)
                    found_structure = True
            except Exception as e:
                logger.warning(f"Failed to get document outline: {e}")

        if not found_structure:
            ctk.CTkLabel(
                self.struct_tree, 
                text="No structure found\n(No Tags or Bookmarks)", 
                text_color="gray",
                font=("Segoe UI", 12)
            ).pack(pady=20)

    def _add_structure_node(self, node, level):
        """Recursively add structure nodes to the UI"""
        if not node: return
        
        tag = node.get("tag", "Unknown")
        title = node.get("title", "")
        xref = node.get("xref", -1)
        text = f"{tag}" + (f": {title[:20]}" if title else "")
        
        # Determine color based on tag type
        color = ("gray10", "gray90")
        if tag in ["H1", "H2", "H3", "H4", "H5", "H6"]:
            color = ("#1a237e", "#9fa8da") # Indigo
        elif tag == "Figure":
            color = ("#1b5e20", "#a5d6a7") # Green
        
        btn = ctk.CTkButton(
            self.struct_tree,
            text=text,
            fg_color="transparent",
            text_color=color,
            anchor="w",
            font=("Segoe UI", 11),
            height=22,
            state="normal" 
        )
        btn.pack(fill="x", padx=(level * 12, 2), pady=0)
        
        # Add tooltips or click events if needed using xref
        
        # Add children
        children = node.get("children", [])
        for child in children:
            self._add_structure_node(child, level + 1)

    def _add_outline_node(self, node, level):
        """Recursively add outline (bookmarks) to the UI"""
        if not node: return
        
        # Outline is a linked list or nested list depending on how it's retrieved
        # PyMuPDF get_outline() returns a generator of (level, title, page, ...)
        # Wait, get_outline() returns the first node of a linked list structure
        
        curr = node
        while curr:
            title = curr.title
            page_num = curr.page
            
            btn = ctk.CTkButton(
                self.struct_tree,
                text=f"🔖 {title}",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                anchor="w",
                font=("Segoe UI", 11),
                height=22,
                command=lambda p=page_num: self.go_to_page(p)
            )
            btn.pack(fill="x", padx=(level * 15, 2), pady=0)
            
            # Recurse into children
            if curr.down:
                self._add_outline_node(curr.down, level + 1)
            
            curr = curr.next

    def go_to_page(self, page_idx):
        if 0 <= page_idx < len(self.doc):
            self.current_page_idx = page_idx
            self._render_page()

    def prev_page(self):
        self.go_to_page(self.current_page_idx - 1)

    def next_page(self):
        self.go_to_page(self.current_page_idx + 1)
        
    def change_zoom(self, delta):
        self.zoom_level = max(0.2, min(5.0, self.zoom_level + delta))
        self.lbl_zoom.configure(text=f"{int(self.zoom_level * 100)}%")
        self._render_page()

    def focus_error(self, page_idx, violation):
        """Switch to page and highlight specific error"""
        self.current_page_idx = page_idx
        self._render_page(highlight_violation=violation)

    def _render_page(self, highlight_violation=None):
        """Render current page to image"""
        if not self.doc:
            return
            
        page = self.doc[self.current_page_idx]
        
        # Create clear label text
        self.lbl_page.configure(text=f"Page: {self.current_page_idx + 1}/{len(self.doc)}")
        
        # Render page to pixmap
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(img, "RGBA")
        
        # Draw all errors for this page
        if self.current_page_idx in self.violations_by_page:
            for v in self.violations_by_page[self.current_page_idx]:
                 # Find rects
                 rects = self._find_violation_rects(page, v)
                 is_focused = (v == highlight_violation)
                 
                 color = (255, 0, 0, 100) if is_focused else (255, 100, 0, 40)
                 border = (255, 0, 0, 255) if is_focused else (255, 100, 0, 150)
                 width = 3 if is_focused else 1
                 
                 if rects:
                     for r in rects:
                         # Scale rect by zoom
                         scaled_r = [c * self.zoom_level for c in r] # x0, y0, x1, y1
                         draw.rectangle(scaled_r, fill=color, outline=border, width=width)
                 
                 # If focused but no rect, show text overlay?
                 if is_focused and not rects:
                      draw.text((10, 10), "Global/Structure Error - Location not visual", fill="red")

        # Display
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(pix.width, pix.height))
        self.image_label.configure(image=ctk_img)
        self.image_label.image = ctk_img # keep ref

    def _find_violation_rects(self, page, violation) -> List[Any]:
        """Find bounding boxes for a violation on the page"""
        rects = []
        target_xref = -1
        
        # 1. Try XREF-based lookup (Images, Annotations, Widgets)
        if violation.object_id:
            try:
                target_xref = int(violation.object_id.split()[0])
                
                # A. Images
                images = page.get_images(full=True)
                for img in images:
                    if img[0] == target_xref:
                        rects.extend(page.get_image_rects(target_xref))
                
                # B. Annotations & Widgets (Links, Form Fields, etc.)
                for ann in page.anns:
                    if ann.xref == target_xref:
                        rects.append(ann.rect)
                        
                for widget in page.widgets():
                    if widget.xref == target_xref:
                        rects.append(widget.rect)
                        
                # C. Links specifically (sometimes separate from anns in older pymupdf?)
                # page.get_links() returns dicts, not objects with xrefs usually, unless we use 'links' generator
                # page.anns covers most interactive elements.
                        
            except Exception as e:
                pass

        # 2. If no XREF or XREF found nothing, try Context Text Search
        # Many VeraPDF contexts look like: .../contentItem[0](Some Text)
        if not rects and violation.context:
            import re
            # Look for content in parenthesis, e.g. " (Hello World) "
            # This is heuristic and might match wrong text, but better than nothing for visualization
            text_matches = re.findall(r'\((.*?)\)', violation.context)
            if text_matches:
                # Use the longest match that looks like content
                # Filter out short coding stuff like (1) or (r)
                candidates = [t for t in text_matches if len(t) > 3]
                if candidates:
                    # Search for the longest candidate
                    target_text = max(candidates, key=len)
                    try:
                        # hit_max=1 to just find the first instance? Or all?
                        # All instances might clutter, but if it's the same error repeated...
                        # Let's limit to 5
                        search_res = page.search_for(target_text, hit_max=5)
                        rects.extend(search_res)
                    except:
                        pass
        
        return rects
