<h1><b>AI Engineering Drawing Comparison System</b></h1>

<h2><b>Overview</b></h2>

This project is a full-stack system designed to compare two engineering drawings (PDF or image formats) and identify visual differences using computer vision techniques. It generates structured outputs including difference visualizations, similarity metrics, statistical analysis, and downloadable reports.

The system is built using Flask for the backend and vanilla JavaScript for the frontend, with OpenCV-based processing for image analysis.

<h2><b>Problem Statement</b></h2>

Manual comparison of engineering drawings is time-consuming and error-prone, especially when dealing with complex revisions. There is a need for an automated system that can accurately detect structural and visual differences between two drawings and present the results in a clear and interpretable format.

<h2><b>Solution Approach</b></h2>

The system processes two input drawings through a structured pipeline:

Input Validation
Files are validated for supported formats (PDF, PNG, JPG, JPEG).
Preprocessing
Image resizing
Noise reduction using Gaussian filtering
Contrast enhancement
ORB feature-based alignment
Normalization for consistent comparison
Image Comparison
Structural Similarity Index (SSIM) computation
Threshold-based difference detection
Morphological processing
Contour extraction for changed regions
Statistical computation of changes
Visualization Generation
Bounding box overlay of differences
Heatmap representation
Difference overlay image
Side-by-side comparison view
Summary and Reporting
Automated textual summary of differences
JSON structured output
Human-readable TXT report
Tech Stack

Backend:

Python
Flask
OpenCV
NumPy
scikit-image

Frontend:

HTML
CSS (Bootstrap-based styling)
JavaScript (Vanilla JS)
Project Structure

app.py
config.py
modules/
preprocess.py
compare.py
visualization.py
summary.py
report_generator.py
utils/
file_handler.py
logger.py
templates/
index.html
outputs/
highlighted/
reports/
uploads/
temp/

<h2><b>Features</b></h2>
Upload and compare two engineering drawings
Automatic image preprocessing and alignment
Structural similarity analysis (SSIM)
Visual difference detection with multiple representations
Statistical breakdown of changes
Automated report generation (TXT and JSON)
Web-based interactive interface
API Endpoints
GET /

Returns the main UI for uploading and comparing drawings.

POST /process

Accepts two files and returns comparison results.

Request:

file1: First drawing
file2: Second drawing

Response:

summary: High-level analysis
statistics: Pixel-level and region-level metrics
visualizations: Paths to generated images
reports: Paths to downloadable reports

<h2><b>How to Run the Project</b></h2>
1. Install dependencies

pip install -r requirements.txt

2. Run Flask server

python app.py

3. Open in browser

http://127.0.0.1:5000

<h2><b>Output Description</b></h2>

The system generates the following outputs:
<ul>
<li>Boxes: Highlighted difference regions using bounding boxes</li>
<li>Heatmap: Intensity map of differences</li>
<li>Overlay: Combined difference visualization</li>
<li>Side-by-side: Direct comparison of both drawings</li>
<li>Reports: Structured analysis in TXT and JSON format</li>
</ul>
<h2><b>Current Limitations</b></h2>
Performance depends on input image quality
PDF conversion relies on rasterization accuracy
Alignment may vary for highly distorted drawings
Not optimized for extremely large-scale CAD files

<h2><b>Future Improvements</b></h2>
Integration with CAD-native formats (DWG/DXF)
Deep learning-based defect detection
Cloud deployment for large-scale processing
Real-time collaborative comparison system
Version tracking for engineering revisions
