/**
 * API Client Module
 * Handles all REST API communication with the backend
 */

const API_BASE_URL = '/api';

/**
 * Base fetch wrapper with error handling
 */
async function apiFetch(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

/**
 * Video API
 */
export const videoAPI = {
    /**
     * Get all videos with optional filters
     */
    async getAll(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.status) queryParams.append('status', params.status);
        if (params.offset !== undefined) queryParams.append('offset', params.offset);
        if (params.limit !== undefined) queryParams.append('limit', params.limit || 100);

        const query = queryParams.toString();
        const result = await apiFetch(`/videos${query ? '?' + query : ''}`);
        // Backend returns { total, items }, return items array
        return result.items || [];
    },

    /**
     * Get video by ID
     */
    async getById(videoId) {
        return apiFetch(`/videos/${videoId}`);
    },

    /**
     * Upload video file
     */
    async upload(file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();

        return new Promise((resolve, reject) => {
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percent = (e.loaded / e.total) * 100;
                    onProgress(percent);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });

            xhr.addEventListener('error', () => reject(new Error('Upload failed')));
            xhr.addEventListener('abort', () => reject(new Error('Upload cancelled')));

            xhr.open('POST', `${API_BASE_URL}/videos/upload`);
            xhr.send(formData);
        });
    },

    /**
     * Download video from URL
     */
    async downloadFromUrl(url) {
        return apiFetch('/videos/download', {
            method: 'POST',
            body: JSON.stringify({ url }),
        });
    },

    /**
     * Delete video
     */
    async delete(videoId) {
        return apiFetch(`/videos/${videoId}`, {
            method: 'DELETE',
        });
    },
};

/**
 * Audio API
 */
export const audioAPI = {
    /**
     * Get all audios
     */
    async getAll(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.offset !== undefined) queryParams.append('offset', params.offset);
        if (params.limit !== undefined) queryParams.append('limit', params.limit || 100);

        const query = queryParams.toString();
        const result = await apiFetch(`/audios${query ? '?' + query : ''}`);
        return result.items || [];
    },

    /**
     * Get audio by ID
     */
    async getById(audioId) {
        return apiFetch(`/audios/${audioId}`);
    },

    /**
     * Extract audio from video
     */
    async extractFromVideo(videoId) {
        return apiFetch('/audios/extract', {
            method: 'POST',
            body: JSON.stringify({ video_id: videoId }),
        });
    },

    /**
     * Delete audio
     */
    async delete(audioId) {
        return apiFetch(`/audios/${audioId}`, {
            method: 'DELETE',
        });
    },
};

/**
 * Transcript API
 */
export const transcriptAPI = {
    /**
     * Get all transcripts
     */
    async getAll(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.language) queryParams.append('language', params.language);
        if (params.offset !== undefined) queryParams.append('offset', params.offset);
        if (params.limit !== undefined) queryParams.append('limit', params.limit || 100);

        const query = queryParams.toString();
        const result = await apiFetch(`/transcripts${query ? '?' + query : ''}`);
        return result.items || [];
    },

    /**
     * Get transcript by ID
     */
    async getById(transcriptId) {
        return apiFetch(`/transcripts/${transcriptId}`);
    },

    /**
     * Create transcript from audio
     */
    async create(audioId, language = 'ko') {
        return apiFetch('/transcripts/create', {
            method: 'POST',
            body: JSON.stringify({ audio_id: audioId, language }),
        });
    },

    /**
     * Delete transcript
     */
    async delete(transcriptId) {
        return apiFetch(`/transcripts/${transcriptId}`, {
            method: 'DELETE',
        });
    },
};

/**
 * Summary API
 */
export const summaryAPI = {
    /**
     * Get all summaries
     */
    async getAll(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.ai_model) queryParams.append('ai_model', params.ai_model);
        if (params.offset !== undefined) queryParams.append('offset', params.offset);
        if (params.limit !== undefined) queryParams.append('limit', params.limit || 100);

        const query = queryParams.toString();
        const result = await apiFetch(`/summaries${query ? '?' + query : ''}`);
        return result.items || [];
    },

    /**
     * Get summary by ID
     */
    async getById(summaryId) {
        return apiFetch(`/summaries/${summaryId}`);
    },

    /**
     * Create summary from transcript
     */
    async create(transcriptId, promptTemplateId = null, aiModel = 'anthropic/claude-3.5-sonnet') {
        const body = {
            transcript_id: transcriptId,
            ai_model_name: aiModel,
        };

        if (promptTemplateId) {
            body.prompt_template_id = promptTemplateId;
        }

        return apiFetch('/summaries/create', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },

    /**
     * Delete summary
     */
    async delete(summaryId) {
        return apiFetch(`/summaries/${summaryId}`, {
            method: 'DELETE',
        });
    },
};

/**
 * Prompt Template API
 */
