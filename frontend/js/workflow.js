/**
 * Unified Workflow Page
 * Handles the complete video processing pipeline: Upload → Audio → Transcript → Summary
 */

import { workflowAPI, templateAPI } from './api.js';
import { showToast, showLoading, hideLoading } from './components.js';
import { isValidVideoFile, isValidVideoUrl } from './utils.js';

// State management
const state = {
    currentStep: 'upload', // upload, audio, transcript, summary
    uploadType: 'file', // file or url
    selectedFile: null,
    videoUrl: '',
    settings: {
        language: 'auto',
        aiModel: 'anthropic/claude-3.5-sonnet',
        promptTemplateId: null,
    },
    processingData: {
        video: null,
        audio: null,
        transcript: null,
        summary: null,
    },
};

// DOM Elements
let elements = {};

/**
 * Initialize the page
 */
function init() {
    // Get DOM elements
    elements = {
        // Upload type toggle
        fileUploadRadio: document.querySelector('input[value="File Upload"]'),
        urlUploadRadio: document.querySelector('input[value="URL"]'),

        // Upload area
        uploadArea: document.querySelector('.border-dashed'),
        browseButton: document.querySelector('button:has(.truncate)'),
        fileInput: null, // Will create dynamically

        // Settings
        languageSelect: document.querySelector('select:has(option:contains("Auto-detect"))') || document.querySelectorAll('select')[0],
        aiModelSelect: document.querySelectorAll('select')[1],
        templateSelect: document.querySelectorAll('select')[2],
        templateViewButton: document.querySelector('button:has(.material-symbols-outlined:contains("visibility"))'),

        // Action buttons
        cancelButton: document.querySelector('button:has(.truncate:contains("Cancel"))'),
        startButton: document.querySelector('button:has(.truncate:contains("Start Processing"))'),

        // Progress indicators
        stepIndicators: document.querySelectorAll('.flex.flex-col.items-center.relative'),
        stepConnectors: document.querySelectorAll('.flex-auto.border-t-2'),
    };

    // Create hidden file input
    createFileInput();

    // Load templates
    loadTemplates();

    // Setup event listeners
    setupEventListeners();

    console.log('Workflow page initialized');
}

/**
 * Create hidden file input element
 */
function createFileInput() {
    elements.fileInput = document.createElement('input');
    elements.fileInput.type = 'file';
    elements.fileInput.accept = 'video/*';
    elements.fileInput.style.display = 'none';
    document.body.appendChild(elements.fileInput);

    elements.fileInput.addEventListener('change', handleFileSelect);
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Upload type toggle
    elements.fileUploadRadio?.addEventListener('change', () => {
        state.uploadType = 'file';
        updateUploadUI();
    });

    elements.urlUploadRadio?.addEventListener('change', () => {
        state.uploadType = 'url';
        updateUploadUI();
    });

    // File upload
    elements.browseButton?.addEventListener('click', () => {
        if (state.uploadType === 'file') {
            elements.fileInput.click();
        }
    });

    // Drag and drop
    elements.uploadArea?.addEventListener('dragover', handleDragOver);
    elements.uploadArea?.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea?.addEventListener('drop', handleDrop);
    elements.uploadArea?.addEventListener('click', (e) => {
        if (state.uploadType === 'file' && e.target !== elements.browseButton) {
            elements.fileInput.click();
        }
    });

    // Settings
    elements.languageSelect?.addEventListener('change', (e) => {
        const value = e.target.value.toLowerCase();
        state.settings.language = value === 'auto-detect' ? 'auto' : value;
    });

    elements.aiModelSelect?.addEventListener('change', (e) => {
        const modelMap = {
            'AdamsAI v3 (Recommended)': 'anthropic/claude-3.5-sonnet',
            'AdamsAI v2': 'anthropic/claude-3-sonnet-20240229',
            'General Purpose Model': 'openai/gpt-4-turbo',
        };
        state.settings.aiModel = modelMap[e.target.value] || 'anthropic/claude-3.5-sonnet';
    });

    elements.templateSelect?.addEventListener('change', async (e) => {
        const selectedIndex = e.target.selectedIndex;
        // First option is usually "Default Summary" which means no template
        state.settings.promptTemplateId = selectedIndex > 0 ? selectedIndex : null;
    });

    elements.templateViewButton?.addEventListener('click', showTemplatePreview);

    // Action buttons
    elements.cancelButton?.addEventListener('click', resetWorkflow);
    elements.startButton?.addEventListener('click', startProcessing);
}

