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
        // Action buttons
        uploadButton: document.querySelector('button:has(span:contains("Upload Video"))'),
        downloadUrlButton: document.querySelector('button:has(span:contains("Download from URL"))'),

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
        window.location.href = '/videos-page';
    });
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
