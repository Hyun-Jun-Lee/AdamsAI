# AdamsAI Frontend Integration Plan

## 🎯 Project Overview

**Objective**: Integrate Stitch-generated Tailwind CSS frontend with FastAPI backend to create a fully functional video summarization web application.

**Technology Stack**:
- Frontend: HTML + Tailwind CSS (CDN) + Vanilla JavaScript
- Backend: FastAPI + SQLAlchemy
- Architecture: Static file serving with REST API

---

## 📁 Project Structure

```
AdamsAI/
├── app/                              # Backend (Existing)
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   ├── config.py                     # Configuration management
│   ├── database.py                   # Database connection & session
│   ├── models.py                     # SQLAlchemy ORM models
│   ├── schemas.py                    # Pydantic validation schemas
│   │
│   ├── routers/                      # API route handlers
│   │   ├── __init__.py
│   │   ├── videos.py                 # Video upload/download endpoints
│   │   ├── audios.py                 # Audio extraction endpoints
│   │   ├── transcripts.py            # Transcription endpoints
│   │   └── summaries.py              # Summarization endpoints
│   │
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── video_service.py
│   │   ├── audio_service.py
│   │   ├── stt_service.py
│   │   └── summary_service.py
│   │
│   ├── repositories/                 # Data access layer
│   │   ├── __init__.py
│   │   ├── video_repository.py
│   │   ├── audio_repository.py
│   │   ├── transcript_repository.py
│   │   ├── summary_repository.py
│   │   └── prompt_template_repository.py
│   │
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       ├── file_utils.py
│       ├── video_utils.py
│       ├── audio_utils.py
│       ├── validators.py
│       └── downloader.py
│
├── frontend/                         # Frontend (New)
│   ├── pages/                        # HTML pages
│   │   ├── index.html                # Dashboard
│   │   ├── videos.html               # Video management
│   │   ├── transcripts.html          # Transcript management
│   │   ├── summaries.html            # Summary results
│   │   ├── templates.html            # Prompt template management
│   │   └── workflow.html             # Unified workflow
│   │
│   ├── js/                           # JavaScript modules
│   │   ├── api.js                    # API client (fetch wrapper)
│   │   ├── components.js             # Reusable UI components
│   │   ├── utils.js                  # Helper functions
│   │   ├── dashboard.js              # Dashboard page logic
│   │   ├── videos.js                 # Video page logic
│   │   ├── transcripts.js            # Transcript page logic
│   │   ├── summaries.js              # Summary page logic
│   │   ├── templates.js              # Template page logic
│   │   └── workflow.js               # Workflow page logic
│   │
│   └── assets/                       # Static assets
│       ├── images/
│       └── icons/
│
├── storage/                          # File storage (Existing)
│   ├── videos/
│   └── audios/
│
├── tests/                            # Test suite (Existing)
│   ├── conftest.py
│   ├── test_repositories/
│   ├── test_services/
│   └── test_routers/
│
├── stitch_web_ui/                    # Source HTML from Stitch
│   ├── adamsai_dashboard/
│   ├── video_management_page/
│   ├── transcript_management_page/
│   ├── summary_results_page/
│   ├── prompt_template_management/
│   └── unified_workflow_page/
│
├── docs/                             # Documentation
│   ├── backend.md
│   └── frontend_integration_plan.md  # This file
│
├── .env.example                      # Environment variables template
├── requirements.txt                  # Python dependencies
├── pytest.ini                        # Test configuration
└── README.md                         # Project documentation
```

---

## 🔄 Development Phases

### Phase 1: Project Structure Setup
**Duration**: 5 minutes
**Status**: pending

#### Tasks:
1. Create `frontend/` directory structure
2. Create `frontend/pages/`, `frontend/js/`, `frontend/assets/` directories
3. Update `.gitignore` to exclude unnecessary frontend files

#### Deliverables:
- ✅ Directory structure created
- ✅ .gitignore updated

---

### Phase 2: Static File Serving Configuration
**Duration**: 10 minutes
**Status**: pending

#### Tasks:
1. Update `app/main.py` to serve static files
2. Add route handlers for HTML pages
3. Configure CORS if needed
4. Test static file serving

#### Implementation:

