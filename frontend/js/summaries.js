/**
 * Summaries Management Page
 * Handles summary listing, viewing, filtering, and management
 */

import { summaryAPI } from './api.js';
import { showToast, showLoading, hideLoading, showConfirmModal } from './components.js';
import { formatDate, truncate, debounce, copyToClipboard, downloadText } from './utils.js';

// State management
const state = {
    summaries: [],
    filteredSummaries: [],
    searchQuery: '',
    modelFilter: 'all',
    sortBy: 'newest', // newest, oldest, model
};

// DOM Elements
let elements = {};

/**
 * Initialize the page
 */
function init() {
    // Get DOM elements
    elements = {
        // Search and filters
        searchInput: document.querySelector('input[placeholder="Search summaries..."]'),
        modelFilter: document.querySelectorAll('select')[0],
        sortFilter: document.querySelectorAll('select')[1],

        // Summary grid
        summaryGrid: document.querySelector('.grid.grid-cols-1'),

        // Generate button
        generateButton: Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Generate Summary')
        ),
    };

    // Setup event listeners
    setupEventListeners();

    // Load summaries
    loadSummaries();

    console.log('Summaries page initialized');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search
    elements.searchInput?.addEventListener('input', debounce((e) => {
        state.searchQuery = e.target.value.toLowerCase();
        filterSummaries();
    }, 300));

    // Model filter
    elements.modelFilter?.addEventListener('change', (e) => {
        const value = e.target.value;
        state.modelFilter = value === 'All Models' ? 'all' : value.toLowerCase();
        filterSummaries();
    });

    // Sort filter
    elements.sortFilter?.addEventListener('change', (e) => {
        const value = e.target.value;
        if (value.includes('Newest')) state.sortBy = 'newest';
        else if (value.includes('Oldest')) state.sortBy = 'oldest';
        else if (value.includes('Model')) state.sortBy = 'model';
        filterSummaries();
    });

    // Generate button
    elements.generateButton?.addEventListener('click', () => {
        window.location.href = '/workflow-page';
    });
}

/**
 * Load summaries from API
 */
async function loadSummaries() {
    try {
        showLoading('Loading summaries...');
        const summaries = await summaryAPI.getAll();
        state.summaries = summaries;
        state.filteredSummaries = summaries;
        filterSummaries(); // Apply default sort
    } catch (error) {
        console.error('Failed to load summaries:', error);
        showToast('Failed to load summaries', 'error');
        renderEmptyState('Error loading summaries');
    } finally {
        hideLoading();
    }
}

/**
 * Filter and sort summaries
 */
function filterSummaries() {
    let filtered = state.summaries;

    // Filter by search query
    if (state.searchQuery) {
        filtered = filtered.filter(s =>
            s.content.toLowerCase().includes(state.searchQuery) ||
            (s.ai_model && s.ai_model.toLowerCase().includes(state.searchQuery))
        );
    }

    // Filter by model
    if (state.modelFilter && state.modelFilter !== 'all') {
        filtered = filtered.filter(s =>
            s.ai_model.toLowerCase().includes(state.modelFilter)
        );
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
        switch (state.sortBy) {
            case 'newest':
                return new Date(b.created_at) - new Date(a.created_at);
            case 'oldest':
                return new Date(a.created_at) - new Date(b.created_at);
            case 'model':
                return (a.ai_model || '').localeCompare(b.ai_model || '');
            default:
                return 0;
        }
    });

    state.filteredSummaries = filtered;
    renderSummaries();
}

/**
 * Render summaries grid
 */
function renderSummaries() {
    if (!elements.summaryGrid) return;

    if (state.filteredSummaries.length === 0) {
        renderEmptyState();
        return;
    }

    elements.summaryGrid.innerHTML = state.filteredSummaries.map(summary =>
        createSummaryCard(summary)
    ).join('');

    // Attach event listeners to cards
    attachCardEventListeners();
}

/**
 * Create summary card HTML
 */
