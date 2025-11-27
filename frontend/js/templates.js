/**
 * Prompt Templates Management Page
 * Handles template listing, creation, editing, and activation
 */

import { templateAPI } from './api.js';
import { showToast, showLoading, hideLoading, showConfirmModal } from './components.js';
import { formatDate, debounce } from './utils.js';

// State management
const state = {
    templates: [],
    filteredTemplates: [],
    searchQuery: '',
    filterActive: 'all', // all, active, inactive
};

// DOM Elements
let elements = {};

/**
 * Initialize the page
 */
function init() {
    // Get DOM elements
    elements = {
        searchInput: document.querySelector('input[placeholder*="Search"]'),
        filterButtons: document.querySelectorAll('[data-filter]'),
        templateGrid: document.querySelector('.grid'),
        createButton: Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Create Template')
        ),
    };

    // Setup event listeners
    setupEventListeners();

    // Load templates
    loadTemplates();

    console.log('Templates page initialized');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search
    elements.searchInput?.addEventListener('input', debounce((e) => {
        state.searchQuery = e.target.value.toLowerCase();
        filterTemplates();
    }, 300));

    // Filter buttons
    elements.filterButtons?.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const filter = e.currentTarget.dataset.filter;
            state.filterActive = filter;
            filterTemplates();
        });
    });

    // Create button
    elements.createButton?.addEventListener('click', () => {
        showCreateModal();
    });
}

/**
 * Load templates from API
 */
async function loadTemplates() {
    try {
        showLoading('Loading templates...');
        const templates = await templateAPI.getAll();
        state.templates = templates;
        state.filteredTemplates = templates;
        filterTemplates();
    } catch (error) {
        console.error('Failed to load templates:', error);
        showToast('Failed to load templates', 'error');
        renderEmptyState('Error loading templates');
    } finally {
        hideLoading();
    }
}

/**
 * Filter templates
 */
function filterTemplates() {
    let filtered = state.templates;

    // Filter by search query
    if (state.searchQuery) {
        filtered = filtered.filter(t =>
            t.name.toLowerCase().includes(state.searchQuery) ||
            (t.description && t.description.toLowerCase().includes(state.searchQuery))
        );
    }

    // Filter by active status
    if (state.filterActive === 'active') {
        filtered = filtered.filter(t => t.is_active);
    } else if (state.filterActive === 'inactive') {
        filtered = filtered.filter(t => !t.is_active);
    }

    state.filteredTemplates = filtered;
    renderTemplates();
}

/**
 * Render templates
 */
function renderTemplates() {
    if (!elements.templateGrid) return;

    if (state.filteredTemplates.length === 0) {
        renderEmptyState();
        return;
    }

    elements.templateGrid.innerHTML = state.filteredTemplates.map(template =>
        createTemplateCard(template)
    ).join('');

    // Attach event listeners
    attachCardEventListeners();
}

/**
 * Create template card HTML
 */
function createTemplateCard(template) {
    return `
        <div class="flex flex-col gap-4 p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div class="flex justify-between items-start">
                <h3 class="text-lg font-bold text-slate-900 dark:text-white">${template.name}</h3>
                <div class="flex items-center gap-2">
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" class="sr-only peer toggle-active" data-id="${template.id}" ${template.is_active ? 'checked' : ''}>
                        <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/40 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-primary"></div>
                    </label>
                </div>
            </div>
            <p class="text-slate-600 dark:text-slate-400 text-sm">${template.description || 'No description'}</p>
            <div class="text-xs text-slate-500 dark:text-slate-400">
                <p>Created: ${formatDate(template.created_at)}</p>
                ${template.category ? `<p>Category: ${template.category}</p>` : ''}
            </div>
            <div class="flex items-center gap-2 border-t border-slate-200 dark:border-slate-800 pt-4">
                <button class="edit-btn flex items-center gap-2 px-3 py-2 rounded-md bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-sm font-medium" data-id="${template.id}">
                    <span class="material-symbols-outlined text-base">edit</span>
                    Edit
                </button>
                <button class="delete-btn flex items-center gap-2 px-3 py-2 rounded-md bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400 text-sm font-medium ml-auto" data-id="${template.id}">
                    <span class="material-symbols-outlined text-base">delete</span>
                </button>
            </div>
        </div>
    `;
}

/**
 * Render empty state
 */
