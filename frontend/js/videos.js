/**
 * Video Management Page
 * Handles video listing, upload, filtering, and management
 */

import { videoAPI } from './api.js';
import { showToast, showLoading, hideLoading, showConfirmModal } from './components.js';
import { formatFileSize, formatDuration, formatDate, isValidVideoFile, isValidVideoUrl, debounce } from './utils.js';

// State management
const state = {
    videos: [],
    filteredVideos: [],
    currentFilter: 'all',
    searchQuery: '',
    currentPage: 1,
    itemsPerPage: 10,
    uploadType: 'file', // 'file' or 'url'
    uploadProgress: 0,
    isUploading: false,
};

// DOM Elements
let elements = {};

/**
 * Initialize the page
 */
function init() {
    // Get DOM elements
    elements = {
        // Filters and search
        statusFilter: document.querySelector('select'),
        searchInput: document.querySelector('input[placeholder="Search videos..."]'),

        // Table
        tableBody: document.querySelector('tbody'),
        selectAllCheckbox: document.querySelector('thead input[type="checkbox"]'),

        // Pagination
        paginationInfo: document.querySelector('.text-sm.text-gray-700'),
        prevButton: Array.from(document.querySelectorAll('nav button')).find(btn =>
            btn.textContent.includes('Previous')
        ) || document.querySelectorAll('nav button')[0],
        nextButton: Array.from(document.querySelectorAll('nav button')).find(btn =>
            btn.textContent.includes('Next')
        ) || document.querySelectorAll('nav button')[1],

        // Upload tabs
        fileUploadTab: document.getElementById('file-upload-tab'),
        urlUploadTab: document.getElementById('url-upload-tab'),

        // Upload container
        uploadContainer: document.getElementById('upload-container'),

        // Upload area (file)
        uploadArea: document.querySelector('.border-dashed'),
        chooseFileButton: Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Choose File')
        ),
        progressBar: document.querySelector('.bg-primary'),
        progressContainer: document.querySelector('.w-full.bg-gray-200'),
        fileInput: null, // Will create dynamically
    };

    // Create hidden file input
    createFileInput();

    // Setup event listeners
    setupEventListeners();

    // Load videos
    loadVideos();

    console.log('Video management page initialized');
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
    // Filters
    elements.statusFilter?.addEventListener('change', (e) => {
        state.currentFilter = e.target.value.toLowerCase();
        filterVideos();
    });

    // Search
    elements.searchInput?.addEventListener('input', debounce((e) => {
        state.searchQuery = e.target.value.toLowerCase();
        filterVideos();
    }, 300));

    // Select all checkbox
    elements.selectAllCheckbox?.addEventListener('change', handleSelectAll);

    // Pagination
    elements.prevButton?.addEventListener('click', () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            renderVideos();
        }
    });

    elements.nextButton?.addEventListener('click', () => {
        const totalPages = Math.ceil(state.filteredVideos.length / state.itemsPerPage);
        if (state.currentPage < totalPages) {
            state.currentPage++;
            renderVideos();
        }
    });

    // Upload tabs
    elements.fileUploadTab?.addEventListener('click', (e) => {
        e.preventDefault();
        switchToFileUpload();
    });

    elements.urlUploadTab?.addEventListener('click', (e) => {
        e.preventDefault();
        switchToUrlUpload();
    });

    // File upload
    elements.chooseFileButton?.addEventListener('click', () => {
        elements.fileInput.click();
    });

    // Drag and drop
    elements.uploadArea?.addEventListener('dragover', handleDragOver);
    elements.uploadArea?.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea?.addEventListener('drop', handleDrop);
    elements.uploadArea?.addEventListener('click', (e) => {
        if (state.uploadType === 'file' && e.target !== elements.chooseFileButton) {
            elements.fileInput.click();
        }
    });
}

/**
 * Load videos from API
 */
async function loadVideos() {
    try {
        showLoading('Loading videos...');
        const videos = await videoAPI.getAll();
        state.videos = videos;
        state.filteredVideos = videos;
        renderVideos();
    } catch (error) {
        console.error('Failed to load videos:', error);
        showToast('Failed to load videos', 'error');
        renderEmptyState();
    } finally {
        hideLoading();
    }
}

