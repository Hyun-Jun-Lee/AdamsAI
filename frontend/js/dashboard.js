/**
 * Dashboard Page
 * Displays overview statistics and recent activity
 */

import { videoAPI, transcriptAPI, summaryAPI, templateAPI } from './api.js';
import { showToast, showLoading, hideLoading } from './components.js';
import { formatFileSize, formatDate, formatDuration } from './utils.js';

// State management
const state = {
    stats: {
        totalVideos: 0,
        processingTasks: 0,
        completedSummaries: 0,
        activeTemplates: 0,
    },
    recentVideos: [],
};

// DOM Elements
let elements = {};

/**
 * Initialize the page
 */
function init() {
    // Get DOM elements
    elements = {
        // Action buttons - find by text content
        uploadButton: Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Upload Video')
        ),
        downloadUrlButton: Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Download from URL')
        ),

        // Stats cards
        totalVideosCard: document.querySelectorAll('.text-3xl.font-bold')[0],
        processingTasksCard: document.querySelectorAll('.text-3xl.font-bold')[1],
        completedSummariesCard: document.querySelectorAll('.text-3xl.font-bold')[2],
        activeTemplatesCard: document.querySelectorAll('.text-3xl.font-bold')[3],

        // Recent videos table
        recentVideosTable: document.querySelector('table tbody'),
    };

    // Setup event listeners
    setupEventListeners();

    // Load dashboard data
    loadDashboard();

    console.log('Dashboard page initialized');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Upload button
    elements.uploadButton?.addEventListener('click', () => {
        window.location.href = '/workflow-page';
    });

    // Download URL button
    elements.downloadUrlButton?.addEventListener('click', () => {
        showDownloadUrlModal();
    });
}

/**
 * Show Download from URL Modal
 */