/**
 * Update upload UI based on upload type
 */
function updateUploadUI() {
    const uploadContent = elements.uploadArea?.querySelector('.flex.flex-col.items-center.gap-6');
    if (!uploadContent) return;

    if (state.uploadType === 'url') {
        // Show URL input
        uploadContent.innerHTML = `
            <div class="flex size-14 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
                <span class="material-symbols-outlined text-3xl text-slate-500 dark:text-slate-400">link</span>
            </div>
            <div class="flex max-w-[480px] flex-col items-center gap-2">
                <p class="text-slate-800 dark:text-slate-100 text-lg font-bold leading-tight tracking-[-0.015em] max-w-[480px] text-center">Enter Video URL</p>
                <p class="text-slate-600 dark:text-slate-400 text-sm font-normal leading-normal max-w-[480px] text-center">Supports YouTube, Vimeo, and direct video URLs</p>
            </div>
            <input
                type="text"
                id="video-url-input"
                placeholder="https://www.youtube.com/watch?v=..."
                class="w-full max-w-md px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:border-primary focus:ring-primary"
            />
        `;

        const urlInput = document.getElementById('video-url-input');
        urlInput?.addEventListener('input', (e) => {
            state.videoUrl = e.target.value;
        });
    } else {
        // Show file upload UI
        uploadContent.innerHTML = `
            <div class="flex size-14 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
                <span class="material-symbols-outlined text-3xl text-slate-500 dark:text-slate-400">upload_file</span>
            </div>
            <div class="flex max-w-[480px] flex-col items-center gap-2">
                <p class="text-slate-800 dark:text-slate-100 text-lg font-bold leading-tight tracking-[-0.015em] max-w-[480px] text-center">Drag & Drop Your Video Here</p>
                <p class="text-slate-600 dark:text-slate-400 text-sm font-normal leading-normal max-w-[480px] text-center">or browse files on your computer</p>
            </div>
            <button class="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 text-sm font-bold leading-normal tracking-[0.015em] hover:bg-slate-300 dark:hover:bg-slate-600">
                <span class="truncate">Browse Files</span>
            </button>
        `;

        const browseBtn = uploadContent.querySelector('button');
        browseBtn?.addEventListener('click', () => elements.fileInput.click());
    }
}

/**
 * Load available templates
 */
async function loadTemplates() {
    try {
        const templates = await templateAPI.getAll({ is_active: true });

        if (elements.templateSelect && templates.length > 0) {
            // Keep first option as default, add templates
            const currentOptions = elements.templateSelect.innerHTML;
            const templateOptions = templates.map(t =>
                `<option value="${t.id}">${t.name}</option>`
            ).join('');

            // Preserve first option, add templates
            const firstOption = elements.templateSelect.querySelector('option');
            elements.templateSelect.innerHTML = firstOption.outerHTML + templateOptions;
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
        // Continue without templates
    }
}

/**
 * Handle file selection
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!isValidVideoFile(file)) {
        showToast('Please select a valid video file', 'error');
        return;
    }

    state.selectedFile = file;
    showSelectedFile(file);
}

/**
 * Handle drag over
 */
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    elements.uploadArea?.classList.add('border-primary', 'bg-blue-50', 'dark:bg-slate-800');
}

/**
 * Handle drag leave
 */
function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    elements.uploadArea?.classList.remove('border-primary', 'bg-blue-50', 'dark:bg-slate-800');
}

/**
 * Handle file drop
 */
function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    elements.uploadArea?.classList.remove('border-primary', 'bg-blue-50', 'dark:bg-slate-800');

    if (state.uploadType !== 'file') return;

    const files = event.dataTransfer.files;
    if (files.length === 0) return;

    const file = files[0];
    if (!isValidVideoFile(file)) {
        showToast('Please drop a valid video file', 'error');
        return;
    }

    state.selectedFile = file;
    showSelectedFile(file);
}

/**
 * Show selected file info
 */
