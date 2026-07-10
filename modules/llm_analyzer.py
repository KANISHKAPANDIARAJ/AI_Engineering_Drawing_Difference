"""
modules/llm_analyzer.py

Leverages Gemini API to analyze engineering drawing revisions based on
SSIM differences, OCR text outputs, and grid coordinate mapping, generating
a professional, multi-dimensional impact report.
"""

from __future__ import annotations

import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any

from config import ProjectConfig
from utils.logger import get_logger


class LLMAnalyzer:
    def __init__(self):
        self.logger = get_logger(__name__)
        self._load_dotenv()

    def _load_dotenv(self) -> None:
        """Load environment variables from project-root .env file if it exists."""
        env_path = ProjectConfig.BASE_DIR / ".env"
        if env_path.exists():
            self.logger.info(f"Loading environment variables from {env_path}")
            try:
                with open(env_path, "r", encoding="utf-8-sig") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            # Remove potential surrounding quotes from values
                            val = val.strip().strip("'\"")
                            os.environ[key.strip()] = val
            except Exception as e:
                self.logger.warning(f"Failed to parse .env file: {e}")

    def _get_api_key(self) -> str | None:
        """Retrieve the Gemini API key from environment variables."""
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def generate_report(self, stats: Dict[str, Any], regions: List[Dict[str, Any]]) -> str:
        """
        Calls Gemini API using urllib to generate a professional engineering drawing
        revision analysis report in markdown format, along with structured descriptions per region.
        """
        api_key = self._get_api_key()
        if not api_key:
            self.logger.warning("Gemini API key is not configured. Skipping LLM report generation.")
            # Set default descriptions for regions
            for idx, box in enumerate(regions, start=1):
                box["description"] = f"Change detected in region {idx} at grid cell {box.get('grid', 'N/A')}."
            return (
                "## AI Revision Analysis & Impact Report\n\n"
                "> [!NOTE]\n"
                "> **AI Report Generation Skipped**: Gemini API Key is missing. "
                "To enable automated engineering analysis, please configure `GEMINI_API_KEY` "
                "in your `.env` file in the project directory."
            )

        self.logger.info("Preparing LLM drawing revision analysis request")

        # Format regions metadata for the prompt
        region_descriptions = []
        for idx, box in enumerate(regions, start=1):
            change_type = box.get("change_type", "Unknown")
            grid = box.get("grid", "N/A")
            before = box.get("before_text")
            after = box.get("after_text")
            
            before_str = f"'{before}'" if before else "[No text/empty]"
            after_str = f"'{after}'" if after else "[No text/empty]"

            region_descriptions.append(
                f"- Region {idx} [Grid {grid}]: {change_type} change. "
                f"Before: {before_str} | After: {after_str}"
            )

        regions_meta = "\n".join(region_descriptions) if region_descriptions else "No changes detected."

        prompt = f"""You are an expert engineering design reviewer and quality control engineer review comparing revision A and B.
Below is the statistical metadata and text extracted via OCR from the changed regions:

==================================================
SUMMARY STATISTICS:
- SSIM Similarity Score: {stats.get('ssim_score', 'N/A')}
- Total Changed Regions: {stats.get('num_regions', 0)}
- Average Region Area (px): {stats.get('average_region_area', 0.0)}
- Severity Level (rule-based): {stats.get('severity', 'UNKNOWN')}

DETECTED CHANGE REGIONS (OCR & GRID DATA):
{regions_meta}
==================================================

Please analyze these drawing changes and output your report in a valid JSON object matching the schema below:
{{
  "report": "A professional, high-grade Engineering Revision Analysis & Impact Report in Markdown format containing: \\n\\n1. **Executive Summary** (reviewing iteration scope & severity)\\n2. **Detailed Revision Notes** (breakdown by grid coordinate)\\n3. **Engineering & Design Impact**\\n4. **Manufacturing & Production Impact**\\n5. **Quality Control & Inspection Notes**\\n6. **Risk Assessment**",
  "regions": [
    {{
      "id": 1,
      "type": "Added | Removed | Modified | Geometry Change",
      "description": "A concise, one-sentence engineering explanation of what changed in this region (e.g. 'Dimension label updated from 25 mm to 29 mm', 'Title block changed', or 'Geometry modified in bridge pier area')"
    }}
  ]
}}

Write only valid JSON. Do not include any greeting or conversational filler.
"""

        # Call Gemini API REST Endpoint using urllib
        # Model: gemini-2.5-flash (excellent for structured text processing & reasoning)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        request_body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        try:
            self.logger.info("Sending request to Gemini API endpoint")
            data = json.dumps(request_body).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                
                # Extract response text safely
                candidates = response_data.get("candidates", [])
                if not candidates:
                    for idx, box in enumerate(regions, start=1):
                        box["description"] = f"Change in region {idx} at Grid {box.get('grid', 'N/A')}."
                    return "Error: No response generated by Gemini model."
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    for idx, box in enumerate(regions, start=1):
                        box["description"] = f"Change in region {idx} at Grid {box.get('grid', 'N/A')}."
                    return "Error: Empty content parts returned by Gemini."
                
                llm_response = parts[0].get("text", "").strip()
                self.logger.info("LLM response received. Parsing JSON.")
                
                try:
                    result_json = json.loads(llm_response)
                    report_text = result_json.get("report", "")
                    
                    # Extract list of region annotations
                    llm_regions = result_json.get("regions", [])
                    region_map = {}
                    for r in llm_regions:
                        if "id" in r:
                            try:
                                r_id = int(r["id"])
                                region_map[r_id] = r
                            except ValueError:
                                continue
                    
                    # Map the AI descriptions and type corrections back to the boxes
                    for idx, box in enumerate(regions, start=1):
                        r_data = region_map.get(idx)
                        if r_data:
                            box["description"] = r_data.get("description", f"Change in region {idx} at Grid {box.get('grid', 'N/A')}.")
                            if "type" in r_data:
                                box["change_type"] = r_data["type"]
                        else:
                            box["description"] = f"Change in region {idx} at Grid {box.get('grid', 'N/A')}."
                    
                    self.logger.info("LLM drawing analysis and region metadata mapped successfully")
                    return report_text

                except Exception as parse_err:
                    self.logger.warning(f"Failed to parse structured JSON from LLM response: {parse_err}")
                    # Fallback to returning raw text and using default description
                    for idx, box in enumerate(regions, start=1):
                        box["description"] = f"Change in region {idx} at Grid {box.get('grid', 'N/A')}."
                    return llm_response

        except urllib.error.HTTPError as http_err:
            error_msg = http_err.read().decode("utf-8")
            self.logger.error(f"Gemini API returned HTTP Error: {http_err.code} - {error_msg}")
            # Fallback descriptions
            for idx, box in enumerate(regions, start=1):
                box["description"] = f"Change in region {idx} at Grid {box.get('grid', 'N/A')}."
            return f"Gemini API Error (HTTP {http_err.code}): Failed to generate analysis report. Check API key."
        except Exception as e:
            self.logger.error(f"Failed to connect or communicate with Gemini API: {e}")
            # Fallback descriptions
            for idx, box in enumerate(regions, start=1):
                box["description"] = f"Change in region {idx} at Grid {box.get('grid', 'N/A')}."
            return f"Error connecting to Gemini API: {str(e)}"
