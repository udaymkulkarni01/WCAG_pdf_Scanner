"""
PDF Annotator service
Highlights accessibility errors in PDF files using PyMuPDF
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Optional
import logging
from models.scan_result import RuleViolation

logger = logging.getLogger(__name__)

class PDFAnnotator:
    """Handles PDF annotation for visualizing errors"""
    
    def annotate_pdf(self, input_path: str, violations: List[RuleViolation], output_path: Optional[str] = None) -> str:
        """
        Annotate PDF with error highlights.
        
        Args:
            input_path: Path to original PDF
            violations: List of violations to highlight
            output_path: Optional path for output file. If None, appends _annotated to original.
            
        Returns:
            Path to annotated PDF
        """
        try:
            doc = fitz.open(input_path)
            
            if not output_path:
                p = Path(input_path)
                output_path = str(p.parent / f"{p.stem}_annotated{p.suffix}")
            
            logger.info(f"Annotating PDF: {input_path}")
            logger.info(f"Violations to process: {len(violations)}")
            
            # Key: (page_idx, unique_rect_str) -> count
            highlighted_areas = set()
            
            # Collection for document-level errors (metadata, etc.)
            global_errors = []
            
            # Reserved height on first page for global errors
            first_page_start_y = 50
            
            for v in violations:
                page_idx = -1
                rects = []
                
                # 1. Determine Page Index
                if v.page is not None:
                    page_idx = v.page
                
                # If page is still unknown, try to find it via Object ID scanning (expensive, fallback)
                if page_idx == -1 and v.object_id:
                     try:
                        target_xref = int(v.object_id.split()[0])
                        # Quick check: is this possibly a page object itself?
                        # Skip for now to keep performance high
                        pass
                     except:
                        pass
                
                # If we still don't know the page, and it's likely a structure/metadata error
                # Treat as global error
                if page_idx == -1:
                    global_errors.append(v)
                    continue
                
                # If page is invalid, skip
                if page_idx < 0 or page_idx >= len(doc):
                    continue
                    
                page = doc[page_idx]
                
                # 2. Try to find the object's visual location
                if v.object_id:
                    try:
                        xref = int(v.object_id.split()[0])
                        
                        # Check images on page
                        images = page.get_images(full=True)
                        for img in images:
                            if img[0] == xref: # img[0] is existing xref
                                img_rects = page.get_image_rects(xref)
                                rects.extend(img_rects)
                    except Exception as e:
                        logger.debug(f"Error parsing object ID {v.object_id}: {e}")

                # 3. Draw Annotations on specific page
                color = (1, 0, 0) # Red
                
                if rects:
                    # Highlight specific objects
                    for r in rects:
                        r_key = f"{page_idx}_{r}"
                        if r_key not in highlighted_areas:
                            page.draw_rect(r, color=color, width=2)
                            highlighted_areas.add(r_key)
                else:
                    # Fallback: Page level annotation (e.g. content error but not an image)
                    # "Figure tags shall include..." but no image found?
                    
                    # Create a note on the page
                    # For page 0, we need to respect the header space we might add
                    base_y = first_page_start_y + 100 if page_idx == 0 else 50
                    
                    # Find a free slot
                    slot_found = False
                    for i in range(20): # Try 20 slots
                        y_pos = base_y + (i * 15)
                        if y_pos > page.rect.height - 50:
                            break
                        
                        point = fitz.Point(30, y_pos)
                        r_key = f"{page_idx}_text_{y_pos}"
                        
                        if r_key not in highlighted_areas:
                            text = f"[{v.rule_id}] {v.description[:60]}..."
                            page.insert_text(point, text, color=color, fontsize=8)
                            highlighted_areas.add(r_key)
                            slot_found = True
                            break
                            
            # 4. Print Global Errors on Page 1 (Index 0)
            if global_errors and len(doc) > 0:
                page = doc[0]
                
                # Draw Header Box
                header_rect = fitz.Rect(20, 20, page.rect.width - 20, first_page_start_y + (len(global_errors) * 12) + 10)
                # Ensure we don't cover whole page if too many errors
                if header_rect.height > 300:
                    header_rect.y1 = 320
                    
                # Semi-transparent background for readability
                page.draw_rect(header_rect, color=(1, 0.9, 0.9), fill=(1, 0.9, 0.9))
                page.draw_rect(header_rect, color=(0.8, 0, 0), width=1)
                
                # Title
                page.insert_text(fitz.Point(30, 40), "DOCUMENT COMPLIANCE ERRORS (Global/Metadata):", color=(0.5, 0, 0), fontsize=10)
                
                y = 60
                unique_globals = set()
                
                for v in global_errors:
                    if y > header_rect.y1 - 10:
                        page.insert_text(fitz.Point(30, y), f"... and {len(global_errors) - len(unique_globals)} more", color=(0,0,0), fontsize=8)
                        break
                        
                    msg = f"• {v.description[:80]}"
                    if msg not in unique_globals:
                        page.insert_text(fitz.Point(30, y), msg, color=(0,0,0), fontsize=8)
                        unique_globals.add(msg)
                        y += 12
            
            doc.save(output_path)
            doc.close()
            
            logger.info(f"Created annotated PDF: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to annotate PDF: {e}", exc_info=True)
            raise e
