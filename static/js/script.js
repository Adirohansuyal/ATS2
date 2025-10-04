let resumeText = '';

document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadSection = document.getElementById('uploadSection');
    const resumePreview = document.getElementById('resumePreview');
    const previewContent = document.getElementById('previewContent');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const changeFileBtn = document.getElementById('changeFileBtn');
    const resultsSection = document.getElementById('resultsSection');
    const skillBadge = document.getElementById('skillBadge');
    const jobsList = document.getElementById('jobsList');
    const loader = document.getElementById('loader');
    const loaderText = document.getElementById('loaderText');

    browseBtn.onclick = function() {
        fileInput.click();
    };

    fileInput.onchange = function(e) {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    };

    changeFileBtn.onclick = function() {
        resumePreview.style.display = 'none';
        uploadSection.style.display = 'block';
        resultsSection.style.display = 'none';
        fileInput.value = '';
        resumeText = '';
    };

    analyzeBtn.onclick = analyzeResume;

    function handleFileUpload(file) {
        const fileName = file.name.toLowerCase();
        
        if (!fileName.endsWith('.pdf') && !fileName.endsWith('.docx')) {
            alert('Please upload a PDF or DOCX file');
            return;
        }
        
        showLoader('Uploading your resume...');
        
        const formData = new FormData();
        formData.append('resume', file);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoader();
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }
            
            resumeText = data.full_text;
            previewContent.textContent = data.preview;
            uploadSection.style.display = 'none';
            resumePreview.style.display = 'block';
            resultsSection.style.display = 'none';
        })
        .catch(error => {
            hideLoader();
            alert('Error uploading file: ' + error.message);
        });
    }

    function analyzeResume() {
        if (!resumeText) {
            alert('Please upload a resume first');
            return;
        }
        
        showLoader('Analyzing your resume with AI...');
        
        fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ resume_text: resumeText })
        })
        .then(response => response.json())
        .then(data => {
            hideLoader();
            
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }
            
            skillBadge.textContent = data.skill;
            
            jobsList.innerHTML = '';
            if (data.jobs && data.jobs.length > 0) {
                data.jobs.forEach((job, index) => {
                    const jobCard = createJobCard(job, index + 1);
                    jobsList.appendChild(jobCard);
                });
            } else {
                jobsList.innerHTML = '<div class="no-jobs">No internships found at the moment. Try again later!</div>';
            }
            
            resultsSection.style.display = 'block';
            setTimeout(() => {
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }, 100);
        })
        .catch(error => {
            hideLoader();
            alert('Error analyzing resume: ' + error.message);
        });
    }

    function createJobCard(job, number) {
        const card = document.createElement('div');
        card.className = 'job-card';
        
        card.innerHTML = `
            <div class="job-title">
                <span class="job-number">${number}</span>
                ${job.title}
            </div>
            <div class="job-company">🏢 ${job.company}</div>
            <div class="job-location">📍 ${job.location}</div>
            <a href="${job.link}" target="_blank" class="job-link">Apply Now</a>
        `;
        
        return card;
    }

    function showLoader(text) {
        loaderText.textContent = text;
        loader.style.display = 'flex';
    }

    function hideLoader() {
        loader.style.display = 'none';
    }
});