/**
 * Filter videos based on status and search query
 */
function filterVideos() {
    let filtered = state.videos;

    // Filter by status
    if (state.currentFilter && state.currentFilter !== 'all') {
        filtered = filtered.filter(v => v.status.toLowerCase() === state.currentFilter);
    }

    // Filter by search query
    if (state.searchQuery) {
        filtered = filtered.filter(v =>
            v.filename.toLowerCase().includes(state.searchQuery) ||
            (v.source && v.source.toLowerCase().includes(state.searchQuery))
        );
    }

    state.filteredVideos = filtered;
    state.currentPage = 1; // Reset to first page
    renderVideos();
}

/**
 * Render videos table
 */
function renderVideos() {
    if (!elements.tableBody) return;

    if (state.filteredVideos.length === 0) {
        renderEmptyState();
        return;
    }

    // Calculate pagination
    const startIndex = (state.currentPage - 1) * state.itemsPerPage;
    const endIndex = Math.min(startIndex + state.itemsPerPage, state.filteredVideos.length);
    const videosToShow = state.filteredVideos.slice(startIndex, endIndex);

    // Render table rows
    elements.tableBody.innerHTML = videosToShow.map(video => createVideoRow(video)).join('');

    // Update pagination info
    updatePaginationInfo();

    // Add event listeners to action buttons
    attachRowEventListeners();
}

/**
 * Create video table row HTML
 */
function createVideoRow(video) {
    const statusColors = {
        uploaded: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300',
        processing: 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300',
        completed: 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300',
        failed: 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300',
    };

    const sourceIcon = video.source === 'url' ? 'link' : 'upload_file';
    const statusClass = statusColors[video.status] || statusColors.uploaded;
    const statusText = video.status.charAt(0).toUpperCase() + video.status.slice(1);

    return `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50" data-id="${video.id}">
            <td class="p-4">
                <input class="rounded border-gray-300 text-primary focus:ring-primary row-checkbox" type="checkbox" value="${video.id}"/>
            </td>
            <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                <div class="h-10 w-16 rounded-md bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                    <span class="material-symbols-outlined text-gray-400">play_circle</span>
                </div>
            </td>
            <td class="whitespace-nowrap px-3 py-4 text-sm font-medium text-gray-900 dark:text-gray-200">${video.filename}</td>
            <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                <span class="material-symbols-outlined text-xl">${sourceIcon}</span>
            </td>
            <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">${formatFileSize(video.file_size)}</td>
            <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">${formatDuration(video.duration)}</td>
            <td class="whitespace-nowrap px-3 py-4 text-sm">
                <span class="inline-flex items-center rounded-full ${statusClass} px-2.5 py-0.5 text-xs font-medium">${statusText}</span>
            </td>
            <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">${formatDate(video.created_at)}</td>
            <td class="whitespace-nowrap px-3 py-4 text-right text-sm font-medium">
                <button class="text-gray-500 hover:text-primary delete-btn" data-id="${video.id}">
                    <span class="material-symbols-outlined">delete</span>
                </button>
            </td>
        </tr>
    `;
}

/**
 * Render empty state
 */
function renderEmptyState() {
    if (!elements.tableBody) return;

    elements.tableBody.innerHTML = `
        <tr>
            <td colspan="9" class="px-6 py-12 text-center">
                <div class="flex flex-col items-center gap-4">
                    <span class="material-symbols-outlined text-6xl text-gray-300 dark:text-gray-600">video_library</span>
                    <p class="text-gray-500 dark:text-gray-400 text-lg font-medium">No videos found</p>
                    <p class="text-gray-400 dark:text-gray-500 text-sm">Upload a video to get started</p>
                </div>
            </td>
        </tr>
    `;

    if (elements.paginationInfo) {
        elements.paginationInfo.innerHTML = 'Showing <span class="font-medium">0</span> to <span class="font-medium">0</span> of <span class="font-medium">0</span> results';
    }
}

/**
 * Update pagination info
 */