function renderEmptyState(message = 'No templates found') {
    if (!elements.templateGrid) return;

    elements.templateGrid.innerHTML = `
        <div class="col-span-full flex flex-col items-center justify-center text-center p-12 bg-white dark:bg-slate-900 rounded-xl border-2 border-dashed border-slate-200 dark:border-slate-800">
            <span class="material-symbols-outlined text-5xl text-slate-400 dark:text-slate-600 mb-4">grid_view</span>
            <h3 class="text-xl font-semibold text-slate-900 dark:text-white mb-1">No Templates</h3>
            <p class="text-slate-500 dark:text-slate-400 mb-4">${message}</p>
            <button class="create-empty-btn flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                <span class="material-symbols-outlined text-base">add_circle</span>
                Create Template
            </button>
        </div>
    `;

    document.querySelector('.create-empty-btn')?.addEventListener('click', showCreateModal);
}

/**
 * Attach event listeners to cards
 */
function attachCardEventListeners() {
    // Toggle active
    document.querySelectorAll('.toggle-active').forEach(toggle => {
        toggle.addEventListener('change', async (e) => {
            const templateId = parseInt(toggle.dataset.id);
            const isActive = toggle.checked;

            try {
                await templateAPI.toggleActive(templateId, isActive);
                showToast(`Template ${isActive ? 'activated' : 'deactivated'}`, 'success');

                // Update state
                const template = state.templates.find(t => t.id === templateId);
                if (template) template.is_active = isActive;
                filterTemplates();
            } catch (error) {
                console.error('Failed to toggle template:', error);
                showToast('Failed to update template', 'error');
                toggle.checked = !isActive; // Revert
            }
        });
    });

    // Edit
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const templateId = parseInt(btn.dataset.id);
            const template = state.templates.find(t => t.id === templateId);
            if (template) showEditModal(template);
        });
    });

    // Delete
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const templateId = parseInt(btn.dataset.id);
            handleDelete(templateId);
        });
    });
}

/**
 * Show create modal
 */
