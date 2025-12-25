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
    This replaces the unreliable veraPDF feature extraction.
    """
    try:
        cat_xref = doc.pdf_catalog()
        st_root_val = doc.xref_get_key(cat_xref, "StructTreeRoot")
        
        if st_root_val[0] != 'xref':
            logger.info("No /StructTreeRoot found in PDF catalog.")
            return []
            
        # Extract the integer part of '123 0 R'
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
        # Find all object references like '123 0 R'
        xref_ids = re.findall(r'(\d+)\s+0\s+R', val[1])
        for xid in xref_ids:
            elem = _parse_struct_elem(doc, int(xid))
            if elem: kids.append(elem)
    
    return kids

def _parse_struct_elem(doc: fitz.Document, xref: int) -> Optional[Dict[str, Any]]:
    """Parse a single /StructElem object"""
    try:
        # Get Tag (Subtype)
        s_val = doc.xref_get_key(xref, "S")
        if s_val[0] == 'name':
            tag = s_val[1].strip('/')
        else:
            tag = "Unknown"
            
        # Get Title
        t_val = doc.xref_get_key(xref, "T")
        title = t_val[1] if t_val[0] in ['string', 'text'] else ""
        
        # Recursively get children
        children = _parse_kids(doc, xref)
        
        return {
            "tag": tag,
            "title": title,
            "xref": xref,
            "children": children
        }
    except Exception as e:
        logger.debug(f"Error parsing struct elem {xref}: {e}")
        return None

