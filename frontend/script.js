const API_BASE = 'http://127.0.0.1:8000';
let currentToken = localStorage.getItem('token');
let currentProjectId = null;

// DOM Elements
const sections = {
    home: document.getElementById('homeSection'),
    login: document.getElementById('loginSection'),
    register: document.getElementById('registerSection'),
    upload: document.getElementById('uploadSection'),
    dashboard: document.getElementById('dashboardSection'),
    analysis: document.getElementById('analysisSection')
};

const navButtons = {
    home: document.getElementById('homeBtn'),
    dashboard: document.getElementById('dashboardBtn'),
    upload: document.getElementById('uploadBtn'),
    login: document.getElementById('loginBtn'),
    logout: document.getElementById('logoutBtn')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupAuthForms();
    setupUploadForms();
    setupAnalysisTabs();
    
    if (currentToken) {
        updateAuthUI(true);
        showSection('dashboard');
        loadProjects();
    }
});

// Utility Functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    }
}

function hideLoading(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Navigation
function setupNavigation() {
    navButtons.home.addEventListener('click', () => showSection('home'));
    navButtons.dashboard.addEventListener('click', () => {
        if (currentToken) {
            showSection('dashboard');
            loadProjects();
        } else {
            showSection('login');
        }
    });
    navButtons.upload.addEventListener('click', () => {
        if (currentToken) {
            showSection('upload');
        } else {
            showSection('login');
        }
    });
    navButtons.login.addEventListener('click', () => showSection('login'));
    navButtons.logout.addEventListener('click', logout);
    
    document.getElementById('getStartedBtn').addEventListener('click', () => {
        if (currentToken) {
            showSection('upload');
        } else {
            showSection('register');
        }
    });
    
    document.getElementById('showRegister').addEventListener('click', (e) => {
        e.preventDefault();
        showSection('register');
    });
    
    document.getElementById('showLogin').addEventListener('click', (e) => {
        e.preventDefault();
        showSection('login');
    });
    
    document.getElementById('backToDashboard').addEventListener('click', () => {
        showSection('dashboard');
        loadProjects();
    });
}

function showSection(sectionName) {
    Object.values(sections).forEach(section => section.classList.remove('active'));
    Object.values(navButtons).forEach(btn => btn.classList.remove('active'));
    
    sections[sectionName].classList.add('active');
    
    if (navButtons[sectionName]) {
        navButtons[sectionName].classList.add('active');
    }
}

// Authentication
function setupAuthForms() {
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = e.target.querySelector('.submit-button');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Logging in...';
        submitBtn.disabled = true;
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
            const response = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                const data = await response.json();
                currentToken = data.access_token;
                localStorage.setItem('token', currentToken);
                updateAuthUI(true);
                showSection('dashboard');
                loadProjects();
                showToast('Login successful!');
            } else {
                const error = await response.json();
                showToast(error.detail || 'Login failed', 'error');
            }
        } catch (error) {
            showToast('Login failed: ' + error.message, 'error');
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
    
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = e.target.querySelector('.submit-button');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Creating account...';
        submitBtn.disabled = true;
        
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        
        try {
            const response = await fetch(`${API_BASE}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password })
            });
            
            if (response.ok) {
                showToast('Registration successful! Please login.');
                showSection('login');
            } else {
                const error = await response.json();
                showToast(error.detail || 'Registration failed', 'error');
            }
        } catch (error) {
            showToast('Registration failed: ' + error.message, 'error');
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
}

function logout() {
    currentToken = null;
    localStorage.removeItem('token');
    updateAuthUI(false);
    showSection('home');
}

function updateAuthUI(isLoggedIn) {
    if (isLoggedIn) {
        navButtons.login.classList.add('hidden');
        navButtons.logout.classList.remove('hidden');
    } else {
        navButtons.login.classList.remove('hidden');
        navButtons.logout.classList.add('hidden');
    }
}

// Upload Forms
function setupUploadForms() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`${btn.dataset.tab}Tab`).classList.add('active');
        });
    });
    
    // ZIP Upload
    document.getElementById('zipUploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = e.target.querySelector('.submit-button');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Uploading...';
        submitBtn.disabled = true;
        
        const name = document.getElementById('projectName').value;
        const description = document.getElementById('projectDescription').value;
        const fileInput = document.getElementById('zipFile');
        
        if (fileInput.files.length === 0) {
            showToast('Please select a ZIP file', 'error');
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('name', name);
        formData.append('description', description);
        
        try {
            const response = await fetch(`${API_BASE}/projects/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${currentToken}`
                },
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                showToast('Project uploaded successfully!');
                
                // Automatically analyze the project
                submitBtn.textContent = 'Analyzing...';
                await analyzeProject(data.project_id);
            } else {
                const error = await response.json();
                showToast(error.detail || 'Upload failed', 'error');
            }
        } catch (error) {
            showToast('Upload failed: ' + error.message, 'error');
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
    
    // GitHub Upload
    document.getElementById('githubUploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = e.target.querySelector('.submit-button');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Adding repository...';
        submitBtn.disabled = true;
        
        const name = document.getElementById('githubProjectName').value;
        const description = document.getElementById('githubDescription').value;
        const source_url = document.getElementById('githubUrl').value;
        
        try {
            const response = await fetch(`${API_BASE}/projects/github`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${currentToken}`
                },
                body: JSON.stringify({
                    name,
                    description,
                    source_type: 'github',
                    source_url
                })
            });
            
            if (response.ok) {
                showToast('GitHub project added successfully!');
                showSection('dashboard');
                loadProjects();
            } else {
                const error = await response.json();
                showToast(error.detail || 'Failed to add GitHub project', 'error');
            }
        } catch (error) {
            showToast('Failed to add GitHub project: ' + error.message, 'error');
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
}