function showCreateModal() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white dark:bg-slate-900 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
            <div class="sticky top-0 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 p-6 flex justify-between items-start">
                <div>
                    <h3 class="text-2xl font-bold text-slate-900 dark:text-white">Create Prompt Template</h3>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Create a new template for summarization</p>
                </div>
                <button class="close-btn text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="p-6 space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-900 dark:text-white mb-2">Template Name *</label>
                    <input
                        type="text"
                        id="template-name"
                        class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white p-2 focus:border-primary focus:ring-primary"
                        placeholder="e.g., Meeting Summary, Interview Analysis"
                        required
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-900 dark:text-white mb-2">Description</label>
                    <input
                        type="text"
                        id="template-description"
                        class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white p-2 focus:border-primary focus:ring-primary"
                        placeholder="Brief description of the template purpose"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-900 dark:text-white mb-2">Category</label>
                    <input
                        type="text"
                        id="template-category"
                        class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white p-2 focus:border-primary focus:ring-primary"
                        placeholder="e.g., general, meeting, interview"
                        value="general"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-900 dark:text-white mb-2">Prompt Content *</label>
                    <textarea
                        id="template-content"
                        rows="8"
                        class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white p-2 focus:border-primary focus:ring-primary font-mono text-sm"
                        placeholder="Enter your prompt template. Use {transcript} as a placeholder for the transcript text.&#10;&#10;Example:&#10;Summarize the following transcript and extract key points:&#10;{transcript}"
                        required
                    ></textarea>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Use <code class="bg-slate-100 dark:bg-slate-800 px-1 rounded">{transcript}</code> as a placeholder for the transcript text
                    </p>
                </div>

                <div class="flex justify-end gap-3 mt-6 pt-6 border-t border-slate-200 dark:border-slate-800">
                    <button class="cancel-btn px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700">
                        Cancel
                    </button>
                    <button class="create-btn px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                        Create Template
                    </button>
                </div>
            </div>
        </div>
    `;

    // Event listeners
    modal.querySelector('.close-btn')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.cancel-btn')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.create-btn')?.addEventListener('click', async () => {
        const name = document.getElementById('template-name')?.value.trim();
        const description = document.getElementById('template-description')?.value.trim() || null;
        const category = document.getElementById('template-category')?.value.trim() || 'general';
        const content = document.getElementById('template-content')?.value.trim();

        if (!name) {
            showToast('Please enter a template name', 'error');
            return;
        }

        if (!content) {
            showToast('Please enter template content', 'error');
            return;
        }

        if (!content.includes('{transcript}')) {
            showToast('Template content must include {transcript} placeholder', 'error');
            return;
        }

        try {
            showLoading('Creating template...');
            modal.remove();
            const template = await templateAPI.create(name, content, description, category);
            showToast('Template created successfully!', 'success');

            // Add to state and re-render
            state.templates.unshift(template);
            filterTemplates();
        } catch (error) {
            console.error('Failed to create template:', error);
            showToast(error.message || 'Failed to create template', 'error');
        } finally {
            hideLoading();
        }
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    document.body.appendChild(modal);
}

/**
 * Show edit modal
 */
function showEditModal(template) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white dark:bg-slate-900 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
            <div class="sticky top-0 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 p-6 flex justify-between items-start">
                <div>
                    <h3 class="text-2xl font-bold text-slate-900 dark:text-white">Edit Prompt Template</h3>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Update template settings and content</p>
                </div>
                <button class="close-btn text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="p-6 space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-900 dark:text-white mb-2">Template Name *</label>
                    <input
                        type="text"
                        id="edit-template-name"
                        class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white p-2 focus:border-primary focus:ring-primary"
                        value="${template.name}"
                        required
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-900 dark:text-white mb-2">Description</label>
                    <input
                        type="text"
                        id="edit-template-description"
                        class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white p-2 focus:border-primary focus:ring-primary"
                        value="${template.description || ''}"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-900 dark:text-white mb-2">Category</label>
                    <input
                        type="text"
                        id="edit-template-category"
                        class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white p-2 focus:border-primary focus:ring-primary"
                        value="${template.category || 'general'}"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-900 dark:text-white mb-2">Prompt Content *</label>
                    <textarea
                        id="edit-template-content"
                        rows="8"
                        class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white p-2 focus:border-primary focus:ring-primary font-mono text-sm"
                        required
                    >${template.content}</textarea>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Use <code class="bg-slate-100 dark:bg-slate-800 px-1 rounded">{transcript}</code> as a placeholder for the transcript text
                    </p>
                </div>

                <div class="flex justify-end gap-3 mt-6 pt-6 border-t border-slate-200 dark:border-slate-800">
                    <button class="cancel-btn px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700">
                        Cancel
                    </button>
                    <button class="update-btn px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                        Update Template
                    </button>
                </div>
            </div>
        </div>
    `;

    // Event listeners
    modal.querySelector('.close-btn')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.cancel-btn')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.update-btn')?.addEventListener('click', async () => {
        const name = document.getElementById('edit-template-name')?.value.trim();
        const description = document.getElementById('edit-template-description')?.value.trim() || null;
        const category = document.getElementById('edit-template-category')?.value.trim() || 'general';
        const content = document.getElementById('edit-template-content')?.value.trim();

        if (!name) {
            showToast('Please enter a template name', 'error');
            return;
        }

        if (!content) {
            showToast('Please enter template content', 'error');
            return;
        }

        if (!content.includes('{transcript}')) {
            showToast('Template content must include {transcript} placeholder', 'error');
            return;
        }

        try {
            showLoading('Updating template...');
            modal.remove();
            const updatedTemplate = await templateAPI.update(template.id, {
                name,
                description,
                category,
                content
            });
            showToast('Template updated successfully!', 'success');

            // Update state
            const index = state.templates.findIndex(t => t.id === template.id);
            if (index !== -1) {
                state.templates[index] = updatedTemplate;
            }
            filterTemplates();
        } catch (error) {
            console.error('Failed to update template:', error);
            showToast(error.message || 'Failed to update template', 'error');
        } finally {
            hideLoading();
        }
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    document.body.appendChild(modal);
}

/**
 * Handle template deletion
 */
function handleDelete(templateId) {
    showConfirmModal(
        'Are you sure you want to delete this template? This action cannot be undone.',
        async () => {
            try {
                showLoading('Deleting template...');
                await templateAPI.delete(templateId);
                showToast('Template deleted successfully', 'success');

                // Remove from state
                state.templates = state.templates.filter(t => t.id !== templateId);
                filterTemplates();
            } catch (error) {
                console.error('Failed to delete template:', error);
                showToast('Failed to delete template', 'error');
            } finally {
                hideLoading();
            }
        }
    );
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
