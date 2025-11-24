/**
 * Transcripts Management Page
 * Handles transcript listing, creation, viewing, and summary generation
 */

import { transcriptAPI, audioAPI, summaryAPI } from './api.js';
import { showToast, showLoading, hideLoading, showConfirmModal } from './components.js';
import { formatDate, truncate, debounce, copyToClipboard } from './utils.js';

// State management
const state = {
    transcripts: [],
    filteredTranscripts: [],
    searchQuery: '',
    languageFilter: null,
    dateRangeFilter: null,
};

// DOM Elements
let elements = {};

/**
 * Initialize the page
 */
function init() {
    // Get DOM elements
    elements = {
        // Search
        searchInput: document.querySelector('input[placeholder="Search in transcripts..."]'),

        // Filters
        languageFilterButton: Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Language')
        ),
        dateRangeFilterButton: Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Date Range')
        ),

        // Transcript grid
        transcriptGrid: document.querySelector('.grid.grid-cols-1'),

        // Create button
        createButton: Array.from(document.querySelectorAll('button')).find(btn =>
            btn.textContent.includes('Create Transcript')
        ),
    };

    // Setup event listeners
    setupEventListeners();

    // Load transcripts
    loadTranscripts();

    console.log('Transcripts page initialized');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search
    elements.searchInput?.addEventListener('input', debounce((e) => {
        state.searchQuery = e.target.value.toLowerCase();
        filterTranscripts();
    }, 300));

    // Create button
    elements.createButton?.addEventListener('click', showCreateTranscriptModal);

    // Note: Filter buttons would require dropdown menus - simplified for now
}

/**
 * Load transcripts from API
 */
async function loadTranscripts() {
    try {
        showLoading('Loading transcripts...');
        const transcripts = await transcriptAPI.getAll();
        state.transcripts = transcripts;
        state.filteredTranscripts = transcripts;
        renderTranscripts();
    } catch (error) {
        console.error('Failed to load transcripts:', error);
        showToast('Failed to load transcripts', 'error');
        renderEmptyState('Error loading transcripts');
    } finally {
        hideLoading();
    }
}

/**
 * Filter transcripts based on search and filters
 */
function filterTranscripts() {
    let filtered = state.transcripts;

    // Filter by search query
    if (state.searchQuery) {
        filtered = filtered.filter(t =>
            t.text.toLowerCase().includes(state.searchQuery) ||
            (t.audio_id && t.audio_id.toString().includes(state.searchQuery))
        );
    }

    // Filter by language
    if (state.languageFilter) {
        filtered = filtered.filter(t => t.language === state.languageFilter);
    }

    state.filteredTranscripts = filtered;
    renderTranscripts();
}

/**
 * Render transcripts grid
 */
function renderTranscripts() {
    if (!elements.transcriptGrid) return;

    if (state.filteredTranscripts.length === 0) {
        renderEmptyState();
        return;
    }

    elements.transcriptGrid.innerHTML = state.filteredTranscripts.map(transcript =>
        createTranscriptCard(transcript)
    ).join('');

    // Attach event listeners to cards
    attachCardEventListeners();
}

/**
 * Create transcript card HTML
 */
