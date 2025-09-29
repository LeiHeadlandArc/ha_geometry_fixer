from qgis.core import *
import processing
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QDate


def fix_invalid_and_clean(layer):
    original_count = layer.featureCount()
    if layer.readOnly():
        layer.setReadOnly(False)
    
    # Step 1: Remove duplicate vertices AND fix geometries DIRECTLY on the original layer
    layer.startEditing()
    duplicate_count = 0
    fixed_count = 0
    
    for feature in layer.getFeatures():
        geom = feature.geometry()
        if geom and not geom.isNull():
            # Check if geometry was originally invalid
            was_invalid = not geom.isGeosValid()
            
            # Remove duplicate vertices with tolerance
            geom.removeDuplicateNodes(0.1)
            
            # Try to fix the geometry if it's still invalid
            if not geom.isGeosValid():
                fixed_geom = geom.makeValid()
                if fixed_geom and not fixed_geom.isNull():
                    geom = fixed_geom
            
            # Count as fixed if it was invalid originally and is now valid
            if was_invalid and geom.isGeosValid():
                fixed_count += 1
            
            layer.changeGeometry(feature.id(), geom)
            duplicate_count += 1
    layer.commitChanges()
    
    # Step 2: Check validity on the layer after cleaning
    validity = processing.run("qgis:checkvalidity", {
        'INPUT_LAYER': layer,
        'METHOD': 1,
        'IGNORE_RING_SELF_INTERSECTION': False,
        'VALID_OUTPUT': 'TEMPORARY_OUTPUT',
        'INVALID_OUTPUT': 'TEMPORARY_OUTPUT',
        'ERROR_OUTPUT': 'TEMPORARY_OUTPUT'
    })

    invalid_layer = validity['INVALID_OUTPUT']
    
    # Count invalid features
    invalid_count = invalid_layer.featureCount()
  
    # Build the report list - mapping out 5 field values
    invalid_list = []
    invalid_fids = []
    fields = list(invalid_layer.fields())[:5] 
    
    for f in invalid_layer.getFeatures():
        invalid_fids.append(f['fid'])
        field_info_parts = []
        for field in fields:
            value = f[field.name()]
            if value not in [None, ""]:
                if isinstance(value, QDate):
                    value = value.toString("yyyy-MM-dd")
                field_info_parts.append(f"{field.name()}={value}")
        field_info = ", ".join(field_info_parts)
        if field_info:
            invalid_list.append(field_info)

    # If no invalid geometries found
    

    # Step 3: Fix the invalid geometries
    fixed = processing.run("native:fixgeometries", {
        'INPUT': invalid_layer,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    })['OUTPUT']

    # Step 4: Add fixed features to the original layer (preserving originals)
    layer.startEditing()
    
    # Get all features from the fixed layer (these are the invalid ones, now fixed)
    fixed_features = list(fixed.getFeatures())
    layer.addFeatures(fixed_features)
    
    layer.commitChanges()
    
    # Calculate statistics
    final_count = layer.featureCount()
    added_features_count = final_count - original_count
    
    iface.messageBar().pushSuccess("Geometry Fixer", 
        f"Layer {layer.name()}: {invalid_count} invalid features fixed and added as new features.")

    # Step 5: Generate detailed report
    features_html = "<ul>"
    if invalid_list:
        for s in invalid_list:
            features_html += f"<li>{s}</li>"
    else:
        features_html += "<li>Feature details not available</li>"
    features_html += "</ul>"

    msg = f"""
        <h3>🧹 Geometry Fix Report</h3>
        <b>Layer:</b> {layer.name()}<br>
        <b>Original features:</b> {original_count}<br>
        <b>Duplicate vertices removed:</b> ✅ Yes<br>
        <b>Geometries auto-fixed:</b> {fixed_count}<br>
        <b>Fixed copies added:</b> {added_features_count}<br>
        <b>Total features now:</b> {final_count}<br>
        <br>
        <b>⚠️ Action Required:</b> {invalid_count} features could not be automatically fixed in place (FIDs: {', '.join(map(str, invalid_fids[:10]))}{' ...' if len(invalid_fids) > 10 else ''}). 
        Fixed copies have been added. Please manually review and delete the problematic originals (they may have area = 0 or other issues).<br>
        
    """
    
    popup = QMessageBox()
    popup.setWindowTitle("Geometry Fix Summary")
    popup.setTextFormat(Qt.TextFormat.RichText) 
    popup.setText(msg)
    popup.exec_()