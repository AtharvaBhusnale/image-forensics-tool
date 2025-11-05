# 🔒 Digital Image Forensics Tool

This is a full-stack web application designed for digital image forensics. It allows users to upload an image and receive a detailed analysis, including:

* **Metadata Analysis**: Extracts and displays all available EXIF data (camera model, software, GPS coordinates, timestamps).
* **Image Integrity**: Computes MD5, SHA-1, and SHA-256 hashes to verify file integrity.
* **Error Level Analysis (ELA)**: Generates an ELA image to highlight potential areas of digital manipulation.
* **PDF Report Generation**: Automatically compiles all findings into a downloadable PDF report.

This tool is built for educational and defensive cybersecurity purposes to help identify image tampering.

## ✨ Features

* **Backend**: Python (Flask) API
* **Frontend**: Simple, single-page HTML/CSS/JS (Bootstrap)
* **Core Libraries**: Pillow, piexif, hashlib, reportlab
* **Secure Uploads**: Validates file types (JPG, PNG) and sanitizes filenames.
* **Clear Visualization**: Presents metadata in tables and displays the ELA result directly.

## 📂 Project Structure

```
digital-forensics-tool/
|
|-- backend/
|   |-- app.py             # Main Flask API server
|   |-- forensics_utils.py # Core logic (metadata, ELA, hash, PDF)
|   |-- requirements.txt   # Python dependencies
|   |-- uploads/           # (Created by app.py for temp storage)
|   |-- reports/           # (Created by app.py for PDF reports)
|
|-- frontend/
|   |-- index.html         # Single-page frontend
|
|-- README.md            # This file
```

## 🛠️ Installation and Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd digital-forensics-tool
```

### 2. Set Up the Backend (Python)

It is highly recommended to use a virtual environment.

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source vv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install the required Python packages
pip install -r requirements.txt
```

## 🚀 Running the Application

You will need to run the backend server and open the frontend file separately.

### 1. Run the Backend Server

Make sure you are in the `backend/` directory with your virtual environment activated.

```bash
flask run
```

The server will start, typically at `http://127.0.0.1:5000`. Keep this terminal window open.

### 2. Launch the Frontend

Navigate to the `frontend/` directory and open the `index.html` file directly in your web browser (e.g., Chrome, Firefox).

* You can right-click the file and choose "Open with..."
* Or, in your terminal, you can use:
    * `open frontend/index.html` (macOS)
    * `start frontend/index.html` (Windows)
    * `xdg-open frontend/index.html` (Linux)

### 3. Usage

1.  The webpage will load in your browser.
2.  Drag and drop an image or click to select a `.jpg` or `.png` file.
3.  Click the "Analyze Image" button.
4.  The tool will process the image, and the results (Metadata, Hashes, ELA, and Thumbnail) will appear on the page.
5.  Click the "Download Full PDF Report" button to get the complete report.

---
