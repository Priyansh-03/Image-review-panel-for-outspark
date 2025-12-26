# Image Review Panel for Outspark

A web-based tool for reviewing and managing user-generated images with defect tracking and commenting capabilities.

## Features

- **User Management**: Browse and filter users with image generation data
- **Review Workflow**: Mark images as defective and add comments
- **Reviewed Tab**: Filter to see only reviewed items
- **Image Lightbox**: Full-screen image viewing
- **Export Options**: Export to CSV or Excel format (all data or reviewed items only)
- **Delete & Edit**: Remove images or clear comments
- **Individual Context**: Each image preserves its unique content

## Installation

1. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python3 main.py
```

4. Open browser to: `http://localhost:5000`

## Usage

1. Upload CSV/Excel file with columns: `userId`, `url`, `title`, `content`
2. Select users from sidebar to review their images
3. Mark defective images and add comments
4. Use "Reviewed" tab to see your progress
5. Export results when done

## Tech Stack

- **Backend**: Flask, Pandas, OpenPyXL
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Custom CSS with glassmorphism design