function createTranscriptCard(transcript) {
    const languageColors = {
        'auto': 'bg-gray-100 text-gray-800',
        'english': 'bg-green-100 text-green-800',
        'korean': 'bg-blue-100 text-blue-800',
        'spanish': 'bg-yellow-100 text-yellow-800',
        'french': 'bg-purple-100 text-purple-800',
    };

    const language = (transcript.language || 'auto').toLowerCase();
    const languageClass = languageColors[language] || languageColors.auto;
    const languageText = language.charAt(0).toUpperCase() + language.slice(1);

    const textPreview = truncate(transcript.text, 150, '...');
    const charCount = transcript.text.length;

    return `
        <div class="flex flex-col bg-surface-light dark:bg-surface-dark rounded-xl border border-border-light dark:border-border-dark shadow-sm hover:shadow-lg hover:border-primary/50 transition-all duration-300" data-id="${transcript.id}">
            <div class="p-4 border-b border-border-light dark:border-border-dark">
                <div class="flex justify-between items-start gap-2">
                    <p class="text-text-primary-light dark:text-text-primary-dark text-base font-semibold leading-normal">Transcript #${transcript.id}</p>
                    <div class="relative">
                        <button class="more-btn text-text-secondary-light dark:text-text-secondary-dark hover:text-primary" data-id="${transcript.id}">
                            <span class="material-symbols-outlined">more_vert</span>
                        </button>
                    </div>
                </div>
                <div class="flex items-center gap-2 mt-1">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${languageClass}">${languageText}</span>
                    <span class="text-text-secondary-light dark:text-text-secondary-dark text-sm">·</span>
                    <p class="text-text-secondary-light dark:text-text-secondary-dark text-sm font-normal leading-normal">${formatDate(transcript.created_at)}</p>
                </div>
            </div>
            <div class="p-4 flex-grow cursor-pointer view-transcript" data-id="${transcript.id}">
                <p class="text-text-secondary-light dark:text-text-secondary-dark text-sm font-normal leading-relaxed line-clamp-3">
                    ${textPreview}
                </p>
            </div>
            <div class="p-4 border-t border-border-light dark:border-border-dark flex justify-between items-center">
                <p class="text-text-secondary-light dark:text-text-secondary-dark text-sm font-normal">${charCount.toLocaleString()} chars</p>
                <button class="generate-summary-btn flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-9 px-3 bg-primary/10 text-primary text-sm font-bold leading-normal tracking-[0.015em] hover:bg-primary/20" data-id="${transcript.id}">
                    <span class="truncate">Generate Summary</span>
                </button>
            </div>
        </div>
    `;
}

/**
 * Render empty state
 */
function renderEmptyState(message = 'No transcripts found') {
    if (!elements.transcriptGrid) return;

    elements.transcriptGrid.innerHTML = `
        <div class="col-span-1 md:col-span-2 lg:col-span-2 xl:col-span-3 flex flex-col items-center justify-center text-center p-12 bg-surface-light dark:bg-surface-dark rounded-xl border-2 border-dashed border-border-light dark:border-border-dark">
            <span class="material-symbols-outlined text-5xl text-text-secondary-light dark:text-text-secondary-dark mb-4">description</span>
            <h3 class="text-xl font-semibold text-text-primary-light dark:text-text-primary-dark mb-1">No Transcripts Found</h3>
            <p class="text-text-secondary-light dark:text-text-secondary-dark mb-4 max-w-xs">${message}</p>
            <button class="create-empty-btn flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-primary/90 gap-2">
                <span class="material-symbols-outlined">add</span>
                <span class="truncate">Create Transcript</span>
            </button>
        </div>
    `;

    document.querySelector('.create-empty-btn')?.addEventListener('click', showCreateTranscriptModal);
}

/**
 * Attach event listeners to card elements
 */
function attachCardEventListeners() {
    // View transcript
    document.querySelectorAll('.view-transcript').forEach(el => {
        el.addEventListener('click', (e) => {
            const transcriptId = parseInt(el.dataset.id);
            viewTranscript(transcriptId);
        });
    });

    // Generate summary
    document.querySelectorAll('.generate-summary-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const transcriptId = parseInt(btn.dataset.id);
            showGenerateSummaryModal(transcriptId);
        });
    });

    // More options
    document.querySelectorAll('.more-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const transcriptId = parseInt(btn.dataset.id);
            showOptionsMenu(transcriptId, btn);
        });
    });
}

/**
 * View transcript in modal
 */
