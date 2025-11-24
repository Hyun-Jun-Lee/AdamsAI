/**
 * Audio Management Page
 * Handles audio listing, extraction, and management
 */

import { audioAPI, videoAPI } from './api.js';
import { showToast, showLoading, hideLoading, showConfirmModal } from './components.js';
import { formatFileSize, formatDuration, formatDate, debounce } from './utils.js';

// State management
const state = {
    audios: [],
    videos: [],
    filteredVideos: [],
    searchQuery: '',
    isExtracting: false,
};

// DOM Elements
let elements = {};

/**
 * Initialize the page
 */
function init() {
    // Get DOM elements
    elements = {
        // Main UI
        extractBtn: document.getElementById('extract-audio-btn'),
        audioList: document.getElementById('audio-list'),
        emptyState: document.getElementById('empty-state'),

        // Modal
        modal: document.getElementById('video-modal'),
        closeModalBtn: document.getElementById('close-modal-btn'),
        cancelModalBtn: document.getElementById('cancel-modal-btn'),
        videoSearch: document.getElementById('video-search'),
        videoList: document.getElementById('video-list'),
        videoLoading: document.getElementById('video-loading'),
    };

    // Setup event listeners
    setupEventListeners();

    // Load audios
    loadAudios();

    console.log('Audios page initialized');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Extract audio button
    elements.extractBtn?.addEventListener('click', showVideoSelectionModal);

    // Modal controls
    elements.closeModalBtn?.addEventListener('click', hideVideoSelectionModal);
    elements.cancelModalBtn?.addEventListener('click', hideVideoSelectionModal);

    // Click outside modal to close
    elements.modal?.addEventListener('click', (e) => {
        if (e.target === elements.modal) {
            hideVideoSelectionModal();
        }
    });

    // Video search
    elements.videoSearch?.addEventListener('input', debounce((e) => {
        state.searchQuery = e.target.value.toLowerCase();
        filterVideos();
    }, 300));
}

/**
 * Load audios from API
 */
async function loadAudios() {
    try {
        showLoading('Loading audio files...');
        const result = await audioAPI.getAll({ limit: 100 });
        state.audios = result;
        renderAudios();
    } catch (error) {
        console.error('Failed to load audios:', error);
        showToast('Failed to load audio files', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Render audios
 */
function renderAudios() {
    if (!elements.audioList || !elements.emptyState) return;

    if (state.audios.length === 0) {
        elements.audioList.classList.add('hidden');
        elements.emptyState.classList.remove('hidden');
        return;
    }

    elements.audioList.classList.remove('hidden');
    elements.emptyState.classList.add('hidden');

    elements.audioList.innerHTML = state.audios.map(audio => createAudioCard(audio)).join('');

    // Attach event listeners
    attachAudioEventListeners();
}

/**
 * Create audio card HTML
 */
function createAudioCard(audio) {
    const statusColors = {
        extracted: 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300',
        processing: 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300',
        completed: 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300',
        failed: 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300',
    };

    const statusColor = statusColors[audio.status] || statusColors.extracted;

    return `
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
            <div class="flex items-start justify-between gap-4">
                <div class="flex items-start gap-4 flex-1">
                    <div class="flex-shrink-0 w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                        <span class="material-symbols-outlined text-2xl text-primary">graphic_eq</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-1 truncate">${audio.filename}</h3>
                        <div class="flex flex-wrap items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
                            ${audio.file_size ? `<span class="flex items-center gap-1">
                                <span class="material-symbols-outlined text-base">storage</span>
                                ${formatFileSize(audio.file_size)}
                            </span>` : ''}
                            ${audio.duration ? `<span class="flex items-center gap-1">
                                <span class="material-symbols-outlined text-base">schedule</span>
                                ${formatDuration(audio.duration)}
                            </span>` : ''}
                            <span class="flex items-center gap-1">
                                <span class="material-symbols-outlined text-base">calendar_today</span>
                                ${formatDate(audio.created_at)}
                            </span>
                        </div>
                        ${audio.video_id ? `<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">From video ID: ${audio.video_id}</p>` : ''}
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor}">
                        ${audio.status}
                    </span>
                    <button class="play-audio-btn text-slate-400 hover:text-primary" data-id="${audio.id}" title="Play audio">
                        <span class="material-symbols-outlined">play_circle</span>
                    </button>
                    <button class="delete-audio-btn text-slate-400 hover:text-red-600" data-id="${audio.id}" title="Delete audio">
                        <span class="material-symbols-outlined">delete</span>
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Attach event listeners to audio cards
 */
function attachAudioEventListeners() {
    // Delete buttons
    document.querySelectorAll('.delete-audio-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const audioId = parseInt(btn.dataset.id);
            handleDeleteAudio(audioId);
        });
    });

    // Play buttons (placeholder)
    document.querySelectorAll('.play-audio-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            showToast('Audio playback feature coming soon!', 'info');
        });
    });
}