function createSummaryCard(summary) {
    const contentPreview = truncate(summary.content, 250, '...');
    const wordCount = summary.content.split(/\s+/).length;

    // Extract model name for display
    const modelName = extractModelName(summary.ai_model);
    const modelColor = getModelColor(summary.ai_model);

    return `
        <div class="flex flex-col gap-4 p-5 bg-white dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-800 hover:border-primary/50 transition-all duration-300" data-id="${summary.id}">
            <div class="flex justify-between items-start">
                <a class="text-lg font-bold text-gray-900 dark:text-white hover:text-primary dark:hover:text-primary/90 transition-colors cursor-pointer view-summary" data-id="${summary.id}">
                    Summary #${summary.id}
                </a>
                <span class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">${formatDate(summary.created_at)}</span>
            </div>
            <div>
                <span class="inline-flex items-center gap-1.5 ${modelColor} text-xs font-medium px-2 py-1 rounded-full">
                    <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                    ${modelName}
                </span>
            </div>
            <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed line-clamp-3">
                ${contentPreview}
            </p>
            <div class="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400">
                <span>${wordCount} words</span>
                <a class="font-semibold text-primary hover:underline cursor-pointer view-summary" data-id="${summary.id}">Read More</a>
            </div>
            <div class="flex items-center gap-2 border-t border-gray-200 dark:border-gray-800 pt-4 mt-auto">
                <button class="copy-btn flex items-center justify-center gap-2 h-9 px-3 rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-sm font-medium" data-id="${summary.id}">
                    <span class="material-symbols-outlined text-base">content_copy</span> Copy
                </button>
                <button class="download-btn flex items-center justify-center gap-2 h-9 px-3 rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-sm font-medium" data-id="${summary.id}">
                    <span class="material-symbols-outlined text-base">download</span> Download
                </button>
                <button class="delete-btn flex items-center justify-center gap-2 h-9 px-3 rounded-md bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400 text-sm font-medium ml-auto" data-id="${summary.id}">
                    <span class="material-symbols-outlined text-base">delete</span>
                </button>
            </div>
        </div>
    `;
}

/**
 * Extract model name from full model string
 */
function extractModelName(modelString) {
    if (!modelString) return 'Unknown Model';

    // Extract common model names
    if (modelString.includes('claude-3.5-sonnet')) return 'Claude 3.5 Sonnet';
    if (modelString.includes('claude-3')) return 'Claude 3';
    if (modelString.includes('gpt-4')) return 'GPT-4';
    if (modelString.includes('gpt-3.5')) return 'GPT-3.5';
    if (modelString.includes('llama')) return 'Llama';

    // Default to the part after the last slash
    const parts = modelString.split('/');
    return parts[parts.length - 1];
}

/**
 * Get model badge color
 */
function getModelColor(modelString) {
    if (!modelString) return 'bg-gray-100 text-gray-800';

    if (modelString.includes('claude')) return 'bg-purple-100 dark:bg-purple-900/50 text-purple-800 dark:text-purple-300';
    if (modelString.includes('gpt')) return 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300';
    if (modelString.includes('llama')) return 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300';

    return 'bg-gray-100 dark:bg-gray-900/50 text-gray-800 dark:text-gray-300';
}

/**
 * Render empty state
 */
function renderEmptyState(message = 'No summaries found') {
    if (!elements.summaryGrid) return;

    elements.summaryGrid.innerHTML = `
        <div class="col-span-1 lg:col-span-2 flex flex-col items-center justify-center text-center p-12 bg-white dark:bg-gray-900/50 rounded-xl border-2 border-dashed border-gray-200 dark:border-gray-800">
            <span class="material-symbols-outlined text-5xl text-gray-400 dark:text-gray-600 mb-4">description</span>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-1">No Summaries Found</h3>
            <p class="text-gray-500 dark:text-gray-400 mb-4 max-w-xs">${message}</p>
            <button class="create-empty-btn flex items-center justify-center gap-2 min-w-[84px] cursor-pointer rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-primary/90 transition-colors">
                <span class="material-symbols-outlined text-base">add_circle</span>
                <span class="truncate">Generate Summary</span>
            </button>
        </div>
    `;

    document.querySelector('.create-empty-btn')?.addEventListener('click', () => {
        window.location.href = '/workflow-page';
    });
}