function updatePaginationInfo() {
    if (!elements.paginationInfo) return;

    const startIndex = (state.currentPage - 1) * state.itemsPerPage + 1;
    const endIndex = Math.min(startIndex + state.itemsPerPage - 1, state.filteredVideos.length);

    elements.paginationInfo.innerHTML = `
        Showing <span class="font-medium">${startIndex}</span> to <span class="font-medium">${endIndex}</span> of <span class="font-medium">${state.filteredVideos.length}</span> results
    `;

    // Enable/disable pagination buttons
    if (elements.prevButton) {
        elements.prevButton.disabled = state.currentPage === 1;
        elements.prevButton.classList.toggle('opacity-50', state.currentPage === 1);
        elements.prevButton.classList.toggle('cursor-not-allowed', state.currentPage === 1);
    }

    const totalPages = Math.ceil(state.filteredVideos.length / state.itemsPerPage);
    if (elements.nextButton) {
        elements.nextButton.disabled = state.currentPage >= totalPages;
        elements.nextButton.classList.toggle('opacity-50', state.currentPage >= totalPages);
        elements.nextButton.classList.toggle('cursor-not-allowed', state.currentPage >= totalPages);
    }
}

/**
 * Attach event listeners to row elements
 */
function attachRowEventListeners() {
    // Delete buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const videoId = parseInt(btn.dataset.id);
            handleDelete(videoId);
        });
    });

    // Row checkboxes
    document.querySelectorAll('.row-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectAllState);
    });
}

/**
 * Handle select all checkbox
 */
function handleSelectAll(e) {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = e.target.checked;
    });
}

/**
 * Update select all checkbox state
 */
function updateSelectAllState() {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    const checkedCount = document.querySelectorAll('.row-checkbox:checked').length;

    if (elements.selectAllCheckbox) {
        elements.selectAllCheckbox.checked = checkedCount === checkboxes.length && checkboxes.length > 0;
        elements.selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
    }
}

/**
 * Handle video deletion
 */
function handleDelete(videoId) {
    const video = state.videos.find(v => v.id === videoId);
    if (!video) return;

    showConfirmModal(
        `Are you sure you want to delete "${video.filename}"? This action cannot be undone.`,
        async () => {
            try {
                showLoading('Deleting video...');
                await videoAPI.delete(videoId);
                showToast('Video deleted successfully', 'success');

                // Remove from state
                state.videos = state.videos.filter(v => v.id !== videoId);
                filterVideos();
            } catch (error) {
                console.error('Failed to delete video:', error);
                showToast('Failed to delete video', 'error');
            } finally {
                hideLoading();
            }
        }
    );
}

/**
 * Switch to file upload mode
 */
function switchToFileUpload() {
    state.uploadType = 'file';

    // Update tab styling
    elements.fileUploadTab?.classList.add('border-b-primary', 'text-primary');
    elements.fileUploadTab?.classList.remove('border-b-transparent', 'text-gray-500', 'dark:text-gray-400');
    elements.urlUploadTab?.classList.remove('border-b-primary', 'text-primary');
    elements.urlUploadTab?.classList.add('border-b-transparent', 'text-gray-500', 'dark:text-gray-400');

    // Restore file upload UI
    if (!elements.uploadContainer) return;

    elements.uploadContainer.innerHTML = `
        <div class="flex flex-col items-center gap-6 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 px-6 py-10">
            <span class="material-symbols-outlined text-5xl text-gray-400 dark:text-gray-500">cloud_upload</span>
            <div class="flex flex-col items-center gap-2">
                <p class="text-gray-900 dark:text-white text-lg font-bold leading-tight tracking-[-0.015em] max-w-[480px] text-center">Drag & drop files here</p>
                <p class="text-gray-600 dark:text-gray-400 text-sm font-normal leading-normal max-w-[480px] text-center">or click to browse</p>
            </div>
            <button class="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em]">
                <span class="truncate">Choose File</span>
            </button>
            <div class="w-full mt-2" style="display: none;">
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div class="bg-primary h-2.5 rounded-full" style="width: 0%"></div>
                </div>
            </div>
            <p class="text-gray-500 dark:text-gray-400 text-xs font-normal leading-normal text-center">Supported formats: MP4, AVI, MOV, MKV</p>
        </div>
    `;

    // Re-attach event listeners for file upload
    elements.uploadArea = document.querySelector('.border-dashed');
    elements.chooseFileButton = Array.from(document.querySelectorAll('button')).find(btn =>
        btn.textContent.includes('Choose File')
    );
    elements.progressBar = document.querySelector('.bg-primary');
    elements.progressContainer = document.querySelector('.w-full.bg-gray-200');

    elements.chooseFileButton?.addEventListener('click', () => {
        elements.fileInput.click();
    });

    elements.uploadArea?.addEventListener('dragover', handleDragOver);
    elements.uploadArea?.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea?.addEventListener('drop', handleDrop);
    elements.uploadArea?.addEventListener('click', (e) => {
        if (state.uploadType === 'file' && e.target !== elements.chooseFileButton) {
            elements.fileInput.click();
        }
    });
}

