"""
Shared PDF utilities for consistent document handling
"""
import fitz
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

def build_xref_page_map(doc: fitz.Document) -> Dict[int, int]:
    """
    Build a mapping of XREF IDs to Page Indices (0-based).
    This is used as a fallback when the report doesn't specify a page.
    """
    xref_map = {}
    logger.info("Building full XREF-to-page map...")
    
    for p_idx in range(len(doc)):
        try:
            page = doc[p_idx]
            
            # 1. Images
            for img in page.get_images(full=True):
                xref_map[img[0]] = p_idx
                
            # 2. Annotations
            for ann in page.annots():
                if ann.xref:
                    xref_map[ann.xref] = p_idx
                    
            # 3. Widgets
            for widget in page.widgets():
                if widget.xref:
                    xref_map[widget.xref] = p_idx
            
            # 4. Indirect References on the page
            # This is a deeper scan of the page's dictionary
            # It helps find objects that aren't strictly images or annotations
            # (e.g. nested Form XObjects, structure elements)
            
            # Get all XREFs mentioned by the page
            for xref in get_page_xrefs(doc, p_idx):
                if xref not in xref_map:
                    xref_map[xref] = p_idx
                    
        except Exception as e:
            logger.debug(f"Error mapping page {p_idx}: {e}")
            
    return xref_map

def get_page_xrefs(doc: fitz.Document, page_idx: int) -> List[int]:
    """Get all XREFs referenced by a page's dictionary and contents"""
    xrefs = []
    try:
        page_xref = doc.page_xref(page_idx)
        # Scan page dictionary for references
        page_dict = doc.xref_get_keys(page_xref)
        # This is very slow if we do it for every key. 
        # Better: use PyMuPDF's built-in reference finder if available
        # Or just stick to common ones.
        
        # Actually, get_images and get_xobjects cover most things.
        # Let's add Form XObjects specifically
        for x in doc.get_page_xobjects(page_idx):
            # x is (xref, name, type, ...)
            xrefs.append(x[0])
            
    except:
        pass
    return xrefs

def resolve_violation_page(violation: Any, doc: fitz.Document, xref_map: Dict[int, int]) -> Optional[int]:
    """
    Attempt to find the correct page for a violation.
    Returns 0-based page index or None.
    """
    # 1. Already has a page?
    if violation.page is not None and 0 <= violation.page < len(doc):
        return violation.page
        
    # 2. Try Object ID lookup
    if violation.object_id:
        try:
            xref = int(violation.object_id.split()[0])
            if xref in xref_map:
                return xref_map[xref]
        except:
            pass
            
    # 3. Last resort: text search (only if we have document handle)
    # This is expensive and heuristic, might be better left to the UI
    
    return None

def get_logical_structure(doc: fitz.Document) -> List[Dict[str, Any]]:
    """
    Extract logical structure (Tags) from PDF manually using low-level XREF access.
    """
    try:
        cat_xref = doc.pdf_catalog()
        st_root_val = doc.xref_get_key(cat_xref, "StructTreeRoot")
        
        if st_root_val[0] != 'xref':
            return []
            
        root_xref = int(st_root_val[1].split()[0])
        return _parse_kids(doc, root_xref)
    except Exception as e:
        logger.error(f"Error extracting manual structure: {e}")
        return []

def _parse_kids(doc: fitz.Document, parent_xref: int) -> List[Dict[str, Any]]:
    """Helper to parse the 'K' (Kids) key of a structure element or root"""
    kids = []
    val = doc.xref_get_key(parent_xref, "K")
    
    # val is like ('xref', '123 0 R') or ('array', '[123 0 R 456 0 R]') or ('int', '5')
    if val[0] == 'xref':
        elem = _parse_struct_elem(doc, int(val[1].split()[0]))
        if elem: kids.append(elem)
    elif val[0] == 'array':
        import re
        # Check if it's an array of integers (MCIDs) or object references
        if 'R' not in val[1]:
            # Likely MCIDs: [0 1 2 3]
            mcids = [int(x) for x in re.findall(r'\d+', val[1])]
            # For simpler UI, we treat MCIDs as children nodes if they are direct kids of root
            # but usually MCIDs are kids of a StructElem.
            # We'll return them as a special key in the parent instead of separate nodes.
            pass
        else:
            xref_ids = re.findall(r'(\d+)\s+0\s+R', val[1])
            for xid in xref_ids:
                elem = _parse_struct_elem(doc, int(xid))
                if elem: kids.append(elem)
    elif val[0] == 'int':
        # Single MCID
        pass
    
    return kids

def _parse_struct_elem(doc: fitz.Document, xref: int) -> Optional[Dict[str, Any]]:
    """Parse a single /StructElem object and its content items"""
    try:
        # Get Tag (Subtype)
        s_val = doc.xref_get_key(xref, "S")
        tag = s_val[1].strip('/') if s_val[0] == 'name' else "Unknown"
            
        # Get Title
        t_val = doc.xref_get_key(xref, "T")
        title = t_val[1] if t_val[0] in ['string', 'text'] else ""
        
        # Get Page Reference
        pg_val = doc.xref_get_key(xref, "Pg")
        page_idx = -1
        if pg_val[0] == 'xref':
            pg_xref = int(pg_val[1].split()[0])
            # Resolve page index from xref
            for i in range(len(doc)):
                if doc[i].xref == pg_xref:
                    page_idx = i
                    break
        
        # Get MCIDs (Content items)
        mcids = []
        k_val = doc.xref_get_key(xref, "K")
        if k_val[0] == 'int':
            mcids.append(int(k_val[1]))
        elif k_val[0] == 'array' and 'R' not in k_val[1]:
            import re
            mcids.extend([int(x) for x in re.findall(r'\d+', k_val[1])])
        elif k_val[0] == 'dict' and '/MCID' in k_val[1]:
            # Some PDFs have dicts as kids
            import re
            mcid_match = re.search(r'/MCID\s+(\d+)', k_val[1])
            if mcid_match:
                mcids.append(int(mcid_match.group(1)))

        # Recursively get children
        children = _parse_kids(doc, xref)
        
        return {
            "tag": tag,
            "title": title,
            "xref": xref,
            "page": page_idx,
            "mcids": mcids,
            "children": children
        }
    except Exception as e:
        logger.debug(f"Error parsing struct elem {xref}: {e}")
        return None

def map_mcids_to_rects(page: fitz.Page, mcids: List[int]) -> List[fitz.Rect]:
    """Find bounding boxes for a list of MCIDs on a page"""
    if not mcids: return []
    
    rects = []
    try:
        # We search the page dictionary for MCIDs
        # Note: 1.26.7 might not show them in get_text("dict") for all files,
        # so we'll try a search-based approach or block-level checking.
        
        # First pass: try to find if any block matches the MCID (if available)
        d = page.get_text("dict")
        for block in d["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    # In some PyMuPDF versions, mcid is available in span
                    if span.get("mcid") in mcids:
                        rects.append(fitz.Rect(span["bbox"]))
        
        # Second pass: if no rects found and tag has a title/text, 
        # we could search for that text, but we don't have it here.
    except:
        pass
    
    return rects