```python
# app/main.py additions

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount static directories
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# Serve HTML pages
@app.get("/", response_class=FileResponse)
async def serve_dashboard():
    return FileResponse("frontend/pages/index.html")

@app.get("/videos", response_class=FileResponse)
async def serve_videos():
    return FileResponse("frontend/pages/videos.html")

@app.get("/transcripts", response_class=FileResponse)
async def serve_transcripts():
    return FileResponse("frontend/pages/transcripts.html")

@app.get("/summaries", response_class=FileResponse)
async def serve_summaries():
    return FileResponse("frontend/pages/summaries.html")

@app.get("/templates", response_class=FileResponse)
async def serve_templates():
    return FileResponse("frontend/pages/templates.html")

@app.get("/workflow", response_class=FileResponse)
async def serve_workflow():
    return FileResponse("frontend/pages/workflow.html")
```

#### Deliverables:
- ✅ Static file serving configured
- ✅ Page routes added
- ✅ Server restart working

---

### Phase 3: HTML Files Migration
**Duration**: 10 minutes
**Status**: pending

#### Tasks:
1. Copy HTML files from `stitch_web_ui/` to `frontend/pages/`
2. Rename files appropriately
3. Update Tailwind CDN links if needed
4. Test each page loads correctly

#### File Mapping:
```
stitch_web_ui/adamsai_dashboard/code.html
  → frontend/pages/index.html

stitch_web_ui/video_management_page/code.html
  → frontend/pages/videos.html

stitch_web_ui/transcript_management_page/code.html
  → frontend/pages/transcripts.html

stitch_web_ui/summary_results_page/code.html
  → frontend/pages/summaries.html

stitch_web_ui/prompt_template_management/code.html
  → frontend/pages/templates.html

stitch_web_ui/unified_workflow_page/code.html
  → frontend/pages/workflow.html
```

#### Deliverables:
- ✅ All 6 HTML pages migrated
- ✅ Pages accessible via browser
- ✅ Tailwind styles rendering correctly

---

### Phase 4: Common Components Implementation
**Duration**: 30 minutes
**Status**: pending

#### 4.1 components.js - Reusable UI Components

```javascript
// frontend/js/components.js

/**
 * Sidebar Navigation Component
 * @param {string} activePage - Currently active page
 * @returns {string} HTML string for sidebar
 */
export function renderSidebar(activePage) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', path: '/' },
    { id: 'videos', label: 'Videos', icon: 'videocam', path: '/videos' },
    { id: 'audios', label: 'Audios', icon: 'audiotrack', path: '/audios' },
    { id: 'transcripts', label: 'Transcripts', icon: 'description', path: '/transcripts' },
    { id: 'summaries', label: 'Summaries', icon: 'summarize', path: '/summaries' },
    { id: 'templates', label: 'Templates', icon: 'folder_special', path: '/templates' },
    { id: 'workflow', label: 'Workflow', icon: 'account_tree', path: '/workflow' }
  ];

  return `
    <aside class="w-64 flex-shrink-0 bg-white dark:bg-slate-900 border-r border-slate-200">
      <div class="h-16 flex items-center px-6 border-b">
        <h1 class="text-xl font-bold text-primary">AdamsAI</h1>
      </div>
      <nav class="p-4">
        ${menuItems.map(item => `
          <a href="${item.path}"
             class="flex items-center gap-3 px-4 py-3 rounded-lg mb-2
                    ${activePage === item.id
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-slate-600 hover:bg-slate-50'}">
            <span class="material-symbols-outlined">${item.icon}</span>
            <span>${item.label}</span>
          </a>
        `).join('')}
      </nav>
    </aside>
  `;
}

/**
 * Loading Spinner Component
 */
export function showLoading(containerId = 'loading-container') {
  const container = document.getElementById(containerId);
  if (container) {
    container.innerHTML = `
      <div class="flex items-center justify-center p-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    `;
  }
}

export function hideLoading(containerId = 'loading-container') {
  const container = document.getElementById(containerId);
  if (container) {
    container.innerHTML = '';
  }
}

/**
 * Toast Notification Component
 * @param {string} message
 * @param {string} type - 'success', 'error', 'info', 'warning'
 */