function showSelectedFile(file) {
    const uploadContent = elements.uploadArea?.querySelector('.flex.flex-col.items-center.gap-6');
    if (!uploadContent) return;

    const fileSize = (file.size / (1024 * 1024)).toFixed(2);

    uploadContent.innerHTML = `
        <div class="flex size-14 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
            <span class="material-symbols-outlined text-3xl text-green-600 dark:text-green-400">check_circle</span>
        </div>
        <div class="flex max-w-[480px] flex-col items-center gap-2">
            <p class="text-slate-800 dark:text-slate-100 text-lg font-bold leading-tight tracking-[-0.015em] max-w-[480px] text-center">${file.name}</p>
            <p class="text-slate-600 dark:text-slate-400 text-sm font-normal leading-normal max-w-[480px] text-center">${fileSize} MB</p>
        </div>
        <button class="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 text-sm font-bold leading-normal tracking-[0.015em] hover:bg-slate-300 dark:hover:bg-slate-600">
            <span class="truncate">Change File</span>
        </button>
    `;

    const changeBtn = uploadContent.querySelector('button');
    changeBtn?.addEventListener('click', () => elements.fileInput.click());
}

/**
 * Show template preview
 */
async function showTemplatePreview() {
    const selectedIndex = elements.templateSelect?.selectedIndex;
    if (!selectedIndex || selectedIndex === 0) {
        showToast('Please select a template first', 'info');
        return;
    }

    try {
        const templateId = elements.templateSelect?.options[selectedIndex].value;
        const template = await templateAPI.getById(templateId);

        // Create modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white dark:bg-slate-900 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-auto p-6">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-xl font-bold text-slate-800 dark:text-slate-100">${template.name}</h3>
                        ${template.description ? `<p class="text-sm text-slate-500 dark:text-slate-400 mt-1">${template.description}</p>` : ''}
                    </div>
                    <button class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 font-mono text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">${template.content}</div>
            </div>
        `;

        modal.querySelector('button')?.addEventListener('click', () => modal.remove());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });

        document.body.appendChild(modal);
    } catch (error) {
        showToast('Failed to load template', 'error');
    }
}

/**
 * Start processing workflow
 */
async function startProcessing() {
    // Validate input
    if (state.uploadType === 'file' && !state.selectedFile) {
        showToast('Please select a video file', 'error');
        return;
    }

    if (state.uploadType === 'url' && !state.videoUrl) {
        showToast('Please enter a video URL', 'error');
        return;
    }

    if (state.uploadType === 'url' && !isValidVideoUrl(state.videoUrl)) {
        showToast('Please enter a valid video URL', 'error');
        return;
    }

    // Disable start button
    if (elements.startButton) {
        elements.startButton.disabled = true;
        elements.startButton.innerHTML = '<span class="truncate">Processing...</span>';
    }

    try {
        const options = {
            language: state.settings.language,
            aiModel: state.settings.aiModel,
            promptTemplateId: state.settings.promptTemplateId,
            onProgress: handleProgress,
        };

        let result;
        if (state.uploadType === 'file') {
            result = await workflowAPI.processVideo(state.selectedFile, options);
        } else {
            result = await workflowAPI.processFromUrl(state.videoUrl, options);
        }

        state.processingData = result;
        showToast('Processing completed successfully!', 'success');

        // Show results
        showResults(result);

    } catch (error) {
        console.error('Processing error:', error);
        showToast(error.message || 'Processing failed', 'error');
        resetStepIndicators();
    } finally {
        // Re-enable start button
        if (elements.startButton) {
            elements.startButton.disabled = false;
            elements.startButton.innerHTML = '<span class="truncate">Start Processing</span>';
        }
    }
}

/**
 * Handle progress updates
 */
function handleProgress(progress) {
    const { step, progress: percent, data, error } = progress;

    if (error) {
        console.error('Progress error:', error);
        return;
    }

    // Update step indicators
    updateStepIndicator(step, percent);

    // Show step completion
    if (percent === 100 && data) {
        console.log(`${step} completed:`, data);
    }
}

/**
 * Update step indicator
 */
function updateStepIndicator(step, percent) {
    const stepMap = {
        upload: 0,
        download: 0,
        audio: 1,
        transcript: 2,
        summary: 3,
    };

    const stepIndex = stepMap[step];
    if (stepIndex === undefined) return;

    // Update current and previous steps
    for (let i = 0; i <= stepIndex; i++) {
        const indicator = elements.stepIndicators[i];
        const connector = elements.stepConnectors[i];

        if (!indicator) continue;

        const circle = indicator.querySelector('.flex.size-8');
        const icon = indicator.querySelector('.material-symbols-outlined');
        const label = indicator.querySelector('p');

        if (i < stepIndex) {
            // Completed step
            circle?.classList.remove('bg-slate-200', 'dark:bg-slate-700', 'bg-primary');
            circle?.classList.add('bg-green-500');
            icon?.classList.remove('text-slate-500', 'dark:text-slate-400');
            icon?.classList.add('text-white');
            icon.style.fontVariationSettings = "'FILL' 1";
            label?.classList.remove('text-slate-500', 'dark:text-slate-400');
            label?.classList.add('text-green-500');

            connector?.classList.remove('border-slate-200', 'dark:border-slate-700');
            connector?.classList.add('border-green-500');
        } else if (i === stepIndex) {
            // Current step
            circle?.classList.remove('bg-slate-200', 'dark:bg-slate-700', 'bg-green-500');
            circle?.classList.add('bg-primary');
            icon?.classList.remove('text-slate-500', 'dark:text-slate-400');
            icon?.classList.add('text-white');
            icon.style.fontVariationSettings = "'FILL' 1";
            label?.classList.remove('text-slate-500', 'dark:text-slate-400');
            label?.classList.add('text-primary');
        }
    }
}

/**
 * Reset step indicators
 */
function resetStepIndicators() {
    elements.stepIndicators.forEach((indicator, i) => {
        const circle = indicator.querySelector('.flex.size-8');
        const icon = indicator.querySelector('.material-symbols-outlined');
        const label = indicator.querySelector('p');
        const connector = elements.stepConnectors[i];

        if (i === 0) {
            circle?.classList.remove('bg-slate-200', 'dark:bg-slate-700', 'bg-green-500');
            circle?.classList.add('bg-primary');
            icon?.classList.remove('text-slate-500', 'dark:text-slate-400');
            icon?.classList.add('text-white');
            icon.style.fontVariationSettings = "'FILL' 1";
            label?.classList.remove('text-slate-500', 'dark:text-slate-400', 'text-green-500');
            label?.classList.add('text-primary');
        } else {
            circle?.classList.remove('bg-primary', 'bg-green-500');
            circle?.classList.add('bg-slate-200', 'dark:bg-slate-700');
            icon?.classList.remove('text-white');
            icon?.classList.add('text-slate-500', 'dark:text-slate-400');
            icon.style.fontVariationSettings = "'FILL' 0";
            label?.classList.remove('text-primary', 'text-green-500');
            label?.classList.add('text-slate-500', 'dark:text-slate-400');
        }

        connector?.classList.remove('border-green-500', 'border-primary');
        connector?.classList.add('border-slate-200', 'dark:border-slate-700');
    });
}

/**
 * Show processing results
 */
function showResults(result) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white dark:bg-slate-900 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-auto p-6">
            <div class="flex justify-between items-start mb-6">
                <h3 class="text-2xl font-bold text-slate-800 dark:text-slate-100">Processing Complete</h3>
                <button class="close-btn text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="space-y-6">
                <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                    <p class="text-green-800 dark:text-green-200 font-medium">✓ All steps completed successfully!</p>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
                    <h4 class="font-semibold text-slate-800 dark:text-slate-100 mb-3">Summary</h4>
                    <div class="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">${result.summary.content}</div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
                        <h5 class="font-medium text-slate-600 dark:text-slate-400 text-sm mb-2">Video</h5>
                        <p class="text-slate-800 dark:text-slate-100">${result.video.filename}</p>
                    </div>
                    <div class="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
                        <h5 class="font-medium text-slate-600 dark:text-slate-400 text-sm mb-2">AI Model</h5>
                        <p class="text-slate-800 dark:text-slate-100">${result.summary.ai_model}</p>
                    </div>
                </div>

                <div class="flex justify-end gap-3">
                    <button class="view-transcript-btn px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600">
                        View Transcript
                    </button>
                    <button class="new-video-btn px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-600">
                        Process Another Video
                    </button>
                </div>
            </div>
        </div>
    `;

    // Event listeners
    modal.querySelector('.close-btn')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.new-video-btn')?.addEventListener('click', () => {
        modal.remove();
        resetWorkflow();
    });
    modal.querySelector('.view-transcript-btn')?.addEventListener('click', () => {
        window.location.href = `/transcripts-page?id=${result.transcript.id}`;
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    document.body.appendChild(modal);
}

/**
 * Reset workflow to initial state
 */
function resetWorkflow() {
    state.selectedFile = null;
    state.videoUrl = '';
    state.processingData = {
        video: null,
        audio: null,
        transcript: null,
        summary: null,
    };

    resetStepIndicators();
    updateUploadUI();

    showToast('Workflow reset', 'info');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
