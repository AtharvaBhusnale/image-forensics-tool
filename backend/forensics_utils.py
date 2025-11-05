import os
import hashlib
import piexif
import io
import base64
from PIL import Image, ImageChops, ImageEnhance
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as ReportImage,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch


def get_metadata(image_path):
    """Extracts EXIF metadata from an image."""
    try:
        img = Image.open(image_path)
        exif_data = img.info.get("exif")

        if not exif_data:
            return {"Status": "No EXIF data found."}

        exif_dict = piexif.load(exif_data)
        metadata = {}

        # GPS Info
        if piexif.GPSIFD.GPSLatitude in exif_dict.get("GPS", {}):
            try:
                lat = exif_dict["GPS"][piexif.GPSIFD.GPSLatitude]
                lat_ref = exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef].decode("utf-8")
                lon = exif_dict["GPS"][piexif.GPSIFD.GPSLongitude]
                lon_ref = exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef].decode(
                    "utf-8"
                )

                def to_decimal(dms, ref):
                    degrees = dms[0][0] / dms[0][1]
                    minutes = dms[1][0] / dms[1][1]
                    seconds = dms[2][0] / dms[2][1]
                    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
                    if ref in ["S", "W"]:
                        decimal = -decimal
                    return decimal

                metadata["GPS_Coordinates"] = (
                    f"{to_decimal(lat, lat_ref)}, {to_decimal(lon, lon_ref)}"
                )
            except Exception as e:
                metadata["GPS_Coordinates"] = f"Error processing GPS data: {e}"

        # General Info
        general_info = {
            "Make": exif_dict.get("0th", {}).get(piexif.ImageIFD.Make),
            "Model": exif_dict.get("0th", {}).get(piexif.ImageIFD.Model),
            "Software": exif_dict.get("0th", {}).get(piexif.ImageIFD.Software),
            "DateTime": exif_dict.get("0th", {}).get(piexif.ImageIFD.DateTime),
        }

        # EXIF Info
        exif_info = {
            "DateTimeOriginal": exif_dict.get("Exif", {}).get(
                piexif.ExifIFD.DateTimeOriginal
            ),
            "DateTimeDigitized": exif_dict.get("Exif", {}).get(
                piexif.ExifIFD.DateTimeDigitized
            ),
            "PixelXDimension": exif_dict.get("Exif", {}).get(
                piexif.ExifIFD.PixelXDimension
            ),
            "PixelYDimension": exif_dict.get("Exif", {}).get(
                piexif.ExifIFD.PixelYDimension
            ),
        }

        # Clean up None values and decode bytes
        for data_dict in [general_info, exif_info]:
            for k, v in data_dict.items():
                if v:
                    if isinstance(v, bytes):
                        metadata[k] = v.decode("utf-8", errors="ignore").strip()
                    else:
                        metadata[k] = v

        return metadata if metadata else {"Status": "No readable EXIF tags found."}

    except Exception as e:
        return {"Error": f"Could not read metadata: {str(e)}"}


def get_hashes(image_path):
    """Computes MD5, SHA-1, and SHA-256 hashes for a file."""
    hashes = {}
    try:
        with open(image_path, "rb") as f:
            data = f.read()
            hashes["MD5"] = hashlib.md5(data).hexdigest()
            hashes["SHA-1"] = hashlib.sha1(data).hexdigest()
            hashes["SHA-256"] = hashlib.sha256(data).hexdigest()
        return hashes
    except Exception as e:
        return {"Error": f"Could not compute hashes: {str(e)}"}


def perform_ela(image_path, quality=90, scale=15):
    """Performs Error Level Analysis (ELA) on an image."""
    try:
        original_img = Image.open(image_path).convert("RGB")

        # In-memory buffer for re-saved image
        buffer = io.BytesIO()
        original_img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

        resaved_img = Image.open(buffer)

        # Find difference
        ela_img = ImageChops.difference(original_img, resaved_img)

        # Enhance brightness to make differences visible
        enhancer = ImageEnhance.Brightness(ela_img)
        ela_img = enhancer.enhance(scale)

        # Convert ELA image to base64 string
        ela_buffer = io.BytesIO()
        ela_img.save(ela_buffer, format="JPEG")

        # --- THIS IS THE FIX ---
        ela_b64 = base64.b64encode(ela_buffer.getvalue()).decode("utf-8")

        return ela_b64

    except Exception as e:
        print(f"ELA Error: {e}")
        return None


