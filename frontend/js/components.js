/**
 * Reusable UI Components Module
 * Common UI components used across multiple pages
 */

/**
 * Show toast notification
 */
export function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white z-50 animate-fade-in ${getToastColor(type)}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function getToastColor(type) {
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500',
    };
    return colors[type] || colors.info;
}

/**
 * Show loading spinner overlay
 */
export function showLoading(message = 'Loading...') {
    const existing = document.getElementById('loading-overlay');
    if (existing) return;

    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    overlay.innerHTML = `
        <div class="bg-white rounded-lg p-6 flex flex-col items-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p class="mt-4 text-gray-700">${message}</p>
        </div>
    `;

    document.body.appendChild(overlay);
}

/**
 * Hide loading spinner overlay
 */
export function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Show confirmation modal
 */
export function showConfirmModal(message, onConfirm, onCancel = null) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Confirm Action</h3>
            <p class="text-gray-600 mb-6">${message}</p>
            <div class="flex justify-end gap-3">
                <button class="cancel-btn px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                    Cancel
                </button>
                <button class="confirm-btn px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600">
                    Confirm
                </button>
            </div>
        </div>
    `;

    const cancelBtn = modal.querySelector('.cancel-btn');
    const confirmBtn = modal.querySelector('.confirm-btn');

    cancelBtn.addEventListener('click', () => {
        modal.remove();
        if (onCancel) onCancel();
    });

    confirmBtn.addEventListener('click', () => {
        modal.remove();
        onConfirm();
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
            if (onCancel) onCancel();
        }
    });

    document.body.appendChild(modal);
}

/**
 * Format file size
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format duration (seconds to HH:MM:SS)
 */
export function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '00:00';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format date to relative time or absolute date
 */
export function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

/**
 * Get status badge HTML
 */
export function getStatusBadge(status) {
    const badges = {
        uploaded: '<span class="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">Uploaded</span>',
        processing: '<span class="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">Processing</span>',
        completed: '<span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">Completed</span>',
        failed: '<span class="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">Failed</span>',
    };
    return badges[status] || status;
}

/**
 * Create progress bar HTML
 */
export function createProgressBar(percent) {
    return `
        <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-blue-500 h-2 rounded-full transition-all duration-300" style="width: ${percent}%"></div>
        </div>
    `;
}

/**
 * Update progress bar
 */
export function updateProgressBar(element, percent) {
    const bar = element.querySelector('.bg-blue-500');
    if (bar) {
        bar.style.width = `${percent}%`;
    }
}

/**
 * Create empty state HTML
 */
export function createEmptyState(icon, title, description, actionButton = null) {
    return `
        <div class="flex flex-col items-center justify-center py-12 text-center">
            <div class="text-6xl text-gray-300 mb-4">${icon}</div>
            <h3 class="text-xl font-semibold text-gray-700 mb-2">${title}</h3>
            <p class="text-gray-500 mb-6 max-w-md">${description}</p>
            ${actionButton || ''}
        </div>
    `;
}

/**
 * Create table row for videos
 */
export function createVideoRow(video) {
    return `
        <tr class="border-b hover:bg-gray-50" data-id="${video.id}">
            <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                    <div class="w-16 h-12 bg-gray-200 rounded flex items-center justify-center">
                        <span class="material-symbols-outlined text-gray-400">play_circle</span>
                    </div>
                    <div>
                        <div class="font-medium text-gray-900">${video.filename}</div>
                        <div class="text-sm text-gray-500">${formatFileSize(video.file_size)}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">${video.source || 'Upload'}</td>
            <td class="px-6 py-4 text-sm text-gray-600">${formatDuration(video.duration)}</td>
            <td class="px-6 py-4">${getStatusBadge(video.status)}</td>
            <td class="px-6 py-4 text-sm text-gray-500">${formatDate(video.created_at)}</td>
            <td class="px-6 py-4">
                <button class="delete-btn text-red-500 hover:text-red-700">
                    <span class="material-symbols-outlined">delete</span>
                </button>
            </td>
        </tr>
    `;
}

/**
 * Create card for transcript
 */
export function createTranscriptCard(transcript) {
    const textPreview = transcript.text.substring(0, 150) + (transcript.text.length > 150 ? '...' : '');

    return `
        <div class="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow" data-id="${transcript.id}">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="font-semibold text-gray-900">Transcript #${transcript.id}</h3>
                    <p class="text-sm text-gray-500 mt-1">Language: ${transcript.language || 'Auto'}</p>
                </div>
                <button class="delete-btn text-red-500 hover:text-red-700">
                    <span class="material-symbols-outlined">delete</span>
                </button>
            </div>
            <p class="text-gray-600 text-sm mb-4">${textPreview}</p>
            <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">${formatDate(transcript.created_at)}</span>
                <button class="view-btn text-blue-500 hover:text-blue-700 text-sm font-medium">
                    View Full
                </button>
            </div>
        </div>
    `;
}

/**
 * Create card for summary
 */
export function createSummaryCard(summary) {
    const contentPreview = summary.content.substring(0, 200) + (summary.content.length > 200 ? '...' : '');

    return `
        <div class="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow" data-id="${summary.id}">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="font-semibold text-gray-900">Summary #${summary.id}</h3>
                    <span class="inline-block mt-2 px-2 py-1 text-xs font-medium rounded bg-purple-100 text-purple-800">
                        ${summary.ai_model}
                    </span>
                </div>
                <button class="delete-btn text-red-500 hover:text-red-700">
                    <span class="material-symbols-outlined">delete</span>
                </button>
            </div>
            <p class="text-gray-600 text-sm mb-4">${contentPreview}</p>
            <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">${formatDate(summary.created_at)}</span>
                <button class="view-btn text-blue-500 hover:text-blue-700 text-sm font-medium">
                    View Full
                </button>
            </div>
        </div>
    `;
}

/**
 * Create card for template
 */
export function createTemplateCard(template) {
    const contentPreview = template.content.substring(0, 150) + (template.content.length > 150 ? '...' : '');

    return `
        <div class="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow" data-id="${template.id}">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="font-semibold text-gray-900">${template.name}</h3>
                    ${template.description ? `<p class="text-sm text-gray-500 mt-1">${template.description}</p>` : ''}
                </div>
                <div class="flex items-center gap-2">
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" class="toggle-active sr-only" ${template.is_active ? 'checked' : ''}>
                        <div class="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-500"></div>
                    </label>
                    <button class="delete-btn text-red-500 hover:text-red-700">
                        <span class="material-symbols-outlined">delete</span>
                    </button>
                </div>
            </div>
            <p class="text-gray-600 text-sm mb-4 font-mono bg-gray-50 p-3 rounded">${contentPreview}</p>
            <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">${formatDate(template.created_at)}</span>
                <button class="edit-btn text-blue-500 hover:text-blue-700 text-sm font-medium">
                    Edit
                </button>
            </div>
        </div>
    `;
}

/**
 * Create workflow step indicator
 */
export function createWorkflowSteps(currentStep) {
    const steps = [
        { key: 'upload', label: 'Video', icon: 'video_file' },
        { key: 'audio', label: 'Audio', icon: 'audio_file' },
        { key: 'transcript', label: 'Transcript', icon: 'description' },
        { key: 'summary', label: 'Summary', icon: 'summarize' },
    ];

    const stepIndex = steps.findIndex(s => s.key === currentStep);

    return `
        <div class="flex items-center justify-between mb-8">
            ${steps.map((step, index) => {
                const isActive = index === stepIndex;
                const isCompleted = index < stepIndex;
                const statusClass = isCompleted ? 'bg-green-500 text-white' : isActive ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-400';

                return `
                    <div class="flex items-center ${index < steps.length - 1 ? 'flex-1' : ''}">
                        <div class="flex flex-col items-center">
                            <div class="w-12 h-12 rounded-full ${statusClass} flex items-center justify-center">
                                <span class="material-symbols-outlined">${isCompleted ? 'check' : step.icon}</span>
                            </div>
                            <span class="text-sm font-medium mt-2 ${isActive ? 'text-blue-500' : 'text-gray-500'}">${step.label}</span>
                        </div>
                        ${index < steps.length - 1 ? `<div class="flex-1 h-1 mx-4 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}"></div>` : ''}
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Debounce function for search input
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
 * Copy text to clipboard
 */
export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard', 'success');
    } catch (err) {
        showToast('Failed to copy', 'error');
    }
}