export function showToast(message, type = 'info') {
  const colors = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
    warning: 'bg-yellow-500'
  };

  const toast = document.createElement('div');
  toast.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity`;
  toast.textContent = message;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/**
 * Status Badge Component
 * @param {string} status
 * @returns {string} HTML string for badge
 */
export function renderStatusBadge(status) {
  const config = {
    completed: { color: 'green', label: 'Completed' },
    processing: { color: 'yellow', label: 'Processing' },
    failed: { color: 'red', label: 'Failed' },
    uploaded: { color: 'gray', label: 'Uploaded' },
    extracted: { color: 'blue', label: 'Extracted' }
  };

  const { color, label } = config[status] || { color: 'gray', label: status };

  return `
    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${color}-100 text-${color}-800">
      ${label}
    </span>
  `;
}

/**
 * Confirmation Modal Component
 * @param {string} title
 * @param {string} message
 * @param {Function} onConfirm
 */
export function showConfirmModal(title, message, onConfirm) {
  const modal = document.createElement('div');
  modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
  modal.innerHTML = `
    <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
      <h3 class="text-lg font-semibold mb-2">${title}</h3>
      <p class="text-slate-600 mb-6">${message}</p>
      <div class="flex justify-end gap-3">
        <button id="cancel-btn" class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded">
          Cancel
        </button>
        <button id="confirm-btn" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
          Confirm
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  document.getElementById('cancel-btn').onclick = () => modal.remove();
  document.getElementById('confirm-btn').onclick = () => {
    onConfirm();
    modal.remove();
  };
}

/**
 * Empty State Component
 * @param {string} icon
 * @param {string} title
 * @param {string} message
 * @param {string} actionLabel
 * @param {Function} onAction
 */
export function renderEmptyState(icon, title, message, actionLabel, onAction) {
  return `
    <div class="flex flex-col items-center justify-center p-12 text-center">
      <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">${icon}</span>
      <h3 class="text-xl font-semibold text-slate-700 mb-2">${title}</h3>
      <p class="text-slate-500 mb-6">${message}</p>
      ${actionLabel ? `
        <button onclick="${onAction}" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          ${actionLabel}
        </button>
      ` : ''}
    </div>
  `;
}
```

#### 4.2 utils.js - Helper Functions

```javascript
// frontend/js/utils.js

/**
 * Format file size to human readable string
 * @param {number} bytes
 * @returns {string}
 */