export const templateAPI = {
    /**
     * Get all templates
     */
    async getAll(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.is_active !== undefined) queryParams.append('is_active', params.is_active);
        if (params.offset !== undefined) queryParams.append('offset', params.offset);
        if (params.limit !== undefined) queryParams.append('limit', params.limit || 100);

        const query = queryParams.toString();
        const result = await apiFetch(`/prompt-templates${query ? '?' + query : ''}`);
        return result.items || [];
    },

    /**
     * Get template by ID
     */
    async getById(templateId) {
        return apiFetch(`/prompt-templates/${templateId}`);
    },

    /**
     * Get template by name
     */
    async getByName(name) {
        return apiFetch(`/prompt-templates/name/${encodeURIComponent(name)}`);
    },

    /**
     * Create new template
     */
    async create(name, content, description = null, category = 'general') {
        return apiFetch('/prompt-templates', {
            method: 'POST',
            body: JSON.stringify({
                name,
                content,
                description,
                category,
                is_active: true,
            }),
        });
    },

    /**
     * Update template
     */
    async update(templateId, data) {
        return apiFetch(`/prompt-templates/${templateId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    /**
     * Delete template
     */
    async delete(templateId) {
        return apiFetch(`/prompt-templates/${templateId}`, {
            method: 'DELETE',
        });
    },

    /**
     * Toggle template active status
     */
    async toggleActive(templateId, isActive) {
        return apiFetch(`/prompt-templates/${templateId}/toggle?is_active=${isActive}`, {
            method: 'PATCH',
        });
    },
};

/**
 * Workflow API - Combined operations
 */
export const workflowAPI = {
    /**
     * Complete workflow: Upload video → Extract audio → Transcribe → Summarize
     */
    async processVideo(file, options = {}) {
        const {
            language = 'auto',
            promptTemplateId = null,
            customPrompt = null,
            aiModel = 'anthropic/claude-3.5-sonnet',
            onProgress = null,
        } = options;

        try {
            // Step 1: Upload video
            if (onProgress) onProgress({ step: 'upload', progress: 0 });
            const video = await videoAPI.upload(file, (percent) => {
                if (onProgress) onProgress({ step: 'upload', progress: percent });
            });
            if (onProgress) onProgress({ step: 'upload', progress: 100, data: video });

            // Step 2: Extract audio
            if (onProgress) onProgress({ step: 'audio', progress: 0 });
            const audio = await audioAPI.extractFromVideo(video.id);
            if (onProgress) onProgress({ step: 'audio', progress: 100, data: audio });

            // Step 3: Create transcript
            if (onProgress) onProgress({ step: 'transcript', progress: 0 });
            const transcript = await transcriptAPI.create(audio.id, language);
            if (onProgress) onProgress({ step: 'transcript', progress: 100, data: transcript });

            // Step 4: Create summary
            if (onProgress) onProgress({ step: 'summary', progress: 0 });
            const summary = await summaryAPI.create(
                transcript.id,
                promptTemplateId,
                customPrompt,
                aiModel
            );
            if (onProgress) onProgress({ step: 'summary', progress: 100, data: summary });

            return {
                video,
                audio,
                transcript,
                summary,
            };
        } catch (error) {
            if (onProgress) onProgress({ step: 'error', error });
            throw error;
        }
    },

    /**
     * Process from URL
     */
    async processFromUrl(url, options = {}) {
        const {
            language = 'auto',
            promptTemplateId = null,
            customPrompt = null,
            aiModel = 'anthropic/claude-3.5-sonnet',
            onProgress = null,
        } = options;

        try {
            // Step 1: Download video
            if (onProgress) onProgress({ step: 'download', progress: 0 });
            const video = await videoAPI.downloadFromUrl(url);
            if (onProgress) onProgress({ step: 'download', progress: 100, data: video });

            // Step 2: Extract audio
            if (onProgress) onProgress({ step: 'audio', progress: 0 });
            const audio = await audioAPI.extractFromVideo(video.id);
            if (onProgress) onProgress({ step: 'audio', progress: 100, data: audio });

            // Step 3: Create transcript
            if (onProgress) onProgress({ step: 'transcript', progress: 0 });
            const transcript = await transcriptAPI.create(audio.id, language);
            if (onProgress) onProgress({ step: 'transcript', progress: 100, data: transcript });

            // Step 4: Create summary
            if (onProgress) onProgress({ step: 'summary', progress: 0 });
            const summary = await summaryAPI.create(
                transcript.id,
                promptTemplateId,
                customPrompt,
                aiModel
            );
            if (onProgress) onProgress({ step: 'summary', progress: 100, data: summary });

            return {
                video,
                audio,
                transcript,
                summary,
            };
        } catch (error) {
            if (onProgress) onProgress({ step: 'error', error });
            throw error;
        }
    },
};

/**
 * Health check
 */
export const healthAPI = {
    async check() {
        return apiFetch('/health');
    },
};