/**
 * Switch to URL upload mode
 */
function switchToUrlUpload() {
    state.uploadType = 'url';

    // Update tab styling
    elements.urlUploadTab?.classList.add('border-b-primary', 'text-primary');
    elements.urlUploadTab?.classList.remove('border-b-transparent', 'text-gray-500', 'dark:text-gray-400');
    elements.fileUploadTab?.classList.remove('border-b-primary', 'text-primary');
    elements.fileUploadTab?.classList.add('border-b-transparent', 'text-gray-500', 'dark:text-gray-400');

    // Replace upload area with URL input
    if (!elements.uploadContainer) return;

    elements.uploadContainer.innerHTML = `
        <div class="flex flex-col gap-4">
            <div>
                <label for="video-url" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Video URL</label>
                <input
                    type="url"
                    id="video-url"
                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-background-dark shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2"
                    placeholder="https://example.com/video.mp4 or YouTube URL"
                />
            </div>
            <button id="download-url-btn" class="flex w-full cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-primary/90">
                <span class="truncate">Download</span>
            </button>
            <p class="text-gray-500 dark:text-gray-400 text-xs font-normal leading-normal text-center">Supports YouTube, Vimeo, and direct video URLs</p>
        </div>
    `;

    // Add event listener for download button
    document.getElementById('download-url-btn')?.addEventListener('click', handleUrlDownload);
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

    uploadFile(file);
}

/**
 * Handle drag over
 */
function handleDragOver(event) {
    if (state.uploadType !== 'file') return;

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

    uploadFile(file);
}

/**
 * Upload file
 */
async function uploadFile(file) {
    if (state.isUploading) {
        showToast('Upload already in progress', 'warning');
        return;
    }

    state.isUploading = true;
    state.uploadProgress = 0;

    try {
        const video = await videoAPI.upload(file, (progress) => {
            state.uploadProgress = progress;
            updateProgressBar(progress);
        });

        showToast('Video uploaded successfully', 'success');

        // Add to state and re-render
        state.videos.unshift(video);
        filterVideos();

        // Reset progress
        state.uploadProgress = 0;
        updateProgressBar(0);

    } catch (error) {
        console.error('Upload failed:', error);
        showToast(error.message || 'Upload failed', 'error');
    } finally {
        state.isUploading = false;
    }
}

/**
 * Handle URL download
 */
async function handleUrlDownload() {
    const urlInput = document.getElementById('video-url');
    const url = urlInput?.value.trim();

    if (!url) {
        showToast('Please enter a video URL', 'error');
        return;
    }

    if (!isValidVideoUrl(url)) {
        showToast('Please enter a valid video URL', 'error');
        return;
    }

    try {
        showLoading('Downloading video...');
        const video = await videoAPI.downloadFromUrl(url);
        showToast('Video download started', 'success');

        // Add to state and re-render
        state.videos.unshift(video);
        filterVideos();

        // Clear input
        if (urlInput) urlInput.value = '';

    } catch (error) {
        console.error('Download failed:', error);
        showToast(error.message || 'Download failed', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Update progress bar
 */
function updateProgressBar(percent) {
    if (elements.progressBar) {
        elements.progressBar.style.width = `${percent}%`;
    }

    // Show/hide progress container
    if (elements.progressContainer) {
        elements.progressContainer.style.display = percent > 0 && percent < 100 ? 'block' : 'none';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