export function formatFileSize(bytes) {
  if (!bytes) return 'N/A';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * Format duration in seconds to HH:MM:SS or MM:SS
 * @param {number} seconds
 * @returns {string}
 */
export function formatDuration(seconds) {
  if (!seconds) return 'N/A';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format ISO date string to readable format
 * @param {string} isoString
 * @returns {string}
 */
export function formatDate(isoString) {
  if (!isoString) return 'N/A';
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Debounce function for search inputs
 * @param {Function} func
 * @param {number} wait
 * @returns {Function}
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Validate video file type
 * @param {File} file
 * @returns {boolean}
 */
export function isValidVideoFile(file) {
  const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv'];
  return validTypes.includes(file.type) ||
         /\.(mp4|avi|mov|mkv)$/i.test(file.name);
}

/**
 * Validate URL format
 * @param {string} url
 * @returns {boolean}
 */
export function isValidURL(url) {
  try {
    new URL(url);
    return url.startsWith('http://') || url.startsWith('https://');
  } catch {
    return false;
  }
}

/**
 * Truncate text to specified length
 * @param {string} text
 * @param {number} maxLength
 * @returns {string}
 */
export function truncateText(text, maxLength = 100) {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Generate pagination data
 * @param {number} totalItems
 * @param {number} currentPage
 * @param {number} itemsPerPage
 * @returns {object}
 */
export function calculatePagination(totalItems, currentPage, itemsPerPage) {
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  return {
    totalPages,
    startItem,
    endItem,
    hasPrevious: currentPage > 1,
    hasNext: currentPage < totalPages
  };
}
```

#### Deliverables:
- ✅ components.js implemented
- ✅ utils.js implemented
- ✅ Helper functions tested

---

### Phase 5: API Client Implementation
**Duration**: 40 minutes
**Status**: pending

#### api.js - Complete REST API Client

```javascript
// frontend/js/api.js

const API_BASE_URL = window.location.origin;

/**
 * Generic API request handler with error handling
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('API Request failed:', error);
    throw error;
  }
}

export const API = {
  // ========================================================================
  // Videos API
  // ========================================================================

  videos: {
    /**
     * Upload video file
     * @param {File} file
     * @param {Function} onProgress - Progress callback (0-100)
     */
    async upload(file, onProgress) {
      const formData = new FormData();
      formData.append('file', file);

      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable && onProgress) {
            const percentComplete = (e.loaded / e.total) * 100;
            onProgress(percentComplete);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error('Upload failed'));
          }
        });

        xhr.addEventListener('error', () => reject(new Error('Upload failed')));

        xhr.open('POST', `${API_BASE_URL}/api/videos/upload`);
        xhr.send(formData);
      });
    },

    /**
     * Download video from URL
     */
    async download(url, title = null) {
      return apiRequest('/api/videos/download', {
        method: 'POST',
        body: JSON.stringify({ url, title })
      });
    },

    /**
     * List videos with pagination
     */
    async list(status = null, limit = 10, offset = 0) {
      const params = new URLSearchParams({ limit, offset });
      if (status) params.append('status', status);

      return apiRequest(`/api/videos?${params}`);
    },

    /**
     * Get video by ID
     */
    async get(videoId) {
      return apiRequest(`/api/videos/${videoId}`);
    },

    /**
     * Delete video
     */
    async delete(videoId) {
      return apiRequest(`/api/videos/${videoId}`, { method: 'DELETE' });
    }
  },

  // ========================================================================
  // Audios API
  // ========================================================================

  audios: {
    /**
     * Extract audio from video
     */
    async extract(videoId) {
      return apiRequest('/api/audios/extract', {
        method: 'POST',
        body: JSON.stringify({ video_id: videoId })
      });
    },

    /**
     * List audios
     */
    async list(videoId = null, limit = 10, offset = 0) {
      const params = new URLSearchParams({ limit, offset });
      if (videoId) params.append('video_id', videoId);

      return apiRequest(`/api/audios?${params}`);
    },

    /**
     * Get audio by ID
     */
    async get(audioId) {
      return apiRequest(`/api/audios/${audioId}`);
    },

    /**
     * Delete audio
     */
    async delete(audioId) {
      return apiRequest(`/api/audios/${audioId}`, { method: 'DELETE' });
    }
  },

  // ========================================================================
  // Transcripts API
  // ========================================================================

  transcripts: {
    /**
     * Create transcript from audio
     */
    async create(audioId, language = 'ko') {
      return apiRequest('/api/transcripts/create', {
        method: 'POST',
        body: JSON.stringify({ audio_id: audioId, language })
      });
    },

    /**
     * List transcripts
     */
    async list(audioId = null, limit = 10, offset = 0) {
      const params = new URLSearchParams({ limit, offset });
      if (audioId) params.append('audio_id', audioId);

      return apiRequest(`/api/transcripts?${params}`);
    },

    /**
     * Get transcript by ID
     */
    async get(transcriptId) {
      return apiRequest(`/api/transcripts/${transcriptId}`);
    },

    /**
     * Search transcripts by text
     */
    async search(query, limit = 10) {
      const params = new URLSearchParams({ q: query, limit });
      return apiRequest(`/api/transcripts/search?${params}`);
    }
  },

  // ========================================================================
  // Summaries API
  // ========================================================================

  summaries: {
    /**
     * Generate summary from transcript
     */
    async create(transcriptId, aiModelName = null, promptTemplateId = null, promptTemplateName = null) {
      const body = { transcript_id: transcriptId };
      if (aiModelName) body.ai_model_name = aiModelName;
      if (promptTemplateId) body.prompt_template_id = promptTemplateId;
      if (promptTemplateName) body.prompt_template_name = promptTemplateName;

      return apiRequest('/api/summaries/create', {
        method: 'POST',
        body: JSON.stringify(body)
      });
    },

    /**
     * List summaries
     */
    async list(transcriptId = null, limit = 10, offset = 0) {
      const params = new URLSearchParams({ limit, offset });
      if (transcriptId) params.append('transcript_id', transcriptId);

      return apiRequest(`/api/summaries?${params}`);
    },

    /**
     * Get summary by ID
     */
    async get(summaryId) {
      return apiRequest(`/api/summaries/${summaryId}`);
    },

    /**
     * Search summaries by AI model
     */
    async searchByModel(model, limit = 10) {
      const params = new URLSearchParams({ model, limit });
      return apiRequest(`/api/summaries/search/by-model?${params}`);
    }
  }
};
```

#### Deliverables:
- ✅ Complete API client implemented
- ✅ Error handling included
- ✅ Progress tracking for uploads
- ✅ All CRUD operations covered

---

### Phase 6: Page-Specific JavaScript

#### 6.1 dashboard.js - Dashboard Page
**Duration**: 25 minutes

```javascript
// frontend/js/dashboard.js