// Projects
async function loadProjects() {
    showLoading('projectsList');

    try {
        const response = await fetch(`${API_BASE}/projects`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayProjects(data.projects);
        } else {
            hideLoading('projectsList', '<p class="no-projects">Failed to load projects. Please try again.</p>');
        }
    } catch (error) {
        console.error('Failed to load projects:', error);
        hideLoading('projectsList', '<p class="no-projects">Failed to load projects. Please try again.</p>');
    }
}

function displayProjects(projects) {
    const projectsList = document.getElementById('projectsList');
    
    if (projects.length === 0) {
        projectsList.innerHTML = '<p class="no-projects">No projects uploaded yet. Upload your first project to get started!</p>';
        return;
    }
    
    // Quick GitHub Upload from Dashboard
    document.getElementById('quickGithubForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('quickGithubName').value;
        const source_url = document.getElementById('quickGithubUrl').value;
        
        try {
            const response = await fetch(`${API_BASE}/projects/github`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${currentToken}`
                },
                body: JSON.stringify({
                    name,
                    description: '',
                    source_type: 'github',
                    source_url
                })
            });
            
            if (response.ok) {
                showToast('GitHub project added successfully!');
                document.getElementById('quickGithubForm').reset();
                loadProjects();
            } else {
                const error = await response.json();
                showToast(error.detail || 'Failed to add GitHub project', 'error');
            }
        } catch (error) {
            showToast('Failed to add GitHub project: ' + error.message, 'error');
        }
    });
    
    projectsList.innerHTML = projects.map(project => `
        <div class="project-card">
            <div onclick="viewProject(${project.id})" style="cursor: pointer;">
                <h3>${project.name}</h3>
                <p>${project.description || 'No description'}</p>
                <div class="project-meta">
                    <span>📦 ${project.source_type}</span>
                    <span>📅 ${new Date(project.created_at).toLocaleDateString()}</span>
                </div>
            </div>
            <div class="project-actions">
                <button class="analyze-btn" onclick="event.stopPropagation(); analyzeProject(${project.id})">🔍 Analyze</button>
                <button class="delete-btn" onclick="event.stopPropagation(); deleteProject(${project.id})">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
}

async function viewProject(projectId) {
    currentProjectId = projectId;
    
    try {
        // Get project details
        const projectResponse = await fetch(`${API_BASE}/projects/${projectId}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (projectResponse.ok) {
            const project = await projectResponse.json();
            document.getElementById('analysisProjectName').textContent = project.name;
        }
        
        // Check if analysis exists
        const analysisResponse = await fetch(`${API_BASE}/projects/${projectId}/analysis`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (analysisResponse.ok) {
            const analysis = await analysisResponse.json();
            displayAnalysis(analysis);
        } else {
            // Trigger analysis
            await analyzeProject(projectId);
        }
        
        showSection('analysis');
    } catch (error) {
        console.error('Failed to view project:', error);
    }
}

async function analyzeProject(projectId) {
    try {
        const response = await fetch(`${API_BASE}/projects/${projectId}/analyze`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.results) {
                displayAnalysis(data.results);
            }
            if (data.ml_results) {
                displayAIInsights(data.ml_results);
            }
            showToast('Analysis completed successfully!', 'success');
            showSection('analysis');
        } else {
            const error = await response.json();
            console.error('Analysis failed:', error.detail);
            showToast('Analysis failed. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Analysis failed:', error);
        showToast('Analysis failed. Please try again.', 'error');
    }
}

async function deleteProject(projectId) {
    if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/projects/${projectId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (response.ok) {
            showToast('Project deleted successfully!', 'success');
            loadProjects(); // Reload the project list
        } else {
            const error = await response.json();
            console.error('Delete failed:', error.detail);
            showToast('Failed to delete project.', 'error');
        }
    } catch (error) {
        console.error('Delete failed:', error);
        showToast('Failed to delete project.', 'error');
    }
}

function displayAIInsights(mlResults) {
    const container = document.getElementById('aiInsightsContent');
    
    if (!mlResults || Object.keys(mlResults).length === 0) {
        container.innerHTML = '<p class="no-projects">No AI insights available for this project.</p>';
        return;
    }
    
    let html = '<div class="ai-insights-grid">';
    
    // Code Quality Analysis
    if (mlResults.code_quality && Object.keys(mlResults.code_quality).length > 0) {
        html += '<div class="ai-section">';
        html += '<h4>📊 Code Quality Analysis</h4>';
        
        let totalScore = 0;
        let fileCount = 0;
        
        for (const [file, quality] of Object.entries(mlResults.code_quality)) {
            totalScore += quality.overall_score || 0;
            fileCount++;
            
            html += `<div class="ai-file-result">
                <div class="ai-file-name">${file}</div>
                <div class="ai-score-badge ${getScoreClass(quality.overall_score)}">${quality.overall_score || 0}/100</div>
                <div class="ai-quality-level">${quality.quality_level || 'Unknown'}</div>
            </div>`;
            
            if (quality.recommendations && quality.recommendations.length > 0) {
                html += '<div class="ai-recommendations">';
                html += '<strong>Recommendations:</strong><ul>';
                quality.recommendations.forEach(rec => {
                    html += `<li>${rec}</li>`;
                });
                html += '</ul></div>';
            }
        }
        
        const avgScore = fileCount > 0 ? Math.round(totalScore / fileCount) : 0;
        html += `<div class="ai-summary">
            <strong>Average Quality Score: ${avgScore}/100</strong>
        </div>`;
        
        html += '</div>';
    }
    
    // Bug Detection
    if (mlResults.bug_detection && Object.keys(mlResults.bug_detection).length > 0) {
        html += '<div class="ai-section">';
        html += '<h4>🐛 Bug Detection</h4>';
        
        let totalBugs = 0;
        
        for (const [file, bugs] of Object.entries(mlResults.bug_detection)) {
            totalBugs += bugs.total_bugs || 0;
            
            if (bugs.total_bugs > 0) {
                html += `<div class="ai-file-result">
                    <div class="ai-file-name">${file}</div>
                    <div class="ai-bug-badge ${getSeverityClass(bugs.severity)}">${bugs.total_bugs} bugs (${bugs.severity})</div>
                </div>`;
                
                if (bugs.recommendations && bugs.recommendations.length > 0) {
                    html += '<div class="ai-recommendations">';
                    html += '<strong>Fix Recommendations:</strong><ul>';
                    bugs.recommendations.forEach(rec => {
                        html += `<li>${rec}</li>`;
                    });
                    html += '</ul></div>';
                }
            }
        }
        
        html += `<div class="ai-summary">
            <strong>Total Bugs Found: ${totalBugs}</strong>
        </div>`;
        
        html += '</div>';
    }
    
    // Security Analysis
    if (mlResults.security_analysis && Object.keys(mlResults.security_analysis).length > 0) {
        html += '<div class="ai-section">';
        html += '<h4>🔒 Security Analysis</h4>';
        
        let totalIssues = 0;
        let securityScore = 100;
        
        for (const [file, security] of Object.entries(mlResults.security_analysis)) {
            totalIssues += security.total_issues || 0;
            securityScore = Math.min(securityScore, security.security_score || 100);
            
            if (security.total_issues > 0) {
                html += `<div class="ai-file-result">
                    <div class="ai-file-name">${file}</div>
                    <div class="ai-security-badge ${getSeverityClass(security.severity)}">${security.total_issues} issues (${security.severity})</div>
                    <div class="ai-security-score">Security Score: ${security.security_score || 0}/100</div>
                </div>`;
                
                if (security.recommendations && security.recommendations.length > 0) {
                    html += '<div class="ai-recommendations">';
                    html += '<strong>Security Recommendations:</strong><ul>';
                    security.recommendations.forEach(rec => {
                        html += `<li>${rec}</li>`;
                    });
                    html += '</ul></div>';
                }
            }
        }
        
        html += `<div class="ai-summary">
            <strong>Total Security Issues: ${totalIssues} | Overall Security Score: ${securityScore}/100</strong>
        </div>`;
        
        html += '</div>';
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function getScoreClass(score) {
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-good';
    if (score >= 40) return 'score-fair';
    return 'score-poor';
}

function getSeverityClass(severity) {
    switch(severity.toLowerCase()) {
        case 'high': return 'severity-high';
        case 'medium': return 'severity-medium';
        case 'low': return 'severity-low';
        default: return 'severity-none';
    }
}

function displayAnalysis(analysis) {
    // Overview
    document.getElementById('fileCount').textContent = analysis.file_count || 0;
    document.getElementById('folderCount').textContent = analysis.folder_count || 0;
    document.getElementById('linesOfCode').textContent = analysis.lines_of_code || 0;
    document.getElementById('languages').textContent = analysis.languages ? analysis.languages.join(', ') : '-';
    document.getElementById('totalClasses').textContent = analysis.total_classes || 0;
    document.getElementById('totalFunctions').textContent = analysis.total_functions || 0;

    // Structure
    const structureTree = document.getElementById('structureTree');
    structureTree.innerHTML = formatStructure(analysis.structure || {});

    // Dependencies
    const dependencyGraph = document.getElementById('dependencyGraph');
    dependencyGraph.innerHTML = formatDependencies(analysis.dependencies || {}, analysis.internal_dependencies || {}, analysis.external_dependencies || {});
}

function formatStructure(structure, indent = 0) {
    let result = '';
    const spaces = '  '.repeat(indent);

    for (const [key, value] of Object.entries(structure)) {
        if (value === null) {
            result += `${spaces}📄 ${key}\n`;
        } else if (typeof value === 'object') {
            result += `${spaces}📁 ${key}/\n`;
            result += formatStructure(value, indent + 1);
        }
    }
    
    return result;
}

function formatDependencies(dependencies, internalDeps, externalDeps) {
    let html = '';
    
    // Internal Dependencies
    if (internalDeps && Object.keys(internalDeps).length > 0) {
        html += '<div class="dependency-section">';
        html += '<h4>🔗 Internal Dependencies (Project Files)</h4>';
        html += Object.entries(internalDeps).map(([file, imports]) => `
            <div class="dependency-item internal">
                <strong>📄 ${file}</strong>
                <ul>
                    ${Array.from(imports).map(imp => `<li>→ ${imp}</li>`).join('')}
                </ul>
            </div>
        `).join('');
        html += '</div>';
    }
    
    // External Dependencies
    if (externalDeps && Object.keys(externalDeps).length > 0) {
        html += '<div class="dependency-section">';
        html += '<h4>📦 External Dependencies (Libraries)</h4>';
        html += Object.entries(externalDeps).map(([file, imports]) => `
            <div class="dependency-item external">
                <strong>📄 ${file}</strong>
                <ul>
                    ${Array.from(imports).map(imp => `<li>→ ${imp}</li>`).join('')}
                </ul>
            </div>
        `).join('');
        html += '</div>';
    }
    
    // All Dependencies (fallback)
    if (!html && dependencies && Object.keys(dependencies).length > 0) {
        html = '<div class="dependency-section">';
        html += '<h4>📋 All Dependencies</h4>';
        html += Object.entries(dependencies).map(([file, imports]) => `
            <div class="dependency-item">
                <strong>📄 ${file}</strong>
                <ul>
                    ${Array.from(imports).map(imp => `<li>→ ${imp}</li>`).join('')}
                </ul>
            </div>
        `).join('');
        html += '</div>';
    }
    
    if (!html) {
        return '<p>No dependencies found.</p>';
    }
    
    return html;
}

// Analysis Tabs
function setupAnalysisTabs() {
    document.querySelectorAll('.analysis-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.analysis-tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.analysis-tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`${btn.dataset.tab}Tab`).classList.add('active');
        });
    });
}