function showDownloadUrlModal() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white dark:bg-slate-900 rounded-xl max-w-lg w-full">
            <div class="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
                <h2 class="text-xl font-bold text-slate-900 dark:text-white">Download from URL</h2>
                <button class="close-modal text-slate-500 hover:text-primary">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="p-6 space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Video URL *
                    </label>
                    <input
                        type="url"
                        id="video-url-input"
                        placeholder="https://youtube.com/watch?v=... or video URL"
                        class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                    <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                        Supports YouTube, Vimeo, and direct video URLs (including m3u8)
                    </p>
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Title (Optional)
                    </label>
                    <input
                        type="text"
                        id="video-title-input"
                        placeholder="Custom title for the video"
                        class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                </div>
            </div>

            <div class="flex items-center justify-end gap-3 p-6 border-t border-slate-200 dark:border-slate-700">
                <button class="cancel-btn px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
                    Cancel
                </button>
                <button class="download-btn px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg flex items-center gap-2">
                    <span class="material-symbols-outlined text-base">download</span>
                    Download
                </button>
            </div>
        </div>
    `;

    // Event listeners
    modal.querySelector('.close-modal')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.cancel-btn')?.addEventListener('click', () => modal.remove());

    modal.querySelector('.download-btn')?.addEventListener('click', async () => {
        const urlInput = modal.querySelector('#video-url-input');
        const titleInput = modal.querySelector('#video-title-input');
        const url = urlInput.value.trim();
        const title = titleInput.value.trim();

        if (!url) {
            showToast('Please enter a video URL', 'error');
            urlInput.focus();
            return;
        }

        // Basic URL validation
        try {
            new URL(url);
        } catch {
            showToast('Please enter a valid URL', 'error');
            urlInput.focus();
            return;
        }

        try {
            modal.remove();
            showLoading('Starting video download...');

            const video = await videoAPI.downloadFromUrl(url, title || undefined);

            showToast('Video download started successfully', 'success');

            // Refresh dashboard data
            await loadDashboard();
        } catch (error) {
            console.error('Failed to download video:', error);
            showToast(error.message || 'Failed to download video', 'error');
        } finally {
            hideLoading();
        }
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    document.body.appendChild(modal);

    // Focus on URL input
    modal.querySelector('#video-url-input')?.focus();
}

/**
 * Load dashboard data
 */
async function loadDashboard() {
    try {
        showLoading('Loading dashboard...');

        // Load all data in parallel
        const [videos, transcripts, summaries, templates] = await Promise.all([
            videoAPI.getAll().catch(() => []),
            transcriptAPI.getAll().catch(() => []),
            summaryAPI.getAll().catch(() => []),
            templateAPI.getAll({ is_active: true }).catch(() => []),
        ]);

        // Calculate stats
        state.stats.totalVideos = videos.length;
        state.stats.processingTasks = videos.filter(v => v.status === 'processing').length;
        state.stats.completedSummaries = summaries.length;
        state.stats.activeTemplates = templates.length;

        // Get recent videos (last 10)
        state.recentVideos = videos
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, 10);

        // Update UI
        updateStats();
        renderRecentVideos();

    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showToast('Failed to load dashboard data', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Update stats cards
 */
function updateStats() {
    if (elements.totalVideosCard) {
        elements.totalVideosCard.textContent = state.stats.totalVideos.toLocaleString();
    }

    if (elements.processingTasksCard) {
        elements.processingTasksCard.textContent = state.stats.processingTasks.toLocaleString();
    }

    if (elements.completedSummariesCard) {
        elements.completedSummariesCard.textContent = state.stats.completedSummaries.toLocaleString();
    }

    if (elements.activeTemplatesCard) {
        elements.activeTemplatesCard.textContent = state.stats.activeTemplates.toLocaleString();
    }
}

/**
 * Render recent videos table
 */
function renderRecentVideos() {
    if (!elements.recentVideosTable) return;

    if (state.recentVideos.length === 0) {
        elements.recentVideosTable.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-12 text-center">
                    <div class="flex flex-col items-center gap-4">
                        <span class="material-symbols-outlined text-6xl text-slate-300 dark:text-slate-600">video_library</span>
                        <p class="text-slate-500 dark:text-slate-400 text-lg font-medium">No videos yet</p>
                        <p class="text-slate-400 dark:text-slate-500 text-sm">Upload a video to get started</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    elements.recentVideosTable.innerHTML = state.recentVideos.map(video =>
        createVideoRow(video)
    ).join('');

    // Attach event listeners
    attachRowEventListeners();
}

/**
 * Create video table row HTML
 */
function createVideoRow(video) {
    const statusColors = {
        uploaded: 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-300',
        processing: 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300',
        completed: 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300',
        failed: 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300',
    };

    const statusClass = statusColors[video.status] || statusColors.uploaded;
    const statusText = video.status.charAt(0).toUpperCase() + video.status.slice(1);

    return `
        <tr class="border-b border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50" data-id="${video.id}">
            <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                    <div class="w-16 h-12 bg-slate-200 dark:bg-slate-700 rounded flex items-center justify-center flex-shrink-0">
                        <span class="material-symbols-outlined text-slate-400">play_circle</span>
                    </div>
                    <div class="min-w-0">
                        <p class="font-medium text-slate-900 dark:text-white truncate">${video.filename}</p>
                        <p class="text-xs text-slate-500 dark:text-slate-400">${formatDuration(video.duration)}</p>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4">
                <span class="inline-flex items-center rounded-full ${statusClass} px-2.5 py-0.5 text-xs font-medium">
                    ${statusText}
                </span>
            </td>
            <td class="px-6 py-4 text-slate-600 dark:text-slate-400">${formatFileSize(video.file_size)}</td>
            <td class="px-6 py-4 text-slate-600 dark:text-slate-400">${formatDate(video.created_at)}</td>
            <td class="px-6 py-4">
                <button class="view-btn text-primary hover:text-primary/80" data-id="${video.id}">
                    <span class="material-symbols-outlined">visibility</span>
                </button>
            </td>
        </tr>
    `;
}

/**
 * Attach event listeners to table rows
 */
function attachRowEventListeners() {
    // View buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const videoId = parseInt(btn.dataset.id);
            window.location.href = `/videos-page?id=${videoId}`;
        });
    });

    // Row clicks
    document.querySelectorAll('tr[data-id]').forEach(row => {
        row.addEventListener('click', () => {
            const videoId = parseInt(row.dataset.id);
            window.location.href = `/videos-page?id=${videoId}`;
        });
        row.style.cursor = 'pointer';
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