import { API } from './api.js';
import { showLoading, hideLoading, showToast, renderStatusBadge } from './components.js';
import { formatFileSize, formatDuration, formatDate } from './utils.js';

async function loadDashboardData() {
  try {
    showLoading('stats-container');
    showLoading('recent-videos-container');

    // Fetch data in parallel
    const [videosResponse, summariesResponse] = await Promise.all([
      API.videos.list(null, 100, 0),
      API.summaries.list(null, 100, 0)
    ]);

    // Update statistics
    updateStatistics(videosResponse, summariesResponse);

    // Render recent videos
    renderRecentVideos(videosResponse.items.slice(0, 10));

  } catch (error) {
    showToast('Failed to load dashboard data', 'error');
    console.error('Dashboard load error:', error);
  } finally {
    hideLoading('stats-container');
    hideLoading('recent-videos-container');
  }
}

function updateStatistics(videosData, summariesData) {
  const processingCount = videosData.items.filter(v => v.status === 'processing').length;

  document.getElementById('total-videos').textContent = videosData.total || 0;
  document.getElementById('processing-tasks').textContent = processingCount || 0;
  document.getElementById('completed-summaries').textContent = summariesData.total || 0;
}

function renderRecentVideos(videos) {
  const tbody = document.getElementById('recent-videos-tbody');

  if (!videos || videos.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-8 text-slate-500">
          No videos found
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = videos.map(video => `
    <tr class="hover:bg-slate-50">
      <td class="px-4 py-3">
        <div class="w-16 h-12 bg-slate-200 rounded flex items-center justify-center">
          <span class="material-symbols-outlined text-slate-400">videocam</span>
        </div>
      </td>
      <td class="px-4 py-3 font-medium">${video.filename}</td>
      <td class="px-4 py-3">${renderStatusBadge(video.status)}</td>
      <td class="px-4 py-3 text-slate-600">${formatFileSize(video.file_size)}</td>
      <td class="px-4 py-3 text-slate-600">${formatDuration(video.duration)}</td>
      <td class="px-4 py-3 text-slate-500 text-sm">${formatDate(video.created_at)}</td>
    </tr>
  `).join('');
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', loadDashboardData);

// Refresh every 30 seconds
setInterval(loadDashboardData, 30000);
```

#### 6.2 workflow.js - Unified Workflow
**Duration**: 40 minutes

```javascript
// frontend/js/workflow.js

import { API } from './api.js';
import { showToast } from './components.js';
import { isValidVideoFile, isValidURL } from './utils.js';

// Workflow state
let workflowState = {
  currentStep: 0,
  videoId: null,
  audioId: null,
  transcriptId: null,
  summaryId: null,
  isProcessing: false
};

// Initialize workflow page
document.addEventListener('DOMContentLoaded', () => {
  setupFileUpload();
  setupURLInput();
  setupProcessButton();
});

function setupFileUpload() {
  const dropArea = document.getElementById('drop-area');
  const fileInput = document.getElementById('file-input');
  const browseButton = document.getElementById('browse-button');

  // Browse button click
  browseButton?.addEventListener('click', () => fileInput?.click());

  // File input change
  fileInput?.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFileSelected(file);
  });

  // Drag and drop
  dropArea?.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropArea.classList.add('border-blue-500', 'bg-blue-50');
  });

  dropArea?.addEventListener('dragleave', () => {
    dropArea.classList.remove('border-blue-500', 'bg-blue-50');
  });

  dropArea?.addEventListener('drop', (e) => {
    e.preventDefault();
    dropArea.classList.remove('border-blue-500', 'bg-blue-50');

    const file = e.dataTransfer.files[0];
    if (file) handleFileSelected(file);
  });
}