/**
 * Attach event listeners to card elements
 */
function attachCardEventListeners() {
    // View summary
    document.querySelectorAll('.view-summary').forEach(el => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            const summaryId = parseInt(el.dataset.id);
            viewSummary(summaryId);
        });
    });

    // Copy
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const summaryId = parseInt(btn.dataset.id);
            const summary = state.summaries.find(s => s.id === summaryId);
            if (summary) {
                const success = await copyToClipboard(summary.content);
                if (success) showToast('Summary copied to clipboard', 'success');
            }
        });
    });

    // Download
    document.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const summaryId = parseInt(btn.dataset.id);
            const summary = state.summaries.find(s => s.id === summaryId);
            if (summary) {
                downloadText(summary.content, `summary_${summaryId}.txt`, 'text/plain');
                showToast('Summary downloaded', 'success');
            }
        });
    });

    // Delete
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const summaryId = parseInt(btn.dataset.id);
            handleDelete(summaryId);
        });
    });
}

/**
 * View summary in modal
 */
function viewSummary(summaryId) {
    const summary = state.summaries.find(s => s.id === summaryId);
    if (!summary) return;

    const wordCount = summary.content.split(/\s+/).length;
    const modelName = extractModelName(summary.ai_model);

    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-900 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-auto">
            <div class="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 p-6 flex justify-between items-start">
                <div>
                    <h3 class="text-2xl font-bold text-gray-900 dark:text-white">Summary #${summary.id}</h3>
                    <div class="flex items-center gap-2 mt-2">
                        <span class="inline-flex items-center gap-1.5 ${getModelColor(summary.ai_model)} text-xs font-medium px-2 py-1 rounded-full">
                            <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                            </svg>
                            ${modelName}
                        </span>
                        <span class="text-gray-500 dark:text-gray-400 text-sm">·</span>
                        <p class="text-gray-500 dark:text-gray-400 text-sm">${formatDate(summary.created_at)}</p>
                        <span class="text-gray-500 dark:text-gray-400 text-sm">·</span>
                        <p class="text-gray-500 dark:text-gray-400 text-sm">${wordCount} words</p>
                    </div>
                </div>
                <button class="close-btn text-gray-500 dark:text-gray-400 hover:text-primary">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="p-6">
                <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                    <p class="text-gray-900 dark:text-white text-base leading-relaxed whitespace-pre-wrap">${summary.content}</p>
                </div>
            </div>
            <div class="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 p-6 flex justify-end gap-3">
                <button class="copy-full-btn px-4 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">
                    Copy
                </button>
                <button class="download-full-btn px-4 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">
                    Download
                </button>
            </div>
        </div>
    `;

    // Event listeners
    modal.querySelector('.close-btn')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.copy-full-btn')?.addEventListener('click', async () => {
        const success = await copyToClipboard(summary.content);
        if (success) showToast('Summary copied to clipboard', 'success');
    });
    modal.querySelector('.download-full-btn')?.addEventListener('click', () => {
        downloadText(summary.content, `summary_${summaryId}.txt`, 'text/plain');
        showToast('Summary downloaded', 'success');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    document.body.appendChild(modal);
}

/**
 * Handle summary deletion
 */
function handleDelete(summaryId) {
    showConfirmModal(
        'Are you sure you want to delete this summary? This action cannot be undone.',
        async () => {
            try {
                showLoading('Deleting summary...');
                await summaryAPI.delete(summaryId);
                showToast('Summary deleted successfully', 'success');

                // Remove from state
                state.summaries = state.summaries.filter(s => s.id !== summaryId);
                filterSummaries();
            } catch (error) {
                console.error('Failed to delete summary:', error);
                showToast('Failed to delete summary', 'error');
            } finally {
                hideLoading();
            }
        }
    );
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