function viewTranscript(transcriptId) {
    const transcript = state.transcripts.find(t => t.id === transcriptId);
    if (!transcript) return;

    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white dark:bg-surface-dark rounded-xl max-w-4xl w-full max-h-[90vh] overflow-auto">
            <div class="sticky top-0 bg-white dark:bg-surface-dark border-b border-border-light dark:border-border-dark p-6 flex justify-between items-start">
                <div>
                    <h3 class="text-2xl font-bold text-text-primary-light dark:text-text-primary-dark">Transcript #${transcript.id}</h3>
                    <div class="flex items-center gap-2 mt-2">
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">${transcript.language || 'Auto'}</span>
                        <span class="text-text-secondary-light dark:text-text-secondary-dark text-sm">·</span>
                        <p class="text-text-secondary-light dark:text-text-secondary-dark text-sm">${formatDate(transcript.created_at)}</p>
                        <span class="text-text-secondary-light dark:text-text-secondary-dark text-sm">·</span>
                        <p class="text-text-secondary-light dark:text-text-secondary-dark text-sm">${transcript.text.length.toLocaleString()} characters</p>
                    </div>
                </div>
                <button class="close-btn text-text-secondary-light dark:text-text-secondary-dark hover:text-primary">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="p-6">
                <div class="bg-surface-light dark:bg-surface-dark rounded-lg p-6 border border-border-light dark:border-border-dark">
                    <p class="text-text-primary-light dark:text-text-primary-dark text-base leading-relaxed whitespace-pre-wrap">${transcript.text}</p>
                </div>
            </div>
            <div class="sticky bottom-0 bg-white dark:bg-surface-dark border-t border-border-light dark:border-border-dark p-6 flex justify-end gap-3">
                <button class="copy-btn px-4 py-2 bg-surface-light dark:bg-surface-dark border border-border-light dark:border-border-dark text-text-primary-light dark:text-text-primary-dark rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
                    Copy Text
                </button>
                <button class="generate-btn px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                    Generate Summary
                </button>
            </div>
        </div>
    `;

    // Event listeners
    modal.querySelector('.close-btn')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.copy-btn')?.addEventListener('click', async () => {
        const success = await copyToClipboard(transcript.text);
        if (success) showToast('Text copied to clipboard', 'success');
    });
    modal.querySelector('.generate-btn')?.addEventListener('click', () => {
        modal.remove();
        showGenerateSummaryModal(transcriptId);
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    document.body.appendChild(modal);
}

/**
 * Show create transcript modal - Audio Selection
 */
async function showCreateTranscriptModal() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white dark:bg-surface-dark rounded-xl max-w-2xl w-full">
            <div class="flex justify-between items-start p-6 border-b border-border-light dark:border-border-dark">
                <div>
                    <h3 class="text-xl font-bold text-text-primary-light dark:text-text-primary-dark">Create Transcript</h3>
                    <p class="text-sm text-text-secondary-light dark:text-text-secondary-dark mt-1">Select an audio file to transcribe</p>
                </div>
                <button class="close-btn text-text-secondary-light dark:text-text-secondary-dark hover:text-primary">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="p-6 space-y-4">
                <!-- Language Selection -->
                <div>
                    <label class="block text-sm font-medium text-text-primary-light dark:text-text-primary-dark mb-2">Language</label>
                    <select
                        id="language-select"
                        class="w-full rounded-lg border border-border-light dark:border-border-dark bg-surface-light dark:bg-surface-dark text-text-primary-light dark:text-text-primary-dark p-2 focus:border-primary focus:ring-primary"
                    >
                        <option value="ko">Korean</option>
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="ja">Japanese</option>
                        <option value="zh">Chinese</option>
                    </select>
                </div>

                <!-- Search Bar -->
                <div>
                    <label class="block text-sm font-medium text-text-primary-light dark:text-text-primary-dark mb-2">Search Audio Files</label>
                    <input
                        type="text"
                        id="audio-search"
                        class="w-full rounded-lg border border-border-light dark:border-border-dark bg-surface-light dark:bg-surface-dark text-text-primary-light dark:text-text-primary-dark p-2 focus:border-primary focus:ring-primary"
                        placeholder="Search by filename..."
                    />
                </div>

                <!-- Audio List -->
                <div class="border border-border-light dark:border-border-dark rounded-lg overflow-hidden">
                    <div id="audio-list-container" class="max-h-96 overflow-y-auto">
                        <div class="flex items-center justify-center p-8">
                            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Event listeners
    modal.querySelector('.close-btn')?.addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    // Load audios
    await loadAudiosForSelection(modal);
}

/**
 * Load audios for selection modal
 */
async function loadAudiosForSelection(modal) {
    const container = modal.querySelector('#audio-list-container');
    const searchInput = modal.querySelector('#audio-search');
    const languageSelect = modal.querySelector('#language-select');

    try {
        const response = await audioAPI.getAll();
        const audios = response.items || response;

        if (!audios || audios.length === 0) {
            container.innerHTML = `
                <div class="flex flex-col items-center justify-center p-8 text-center">
                    <span class="material-symbols-outlined text-5xl text-text-secondary-light dark:text-text-secondary-dark mb-2">music_off</span>
                    <p class="text-text-secondary-light dark:text-text-secondary-dark">No audio files available</p>
                    <p class="text-sm text-text-secondary-light dark:text-text-secondary-dark mt-1">Please extract audio from a video first</p>
                </div>
            `;
            return;
        }

        // Render audio list
        const renderAudios = (filteredAudios) => {
            if (filteredAudios.length === 0) {
                container.innerHTML = `
                    <div class="flex flex-col items-center justify-center p-8">
                        <p class="text-text-secondary-light dark:text-text-secondary-dark">No matching audio files found</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = filteredAudios.map(audio => `
                <div class="audio-item flex items-center justify-between p-4 border-b border-border-light dark:border-border-dark hover:bg-surface-light dark:hover:bg-gray-800 cursor-pointer transition-colors"
                     data-audio-id="${audio.id}">
                    <div class="flex items-center gap-3 flex-1">
                        <span class="material-symbols-outlined text-primary">audio_file</span>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-text-primary-light dark:text-text-primary-dark truncate">${audio.filename}</p>
                            <div class="flex items-center gap-2 mt-1">
                                <span class="text-xs text-text-secondary-light dark:text-text-secondary-dark">${formatFileSize(audio.file_size)}</span>
                                <span class="text-xs text-text-secondary-light dark:text-text-secondary-dark">•</span>
                                <span class="text-xs text-text-secondary-light dark:text-text-secondary-dark">${formatDuration(audio.duration)}</span>
                                <span class="text-xs text-text-secondary-light dark:text-text-secondary-dark">•</span>
                                <span class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800">${audio.status}</span>
                            </div>
                        </div>
                    </div>
                    <button class="select-audio-btn flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary text-sm font-medium rounded-lg hover:bg-primary/20 transition-colors"
                            data-audio-id="${audio.id}">
                        <span class="material-symbols-outlined text-sm">check_circle</span>
                        <span>Select</span>
                    </button>
                </div>
            `).join('');

            // Attach select event listeners
            container.querySelectorAll('.select-audio-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const audioId = parseInt(btn.dataset.audioId);
                    const language = languageSelect.value;
                    await handleAudioSelection(audioId, language, modal);
                });
            });

            // Click on row to select
            container.querySelectorAll('.audio-item').forEach(item => {
                item.addEventListener('click', async (e) => {
                    if (e.target.closest('.select-audio-btn')) return;
                    const audioId = parseInt(item.dataset.audioId);
                    const language = languageSelect.value;
                    await handleAudioSelection(audioId, language, modal);
                });
            });
        };

        // Initial render
        renderAudios(audios);

        // Search functionality
        searchInput?.addEventListener('input', debounce((e) => {
            const query = e.target.value.toLowerCase();
            const filtered = audios.filter(audio =>
                audio.filename.toLowerCase().includes(query)
            );
            renderAudios(filtered);
        }, 300));

    } catch (error) {
        console.error('Failed to load audios:', error);
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center p-8 text-center">
                <span class="material-symbols-outlined text-5xl text-red-500 mb-2">error</span>
                <p class="text-text-secondary-light dark:text-text-secondary-dark">Failed to load audio files</p>
            </div>
        `;
    }
}

/**
 * Handle audio selection for transcription
 */
async function handleAudioSelection(audioId, language, modal) {
    try {
        showLoading('Creating transcript...');
        modal.remove();

        const transcript = await transcriptAPI.create(audioId, language);
        showToast('Transcript created successfully!', 'success');

        // Add to state and re-render
        state.transcripts.unshift(transcript);
        filterTranscripts();
    } catch (error) {
        console.error('Failed to create transcript:', error);
        showToast(error.message || 'Failed to create transcript', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Format file size helper
 */
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format duration helper
 */
function formatDuration(seconds) {
    if (!seconds || seconds === 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Show generate summary modal
 */
function showGenerateSummaryModal(transcriptId) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white dark:bg-surface-dark rounded-xl max-w-md w-full p-6">
            <div class="flex justify-between items-start mb-6">
                <h3 class="text-xl font-bold text-text-primary-light dark:text-text-primary-dark">Generate Summary</h3>
                <button class="close-btn text-text-secondary-light dark:text-text-secondary-dark hover:text-primary">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-text-primary-light dark:text-text-primary-dark mb-2">AI Model</label>
                    <select
                        id="ai-model-select"
                        class="w-full rounded-lg border border-border-light dark:border-border-dark bg-surface-light dark:bg-surface-dark text-text-primary-light dark:text-text-primary-dark p-2 focus:border-primary focus:ring-primary"
                    >
                        <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet (Recommended)</option>
                        <option value="anthropic/claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                        <option value="openai/gpt-4-turbo">GPT-4 Turbo</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium text-text-primary-light dark:text-text-primary-dark mb-2">Custom Prompt (Optional)</label>
                    <textarea
                        id="custom-prompt-input"
                        rows="4"
                        class="w-full rounded-lg border border-border-light dark:border-border-dark bg-surface-light dark:bg-surface-dark text-text-primary-light dark:text-text-primary-dark p-2 focus:border-primary focus:ring-primary"
                        placeholder="Enter custom summarization instructions..."
                    ></textarea>
                </div>

                <div class="flex justify-end gap-3 mt-6">
                    <button class="cancel-btn px-4 py-2 bg-surface-light dark:bg-surface-dark border border-border-light dark:border-border-dark text-text-primary-light dark:text-text-primary-dark rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
                        Cancel
                    </button>
                    <button class="generate-btn px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                        Generate
                    </button>
                </div>
            </div>
        </div>
    `;

    // Event listeners
    modal.querySelector('.close-btn')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.cancel-btn')?.addEventListener('click', () => modal.remove());
    modal.querySelector('.generate-btn')?.addEventListener('click', async () => {
        const aiModel = document.getElementById('ai-model-select')?.value;
        const customPrompt = document.getElementById('custom-prompt-input')?.value.trim() || null;

        try {
            showLoading('Generating summary...');
            modal.remove();
            const summary = await summaryAPI.create(transcriptId, null, customPrompt, aiModel);
            showToast('Summary generated successfully!', 'success');

            // Redirect to summaries page
            setTimeout(() => {
                window.location.href = `/summaries-page?id=${summary.id}`;
            }, 1000);
        } catch (error) {
            console.error('Failed to generate summary:', error);
            showToast(error.message || 'Failed to generate summary', 'error');
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
 * Show options menu
 */
function showOptionsMenu(transcriptId, buttonElement) {
    const transcript = state.transcripts.find(t => t.id === transcriptId);
    if (!transcript) return;

    // Remove existing menu if any
    document.querySelectorAll('.options-menu').forEach(menu => menu.remove());

    const menu = document.createElement('div');
    menu.className = 'options-menu absolute bg-white dark:bg-surface-dark border border-border-light dark:border-border-dark rounded-lg shadow-lg z-50 py-2 min-w-[150px]';
    menu.innerHTML = `
        <button class="view-option w-full px-4 py-2 text-left text-sm text-text-primary-light dark:text-text-primary-dark hover:bg-gray-50 dark:hover:bg-gray-800">
            View Full Text
        </button>
        <button class="copy-option w-full px-4 py-2 text-left text-sm text-text-primary-light dark:text-text-primary-dark hover:bg-gray-50 dark:hover:bg-gray-800">
            Copy Text
        </button>
        <button class="delete-option w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">
            Delete
        </button>
    `;

    // Position menu near button
    const rect = buttonElement.getBoundingClientRect();
    menu.style.position = 'fixed';
    menu.style.top = `${rect.bottom + 5}px`;
    menu.style.right = `${window.innerWidth - rect.right}px`;

    // Event listeners
    menu.querySelector('.view-option')?.addEventListener('click', () => {
        menu.remove();
        viewTranscript(transcriptId);
    });

    menu.querySelector('.copy-option')?.addEventListener('click', async () => {
        menu.remove();
        const success = await copyToClipboard(transcript.text);
        if (success) showToast('Text copied to clipboard', 'success');
    });

    menu.querySelector('.delete-option')?.addEventListener('click', () => {
        menu.remove();
        handleDelete(transcriptId);
    });

    // Close menu when clicking outside
    setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
            if (!menu.contains(e.target) && e.target !== buttonElement) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 0);

    document.body.appendChild(menu);
}

/**
 * Handle transcript deletion
 */
function handleDelete(transcriptId) {
    showConfirmModal(
        'Are you sure you want to delete this transcript? This action cannot be undone.',
        async () => {
            try {
                showLoading('Deleting transcript...');
                await transcriptAPI.delete(transcriptId);
                showToast('Transcript deleted successfully', 'success');

                // Remove from state
                state.transcripts = state.transcripts.filter(t => t.id !== transcriptId);
                filterTranscripts();
            } catch (error) {
                console.error('Failed to delete transcript:', error);
                showToast('Failed to delete transcript', 'error');
            } finally {
                hideLoading();
            }
        }
    );
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
