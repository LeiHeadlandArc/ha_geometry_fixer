from qgis.core import *
import processing
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMessageBox

from PyQt5.QtCore import Qt, QDate


def fix_invalid_and_clean(layer):
    original_count = layer.featureCount()
    if layer.readOnly():
        layer.setReadOnly(False)
    # Step 1: check validity
    validity = processing.run("qgis:checkvalidity", {
        'INPUT_LAYER': layer,
        'METHOD': 1,
        'IGNORE_RING_SELF_INTERSECTION': False,
        'VALID_OUTPUT': 'TEMPORARY_OUTPUT',
        'INVALID_OUTPUT': 'TEMPORARY_OUTPUT',
        'ERROR_OUTPUT': 'TEMPORARY_OUTPUT'
    })

    invalid_layer = validity['INVALID_OUTPUT']
    invalid_ids = [f['fid'] for f in invalid_layer.getFeatures()]
  
        # maping out 5 field value.fid, etc... 
    invalid_list = []
    fields = list(invalid_layer.fields())[:5] 

    
    # Get the list for the short report
    for f in invalid_layer.getFeatures():
        field_info_parts = []
        for field in fields:
            value = f[field.name()]
            if value not in [None, ""]:
                if isinstance(value, QDate): # type: ignore
                    value = value.toString("yyyy-MM-dd")
                field_info_parts.append(f"{field.name()}={value}")
        field_info = ", ".join(field_info_parts)
    

        invalid_list.append(f"{field_info}")

    if not invalid_ids:
        iface.messageBar().pushSuccess("Geometry Fixer", "No invalid geometries found.")
        return

    # Step 2: fix only invalid features
    fixed = processing.run("native:fixgeometries", {
        'INPUT': invalid_layer,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    })['OUTPUT']

    # Step 3: remove duplicated vertices from fixed features
    cleaned = processing.run("native:removeduplicatevertices", {
        'INPUT': fixed,
        'TOLERANCE': 0.1,
        'USE_Z_VALUE': False,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    })['OUTPUT']

    # Step 4: replace invalid features in original layer
    layer.startEditing()
    for f in layer.getFeatures():
        if f['fid'] in invalid_ids:
            layer.deleteFeature(f.id())

    cleaned.selectAll()
    iface.mapCanvas().refresh()
    iface.copySelectionToClipboard(cleaned)
    iface.pasteFromClipboard(layer)
    layer.commitChanges()
    iface.messageBar().pushSuccess("Geometry Fixer", f"In layer {layer.name()}, {len(invalid_ids)} invalid features fixed and cleaned.")
    fixed_count = layer.featureCount()

    unfixed_geometry_count =original_count - fixed_count
    if unfixed_geometry_count == 0:
        fixed_geometry_count = len(invalid_ids)
    else:
        fixed_geometry_count = f"{len(invalid_ids)} has been fixed, {unfixed_geometry_count} has been removed as empty geometry"

        # Step 5: Pop-up summary
    features_html = "<ul>"
    for s in invalid_list:
        features_html += f"<li>{s}</li>"
    features_html += "</ul>"

    msg = f"""
        <h3>🧹 Geometry Fix Report</h3>
        <b>Layer:</b> {layer.name()}<br>
        <b>Invalid features:</b> {len(invalid_ids)}<br>
        <b>Fixed features:</b> {fixed_geometry_count}<br>
        <b>Details:</b>{features_html}
    """
    popup = QMessageBox()
    popup.setWindowTitle("Geometry Fix Summary")
    popup.setTextFormat(Qt.TextFormat.RichText) 
    popup.setText(msg)
    popup.exec_()

    