def analyze_thumbnail(image_path):
    """
    Extracts the embedded thumbnail from EXIF data.
    If the thumbnail doesn't match the main image, it's a strong
    indicator of modification.
    """
    try:
        img = Image.open(image_path)
        exif_data = img.info.get("exif")

        if not exif_data:
            return {
                "status": "no_exif",
                "message": "No EXIF data found, so no thumbnail.",
            }

        exif_dict = piexif.load(exif_data)
        thumbnail_bytes = exif_dict.get("thumbnail")

        if not thumbnail_bytes:
            return {"status": "no_thumbnail", "message": "No embedded thumbnail found."}

        # We found a thumbnail, let's decode it
        try:
            thumb_img = Image.open(io.BytesIO(thumbnail_bytes))

            # Convert thumbnail to base64 to send to frontend
            buf = io.BytesIO()
            thumb_img.save(buf, format="PNG")  # Use PNG for lossless display
            thumb_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            return {
                "status": "found",
                "message": "Embedded thumbnail extracted. Compare it to the main image.",
                "thumbnail_b64": thumb_b64,
            }
        except Exception as e:
            # This can happen if the thumbnail data is corrupt
            return {"status": "error", "message": f"Error decoding thumbnail: {str(e)}"}

    except Exception as e:
        return {"status": "error", "message": f"Error reading image file: {str(e)}"}


def generate_report(analysis_data, report_path):
    """Generates a PDF report summarizing all findings."""
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Digital Image Forensic Report", styles["h1"]))
    story.append(Spacer(1, 0.2 * inch))

    # Filename
    story.append(
        Paragraph(
            f"<b>Analyzed File:</b> {analysis_data['filename']}", styles["Normal"]
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # --- Hashes ---
    story.append(Paragraph("Image Integrity Hashes", styles["h2"]))
    hash_data = [
        ["Algorithm", "Hash Value"],
        ["MD5", analysis_data["hashes"].get("MD5", "N/A")],
        ["SHA-1", analysis_data["hashes"].get("SHA-1", "N/A")],
        ["SHA-256", analysis_data["hashes"].get("SHA-256", "N/A")],
    ]
    hash_table = Table(hash_data, colWidths=[1.5 * inch, 4.5 * inch])
    hash_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(hash_table)
    story.append(Spacer(1, 0.2 * inch))

    # --- Metadata ---
    story.append(Paragraph("Extracted EXIF Metadata", styles["h2"]))
    metadata = analysis_data["metadata"]
    if metadata:
        meta_data_list = [[k, str(v)] for k, v in metadata.items()]
    else:
        meta_data_list = [["Status", "No metadata found."]]

    meta_table = Table(meta_data_list, colWidths=[2 * inch, 4 * inch])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 0.2 * inch))

    # --- ELA Analysis ---
    story.append(Paragraph("Error Level Analysis (ELA)", styles["h2"]))
    story.append(
        Paragraph(
            "Regions with high variation (brighter areas) may indicate "
            "potential digital alteration, as they have a different "
            "compression history from the rest of the image.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    if analysis_data["ela_b64"]:
        try:
            ela_img_data = base64.b64decode(analysis_data["ela_b64"])
            ela_img_stream = io.BytesIO(ela_img_data)

            # Resize image to fit page width AND height
            img = Image.open(ela_img_stream)
            img_width, img_height = img.size

            # Define max bounds for the image in the PDF
            max_width = 6 * inch  # 432 points
            max_height = 8 * inch  # 576 points (leaving space)

            # Calculate aspect ratio
            aspect = img_height / float(img_width)

            # Calculate new dimensions based on max width
            display_width = max_width
            display_height = display_width * aspect

            # Check if height is too much, if so, scale by height instead
            if display_height > max_height:
                display_height = max_height
                display_width = display_height / aspect

            story.append(
                ReportImage(ela_img_stream, width=display_width, height=display_height)
            )

        except Exception as e:
            story.append(
                Paragraph(f"Could not render ELA image: {e}", styles["Normal"])
            )
    else:
        story.append(Paragraph("ELA could not be performed.", styles["Normal"]))

    doc.build(story)
