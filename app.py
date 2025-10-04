from flask import Flask, render_template, request, jsonify
import PyPDF2
from docx import Document
import io
import http.client
import urllib.parse
import json
import requests
import os
import logging

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_MODEL = "gemma2-9b-it"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

INDEED_API_KEY = os.environ.get('INDEED_API_KEY', "caec2dd3c7mshba30a0af1c5df30p16b963jsnf0646e1a05b8")
INDEED_API_HOST = "indeed12.p.rapidapi.com"

def extract_text_from_pdf(file_stream):
    try:
        pdf_reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return None

def extract_text_from_docx(file_stream):
    try:
        doc = Document(file_stream)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        return None

def analyze_resume_groq(resume_text):
    try:
        prompt = f"""
        Analyze this resume and tell me the main technical skill or task the person is specialized in.
        Provide only the main skill/task as a single short phrase.

        Resume:
        {resume_text}
        """
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are a resume analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 50,
            "temperature": 0.2
        }

        print(f"Making request to Groq API with model: {GROQ_MODEL}")
        response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)
        print(f"Groq API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            main_task = result['choices'][0]['message']['content'].strip()
            print(f"Analysis result: {main_task}")
            return main_task
        else:
            print(f"Groq API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error in analyze_resume_groq: {str(e)}")
        return None

def fetch_internships(skill, locality="in", start=0):
    try:
        conn = http.client.HTTPSConnection(INDEED_API_HOST)

        headers = {
            "x-rapidapi-key": INDEED_API_KEY,
            "x-rapidapi-host": INDEED_API_HOST
        }

        query = urllib.parse.urlencode({
            "query": skill + " Internship",
            "locality": locality,
            "start": start
        })

        endpoint = f"/jobs/search?{query}"
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        jobs = json.loads(data)
        hits = jobs.get("hits", [])
        return hits
    except Exception as e:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    
    if not file.filename or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = file.filename.lower()
    
    if filename.endswith('.pdf'):
        resume_text = extract_text_from_pdf(file.stream)
    elif filename.endswith('.docx'):
        resume_text = extract_text_from_docx(file.stream)
    else:
        return jsonify({'error': 'Invalid file format. Please upload PDF or DOCX'}), 400
    
    if not resume_text:
        return jsonify({'error': 'Could not extract text from file'}), 400
    
    preview = resume_text[:500] + ("..." if len(resume_text) > 500 else "")
    
    return jsonify({
        'success': True,
        'preview': preview,
        'full_text': resume_text
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        resume_text = data.get('resume_text', '')
        
        if not resume_text:
            return jsonify({'error': 'No resume text provided'}), 400
        
        print(f"Analyzing resume text (length: {len(resume_text)})")
        main_skill = analyze_resume_groq(resume_text)
        
        if not main_skill:
            return jsonify({'error': 'Could not analyze resume with Groq API'}), 500
        
        print(f"Fetching jobs for skill: {main_skill}")
        jobs_data = fetch_internships(main_skill)
        
        if jobs_data is None:
            return jsonify({'error': 'Could not fetch internships from Indeed API'}), 500
        
        jobs_list = []
        for job in jobs_data[:10]:
            jobs_list.append({
                'title': job.get('title', 'N/A'),
                'company': job.get('company_name', 'N/A'),
                'location': job.get('location', 'N/A'),
                'link': f"https://in.indeed.com{job.get('link', '')}"
            })
        
        return jsonify({
            'success': True,
            'skill': main_skill,
            'jobs': jobs_list
        })
    except Exception as e:
        print(f"Error in analyze endpoint: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
