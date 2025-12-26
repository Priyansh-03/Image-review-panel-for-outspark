import os
import pandas as pd
from flask import Flask, request, jsonify, render_template, send_file
import io

app = Flask(__name__)

# --- Helper Functions ---
def parse_file(file):
    filename = file.filename
    if filename.endswith('.csv'):
        df = pd.read_csv(file)
    elif filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file)
    else:
        raise ValueError("Unsupported file format")
    
    # Normalize columns: remove whitespace
    df.columns = df.columns.str.strip()
    return df

def clean_data(df):
    """
    Cleans the dataframe to ensure we have the necessary columns.
    Expected columns: userId, url, title, content
    """
    df = df.copy()
    # Ensure required columns exist (case-insensitive check could be added if needed)
    required = ['userId', 'url', 'title', 'content']
    missing = [c for c in required if c not in df.columns]
    if missing:
        # Try to guess case insensitive
        for m in missing:
            found = False
            for c in df.columns:
                if c.lower() == m.lower():
                    df.rename(columns={c: m}, inplace=True)
                    found = True
                    break
            if not found:
                 # If still missing, we might need to handle it or error out. 
                 # For now, let's just make them empty strings if missing? 
                 # Or better, just error if userId or url is missing.
                 pass
    
    # Fill NaNs
    df.fillna('', inplace=True)
    return df

def transform_to_hierarchy(df):
    """
    Transforms flat DataFrame into a hierarchical structure:
    User -> Prompts (Title) -> Images
    """
    # Group by User ID first
    users_data = {}
    
    grouped_users = df.groupby('userId')
    
    for user_id, user_group in grouped_users:
        user_id_str = str(user_id)
        users_data[user_id_str] = {
            'userId': user_id_str,
            'prompts': {}
        }
        
        # Group by Title (Prompt) within the user
        grouped_prompts = user_group.groupby('title')
        
        for title, prompt_group in grouped_prompts:
            # We want to keep track of images under this prompt
            # Also, 'content' might be the same for the prompt, or specific to image?
            # Usually content is prompt text? prompt_group['content'].iloc[0]
            
            # Let's assume content acts as the full prompt description
            prompt_content = prompt_group['content'].iloc[0] if 'content' in prompt_group.columns else ''
            
            users_data[user_id_str]['prompts'][title] = {
                'title': title,
                'content': prompt_content,
                'images': []
            }
            
            for _, row in prompt_group.iterrows():
                users_data[user_id_str]['prompts'][title]['images'].append({
                    'url': row['url'],
                    'content': row['content'] if 'content' in row else prompt_content,  # Preserve individual content
                    'original_row_index': _ , # might be useful for tracking but we just re-export
                    # Add any other fields you want to preserve here
                })
                
    return users_data

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    try:
        df = parse_file(file)
        df = clean_data(df)
        data = transform_to_hierarchy(df)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export', methods=['POST'])
def export_file():
    try:
        # Expecting JSON data with list of users, their prompts, and images marked with 'defective' and 'comment'
        req_data = request.json
        users_data = req_data.get('data', {})
        export_format = req_data.get('format', 'xlsx') # 'csv' or 'xlsx'
        reviewed_only = req_data.get('reviewed_only', False)
        
        # Flatten the data back to list of dicts
        flat_data = []
        
        for user_id, user_info in users_data.items():
            prompts = user_info.get('prompts', {})
            for title, prompt_info in prompts.items():
                content = prompt_info.get('content', '')
                images = prompt_info.get('images', [])
                
                for img in images:
                    is_defective = img.get('is_defective', False)
                    review_comment = img.get('review_comment', '')
                    
                    # Filter if requested
                    if reviewed_only:
                        if not is_defective and not review_comment:
                            continue

                    row = {
                        'userId': user_id,
                        'title': title,
                        'content': content,
                        'url': img.get('url', ''),
                        'is_defective': is_defective,
                        'review_comment': review_comment
                    }
                    flat_data.append(row)
        
        if not flat_data and reviewed_only:
             # If filter results in empty data, but we need to return something valid or error
             # Let's return empty file or handle gracefully?
             pass 

        df = pd.DataFrame(flat_data)
        
        if export_format == 'csv':
            output = io.BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            mimetype = 'text/csv'
            fname = 'reviewed_images.csv'
        else:
            # Excel default
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            fname = 'reviewed_images.xlsx'

        
        return send_file(
            output,
            as_attachment=True,
            download_name=fname,
            mimetype=mimetype
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use port from environment variable or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
