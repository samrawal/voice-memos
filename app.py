from flask import Flask, request, render_template, jsonify
import os
import pathlib
import google.generativeai as genai
from werkzeug.utils import secure_filename
import markdown 

# Configure Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Initialize Gemini model
model = genai.GenerativeModel('models/gemini-1.5-flash')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    custom_instructions = request.form.get('custom_instructions', '').strip()

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Generate summary using Gemini API with custom instructions
        summary = process_audio(file_path, custom_instructions)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return jsonify({"summary": summary})

def process_audio(file_path, custom_instructions):
    # Base prompt for the Gemini model
    base_prompt = """
Given this voice memo, return the following. Use markdown format:

# Transcription
A transcription of the voice memo. You can clean it up by removing "ums", but don't add or remove any significant words. Feel free to add line breaks to make it readable. Make this collapsible HTML.

# Notes
Capture the contents of the voice memo in a structured manner. Use subheadings, bullets, emphasis, etc. as needed to make the notes clear, organized, and readable.
    """.strip()
    
    # Add custom instructions if provided
    if custom_instructions:
        base_prompt += f" Follow the following user Custom Instructions: \"{custom_instructions}\""

    # Load the audio file into a Python Blob object containing the audio's bytes
    audio_data = pathlib.Path(file_path).read_bytes()
    
    # Pass the prompt and the audio to Gemini
    response = model.generate_content([
        base_prompt,
        {
            "mime_type": "audio/mp3",
            "data": audio_data
        }
    ])
    
    # Return the summary text from Gemini's response
    return markdown.markdown(response.text)

if __name__ == '__main__':
    app.run(debug=True, port=9998)  # Changed port to 9998
