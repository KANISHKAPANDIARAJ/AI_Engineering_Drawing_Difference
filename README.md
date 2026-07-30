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
<h2><b>System Architecture</b></h2>

                    +-------------------------+
                    |      User Browser       |
                    +-----------+-------------+
                                |
                                |
                         Upload Drawings
                                |
                                v
                     +----------------------+
                     |      Flask App       |
                     |       (app.py)       |
                     +----------+-----------+
                                |
                                |
        ----------------------------------------------------
        |                  Main Processing Pipeline          |
        ----------------------------------------------------
                                |
                                v
                    +------------------------+
                    | Input Validation       |
                    | validate_file()        |
                    +-----------+------------+
                                |
                                v
                    +------------------------+
                    | Save Uploaded Files    |
                    | save_upload()          |
                    +-----------+------------+
                                |
                                v
                 +-----------------------------+
                 | Image Preprocessor          |
                 | preprocess.py               |
                 |                             |
                 | • PDF Conversion            |
                 | • Resize                    |
                 | • Gaussian Blur             |
                 | • ORB Alignment             |
                 | • Homography                |
                 +-------------+---------------+
                               |
                               v
                 +-----------------------------+
                 | Image Comparator            |
                 | compare.py                  |
                 |                             |
                 | • SSIM                      |
                 | • Thresholding              |
                 | • Morphology                |
                 | • Contours                  |
                 | • Bounding Boxes            |
                 +-------------+---------------+
                               |
                               v
                 +-----------------------------+
                 | OCR Extractor               |
                 | ocr_extractor.py            |
                 |                             |
                 | • Text Detection            |
                 | • Before Text               |
                 | • After Text                |
                 +-------------+---------------+
                               |
                               v
                 +-----------------------------+
                 | LLM Analyzer                |
                 | llm_analyzer.py             |
                 |                             |
                 | • AI Summary                |
                 | • Revision Analysis         |
                 | • Recommendations           |
                 +-------------+---------------+
                               |
                               v
                 +-----------------------------+
                 | Summary Generator           |
                 | summary.py                  |
                 |                             |
                 | • Similarity Score          |
                 | • Severity                  |
                 | • Statistics                |
                 +-------------+---------------+
                               |
                               v
                 +-----------------------------+
                 | Visualization Generator     |
                 | visualization.py            |
                 |                             |
                 | • Boxes                     |
                 | • Overlay                   |
                 | • Heatmap                   |
                 | • Side-by-Side              |
                 +-------------+---------------+
                               |
                               v
                 +-----------------------------+
                 | Report Generator            |
                 | report_generator.py         |
                 |                             |
                 | • TXT                       |
                 | • JSON                      |
                 | • Markdown                  |
                 | • HTML Report               |
                 +-------------+---------------+
                               |
                               v
                   outputs/
                   ├── highlighted/
                   ├── reports/
                   └── last_result.json
                               |
                               v
                     Flask Response (JSON)
                               |
                               v
                  Dashboard (Vanilla JavaScript)
                               |
                               |
        --------------------------------------------------
        | Dashboard Features                              |
        --------------------------------------------------
        | • Similarity Gauge                              |
        | • Change Statistics                             |
        | • Drawing Viewer                               |
        | • AI Summary                                   |
        | • Region Table                                 |
        | • Heatmap                                      |
        | • Overlay                                      |
        | • Download Reports                             |
        --------------------------------------------------



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

<h3><b>Project Structure</b></h3>

| Folder / File               | Description                                                                                                 |
| --------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **app.py**                  | Entry point of the Flask application. Handles routes, file uploads, processing pipeline, and API responses. |
| **config.py**               | Stores project configurations such as paths, host, port, API keys, and application settings.                |
| **requirements.txt**        | Lists all Python dependencies required to run the project.                                                  |
| **modules/**                | Contains the core processing modules used in the comparison pipeline.                                       |
| ├── **preprocess.py**       | Converts PDFs to images, resizes, aligns drawings using ORB, and performs preprocessing.                    |
| ├── **compare.py**          | Performs SSIM comparison, difference detection, contour extraction, and region identification.              |
| ├── **ocr_extractor.py**    | Extracts text from changed regions using OCR for before/after comparison.                                   |
| ├── **llm_analyzer.py**     | Generates AI-powered engineering revision summaries and recommendations using an LLM.                       |
| ├── **summary.py**          | Calculates similarity score, severity level, and overall statistics.                                        |
| ├── **visualization.py**    | Generates bounding-box images, overlays, heatmaps, and side-by-side comparisons.                            |
| └── **report_generator.py** | Creates TXT, JSON, Markdown, and printable report files.                                                    |
| **utils/**                  | Utility functions used throughout the application.                                                          |
| ├── **file_handler.py**     | Handles file validation, uploads, cleanup, and folder creation.                                             |
| ├── **pdf_utils.py**        | Provides helper functions for PDF processing and conversion.                                                |
| ├── **logger.py**           | Configures logging for debugging and application monitoring.                                                |
| └── **constants.py**        | Stores reusable constants used across the project.                                                          |
| **templates/**              | Jinja2 HTML templates rendered by Flask.                                                                    |
| ├── **layout.html**         | Common layout shared by all pages.                                                                          |
| ├── **index.html**          | Main dashboard for uploading and comparing drawings.                                                        |
| └── **report.html**         | Printable HTML report generated after comparison.                                                           |
| **static/**                 | Frontend static assets.                                                                                     |
| ├── **css/**                | Stylesheets for the web interface.                                                                          |
| ├── **js/**                 | JavaScript controlling the dashboard and API communication.                                                 |
| └── **images/**             | Static images and icons used in the interface.                                                              |
| **outputs/**                | Stores generated outputs after each comparison.                                                             |
| ├── **highlighted/**        | Generated visualization images (boxes, overlays, heatmaps, etc.).                                           |
| ├── **reports/**            | Generated TXT, JSON, Markdown, and downloadable reports.                                                    |
| └── **last_result.json**    | Cached comparison result used by the report page.                                                           |
| **uploads/**                | Stores uploaded drawing files during processing.                                                            |
| **temp/**                   | Temporary working directory used while processing files.                                                    |


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
