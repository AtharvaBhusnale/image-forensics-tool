import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import forensics_utils

# Configuration
UPLOAD_FOLDER = "uploads"
REPORT_FOLDER = "reports"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORT_FOLDER"] = REPORT_FOLDER

# Enable Cross-Origin Resource Sharing (CORS)
CORS(app)


# --- Helper Function ---
def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Create directories if they don't exist ---
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- API Endpoints ---


@app.route("/analyze", methods=["POST"])
def analyze_image():
    """
    Main analysis endpoint.
    Receives an image, performs all analyses, generates a report,
    and returns a JSON summary.
    """
    # 1. Check if the file is present
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]

    # 2. Check if the filename is valid
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # 3. Check if the file type is allowed and secure
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        img_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(img_path)

        try:
            # 4. Perform Forensic Analysis
            metadata = forensics_utils.get_metadata(img_path)
            hashes = forensics_utils.get_hashes(img_path)
            ela_b64 = forensics_utils.perform_ela(img_path)
            thumbnail_analysis = forensics_utils.analyze_thumbnail(
                img_path
            )  # <-- UPDATED

            # 5. Prepare data for report
            report_filename = f"report_{os.path.splitext(filename)[0]}.pdf"
            report_path = os.path.join(app.config["REPORT_FOLDER"], report_filename)

            analysis_data = {
                "filename": filename,
                "metadata": metadata,
                "hashes": hashes,
                "ela_b64": ela_b64,
                "thumbnail_analysis": thumbnail_analysis,  # <-- UPDATED
            }

            # 6. Generate PDF Report
            forensics_utils.generate_report(analysis_data, report_path)

            # 7. Clean up uploaded file
            os.remove(img_path)

            # 8. Return JSON response
            return jsonify(
                {
                    "filename": filename,
                    "metadata": metadata,
                    "hashes": hashes,
                    "ela_b64": ela_b64,
                    "thumbnail_analysis": thumbnail_analysis,  # <-- UPDATED
                    "report_url": f"/reports/{report_filename}",
                }
            )

        except Exception as e:
            # Clean up on error
            if os.path.exists(img_path):
                os.remove(img_path)
            return jsonify(
                {"error": f"An error occurred during analysis: {str(e)}"}
            ), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400


@app.route("/reports/<filename>", methods=["GET"])
def get_report(filename):
    """Serves the generated PDF report for download."""
    try:
        return send_from_directory(
            app.config["REPORT_FOLDER"], filename, as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({"error": "Report not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