function handleFileSelected(file) {
  if (!isValidVideoFile(file)) {
    showToast('Invalid video file format', 'error');
    return;
  }

  workflowState.selectedFile = file;
  document.getElementById('file-name-display').textContent = file.name;
  document.getElementById('start-button').disabled = false;
}

function setupURLInput() {
  const urlInput = document.getElementById('url-input');
  urlInput?.addEventListener('input', (e) => {
    const url = e.target.value.trim();
    if (url && isValidURL(url)) {
      workflowState.videoURL = url;
      document.getElementById('start-button').disabled = false;
    }
  });
}

function setupProcessButton() {
  const startButton = document.getElementById('start-button');
  startButton?.addEventListener('click', startWorkflow);

  const cancelButton = document.getElementById('cancel-button');
  cancelButton?.addEventListener('click', cancelWorkflow);
}

async function startWorkflow() {
  if (workflowState.isProcessing) return;

  workflowState.isProcessing = true;
  document.getElementById('start-button').disabled = true;

  const language = document.getElementById('language-select').value;
  const aiModel = document.getElementById('ai-model-select').value;
  const templateId = document.getElementById('template-select').value;

  try {
    // Step 1: Upload or Download Video
    await executeStep1();

    // Step 2: Extract Audio
    await executeStep2();

    // Step 3: Create Transcript
    await executeStep3(language);

    // Step 4: Generate Summary
    await executeStep4(aiModel, templateId);

    // Show results
    showResults();

  } catch (error) {
    showToast(`Workflow failed: ${error.message}`, 'error');
    updateStepStatus(workflowState.currentStep, 'failed');
  } finally {
    workflowState.isProcessing = false;
  }
}

async function executeStep1() {
  updateStepStatus(1, 'processing');
  workflowState.currentStep = 1;

  let video;
  if (workflowState.selectedFile) {
    video = await API.videos.upload(workflowState.selectedFile, (progress) => {
      updateProgress(1, progress);
    });
  } else if (workflowState.videoURL) {
    video = await API.videos.download(workflowState.videoURL);
  }

  workflowState.videoId = video.id;
  updateStepStatus(1, 'completed');
  showToast('Video uploaded successfully', 'success');
}

async function executeStep2() {
  updateStepStatus(2, 'processing');
  workflowState.currentStep = 2;

  const audio = await API.audios.extract(workflowState.videoId);
  workflowState.audioId = audio.id;

  updateStepStatus(2, 'completed');
  showToast('Audio extracted successfully', 'success');
}

async function executeStep3(language) {
  updateStepStatus(3, 'processing');
  workflowState.currentStep = 3;

  const transcript = await API.transcripts.create(workflowState.audioId, language);
  workflowState.transcriptId = transcript.id;

  updateStepStatus(3, 'completed');
  showToast('Transcript created successfully', 'success');
}

async function executeStep4(aiModel, templateId) {
  updateStepStatus(4, 'processing');
  workflowState.currentStep = 4;

  const summary = await API.summaries.create(
    workflowState.transcriptId,
    aiModel,
    templateId
  );
  workflowState.summaryId = summary.id;

  updateStepStatus(4, 'completed');
  showToast('Summary generated successfully', 'success');
}

function updateStepStatus(step, status) {
  const stepElement = document.getElementById(`step-${step}`);
  const statusIcon = stepElement?.querySelector('.status-icon');

  if (status === 'processing') {
    statusIcon.innerHTML = '<div class="animate-spin">⏳</div>';
    stepElement.classList.add('text-blue-600');
  } else if (status === 'completed') {
    statusIcon.innerHTML = '✓';
    stepElement.classList.add('text-green-600');
  } else if (status === 'failed') {
    statusIcon.innerHTML = '✗';
    stepElement.classList.add('text-red-600');
  }
}

function updateProgress(step, percent) {
  const progressBar = document.getElementById(`progress-${step}`);
  if (progressBar) {
    progressBar.style.width = `${percent}%`;
  }
}

function cancelWorkflow() {
  workflowState = {
    currentStep: 0,
    videoId: null,
    audioId: null,
    transcriptId: null,
    summaryId: null,
    isProcessing: false
  };

  // Reset UI
  for (let i = 1; i <= 4; i++) {
    updateStepStatus(i, 'pending');
  }

  document.getElementById('start-button').disabled = false;
}

