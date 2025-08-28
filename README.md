# HAZFixer – Geometry Validation and Cleaning Tool

**HAZFixer** is a QGIS plugin designed to help you identify and repair invalid geometries in your layers.  
It ensures cleaner datasets by validating features, fixing geometry issues, and removing duplicate vertices, all while providing a clear summary report of the changes made.  

---


## ⚙️ Functionality

- Validates the geometry of selected layers  
- Fixes only **invalid features** while leaving valid features untouched  
- Removes duplicate vertices from repaired features  
- Generates a **report window** listing invalid features (with sample attribute values for reference)  
- Protects your data: no changes are applied to valid geometries  

---

## 📝 Usage Instructions

1. Select one or more layers in the **Layers Panel**  
2. Ensure the layers are **editable**; otherwise, the process will fail  
3. Run **HAZFixer** to check and repair invalid geometries  
4. Review the **summary report** window for details of features identified and fixed  

---

## 🔔 Notes

- Raster or non-editable layers are not supported  
- Invalid features that cannot be repaired will still be listed in the report for manual inspection  
- Best used before analysis, digitising edits, or project submission to ensure clean geometry  

---

## 📅 Update History

- **2025-02-11**  
  Added functionality to remove invalid or empty geometries  

- **2025-07-11**  
  Improved logic: only invalid features are processed  
  Added detailed HTML report window summarising invalid features and fixes applied  