/**
 * Handle audio deletion
 */
function handleDeleteAudio(audioId) {
    showConfirmModal(
        'Are you sure you want to delete this audio file? This action cannot be undone.',
        async () => {
            try {
                showLoading('Deleting audio...');
                await audioAPI.delete(audioId);
                showToast('Audio deleted successfully', 'success');

                // Remove from state
                state.audios = state.audios.filter(a => a.id !== audioId);
                renderAudios();
            } catch (error) {
                console.error('Failed to delete audio:', error);
                showToast('Failed to delete audio', 'error');
            } finally {
                hideLoading();
            }
        }
    );
}

/**
 * Show video selection modal
 */
async function showVideoSelectionModal() {
    if (!elements.modal) return;

    // Show modal
    elements.modal.classList.remove('hidden');

    // Load videos
    await loadVideos();
}

/**
 * Hide video selection modal
 */
function hideVideoSelectionModal() {
    if (!elements.modal) return;
    elements.modal.classList.add('hidden');
    state.searchQuery = '';
    if (elements.videoSearch) elements.videoSearch.value = '';
}

/**
 * Load videos from API
 */
async function loadVideos() {
    if (!elements.videoList || !elements.videoLoading) return;

    try {
        elements.videoLoading.classList.remove('hidden');
        elements.videoList.innerHTML = '';

        const result = await videoAPI.getAll({ limit: 100 });
        state.videos = result;
        state.filteredVideos = result;

        filterVideos();
    } catch (error) {
        console.error('Failed to load videos:', error);
        showToast('Failed to load videos', 'error');
        elements.videoList.innerHTML = `
            <div class="text-center py-8 text-slate-500 dark:text-slate-400">
                Failed to load videos. Please try again.
            </div>
        `;
    } finally {
        elements.videoLoading.classList.add('hidden');
    }
}

/**
 * Filter videos based on search query
 */
function filterVideos() {
    if (!state.videos) return;

    state.filteredVideos = state.videos.filter(video =>
        video.filename.toLowerCase().includes(state.searchQuery)
    );

    renderVideos();
}

/**
 * Render videos in modal
 */
function renderVideos() {
    if (!elements.videoList) return;

    if (state.filteredVideos.length === 0) {
        elements.videoList.innerHTML = `
            <div class="text-center py-8 text-slate-500 dark:text-slate-400">
                No videos found
            </div>
        `;
        return;
    }

    elements.videoList.innerHTML = state.filteredVideos.map(video => `
        <button
            class="video-select-btn w-full text-left p-4 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-primary hover:bg-primary/5 transition-colors"
            data-id="${video.id}"
        >
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-2xl text-slate-400">videocam</span>
                <div class="flex-1 min-w-0">
                    <p class="font-medium text-slate-900 dark:text-white truncate">${video.filename}</p>
                    <div class="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
                        ${video.file_size ? `<span>${formatFileSize(video.file_size)}</span>` : ''}
                        ${video.duration ? `<span>${formatDuration(video.duration)}</span>` : ''}
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(video.status)}">
                            ${video.status}
                        </span>
                    </div>
                </div>
                <span class="material-symbols-outlined text-slate-400">chevron_right</span>
            </div>
        </button>
    `).join('');

    // Attach event listeners
    document.querySelectorAll('.video-select-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const videoId = parseInt(btn.dataset.id);
            handleVideoSelection(videoId);
        });
    });
}

/**
 * Get status color class
 */
function getStatusColor(status) {
    const colors = {
        uploaded: 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-300',
        processing: 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300',
        completed: 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300',
        failed: 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300',
    };
    return colors[status] || colors.uploaded;
}

/**
 * Handle video selection for audio extraction
 */
async function handleVideoSelection(videoId) {
    if (state.isExtracting) {
        showToast('Extraction already in progress', 'warning');
        return;
    }

    const video = state.videos.find(v => v.id === videoId);
    if (!video) return;

    // Close modal
    hideVideoSelectionModal();

    // Start extraction
    state.isExtracting = true;

    try {
        showLoading(`Extracting audio from "${video.filename}"...`);

        const audio = await audioAPI.extractFromVideo(videoId);

        showToast('Audio extracted successfully!', 'success');

        // Add to state and re-render
        state.audios.unshift(audio);
        renderAudios();
    } catch (error) {
        console.error('Failed to extract audio:', error);
        showToast(error.message || 'Failed to extract audio', 'error');
    } finally {
        state.isExtracting = false;
        hideLoading();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