function showResults() {
  // Show results section with tabs
  const resultsSection = document.getElementById('results-section');
  resultsSection.classList.remove('hidden');

  // Load summary data
  loadSummaryResults();
}

async function loadSummaryResults() {
  const summary = await API.summaries.get(workflowState.summaryId);
  const transcript = await API.transcripts.get(workflowState.transcriptId);

  document.getElementById('summary-text').textContent = summary.summary_text;
  document.getElementById('transcript-text').textContent = transcript.text;
}
```

#### 6.3-6.6 Other Pages
**Duration**: 20 minutes each

Implementation details for:
- `videos.js` - Video upload, list, delete
- `transcripts.js` - Transcript list, search, view
- `summaries.js` - Summary list, search, download
- `templates.js` - Template CRUD (if needed)

---

### Phase 7: Error Handling & UX Polish
**Duration**: 30 minutes
**Status**: pending

#### Tasks:
1. Add skeleton loading states
2. Implement error boundaries
3. Add retry logic for failed requests
4. Improve form validation
5. Add confirmation dialogs for destructive actions
6. Implement auto-refresh for processing items

#### Deliverables:
- ✅ Loading states implemented
- ✅ Error messages user-friendly
- ✅ Confirmation dialogs working
- ✅ Auto-refresh functional

---

### Phase 8: Testing & Bug Fixes
**Duration**: 1-2 hours
**Status**: pending

#### Test Checklist:

**Functional Testing**:
- [ ] Video upload works
- [ ] URL download works
- [ ] Audio extraction works
- [ ] Transcription works
- [ ] Summary generation works
- [ ] Search functionality works
- [ ] Pagination works
- [ ] Delete operations work

**UI/UX Testing**:
- [ ] All buttons clickable
- [ ] Loading states display
- [ ] Error messages show
- [ ] Success feedback shows
- [ ] Navigation works between pages
- [ ] Responsive on mobile
- [ ] Browser compatibility (Chrome, Firefox, Safari)

**Integration Testing**:
- [ ] Complete workflow end-to-end
- [ ] Data synchronization between pages
- [ ] Real-time status updates

#### Deliverables:
- ✅ All tests passing
- ✅ Bugs documented and fixed
- ✅ Ready for user testing

---

## 📊 Timeline Summary

| Phase | Tasks | Duration | Status |
|-------|-------|----------|--------|
| 1 | Project Structure | 5 min | pending |
| 2 | Static File Serving | 10 min | pending |
| 3 | HTML Migration | 10 min | pending |
| 4 | Common Components | 30 min | pending |
| 5 | API Client | 40 min | pending |
| 6 | Page JavaScript | 2-3 hours | pending |
| 7 | Error Handling & UX | 30 min | pending |
| 8 | Testing & Bugs | 1-2 hours | pending |
| **Total** | | **4.5-6.5 hours** | |

---

## 🎯 Priority Order

### High Priority (Must Have):
1. ✅ Unified Workflow - Core functionality
2. ✅ Video Upload - Essential for all workflows
3. ✅ Dashboard - Main landing page
4. ✅ API Client - Foundation for all pages

### Medium Priority (Should Have):
5. ✅ Videos Page - Management interface
6. ✅ Transcripts Page - View results
7. ✅ Summaries Page - View results

### Low Priority (Nice to Have):
8. ⭕ Templates Page - Admin functionality
9. ⭕ Advanced search features
10. ⭕ Bulk operations

---

## 🚀 Getting Started

### Prerequisites:
- FastAPI backend running (`uv run uvicorn app.main:app --reload`)
- Database initialized
- Environment variables configured
- Browser with JavaScript enabled

### Quick Start:
```bash
# Start backend server
cd /Users/hj/Documents/GitHub/AdamsAI
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Open browser
open http://localhost:8000
```

---

## 📝 Notes

- Using Tailwind CDN for rapid development
- No build process required initially
- Can migrate to npm-based Tailwind later for production
- All JavaScript uses ES6 modules
- API client handles CORS automatically
- File uploads use XMLHttpRequest for progress tracking

---

## 🔗 Related Documentation

- [Backend API Documentation](./backend.md)
- FastAPI Docs: http://localhost:8000/docs
- Tailwind CSS: https://tailwindcss.com/docs

---

**Last Updated**: 2024-01-XX
**Version**: 1.0
**Status**: In Progress
