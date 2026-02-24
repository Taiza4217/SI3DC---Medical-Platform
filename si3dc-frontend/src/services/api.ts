/**
 * SI3DC — API Service Layer
 * 
 * Centralized HTTP client for all backend communication.
 * All API calls go through this module for consistency.
 */

const API_BASE = '/api';

// ── Auth helpers ─────────────────────────────────────────────────────

export function getStoredToken(): string | null {
    return localStorage.getItem('si3dc_token');
}

export function getStoredUser(): any | null {
    const raw = localStorage.getItem('si3dc_user');
    return raw ? JSON.parse(raw) : null;
}

export function clearAuth(): void {
    localStorage.removeItem('si3dc_token');
    localStorage.removeItem('si3dc_user');
}

function storeAuth(token: string, user: any): void {
    localStorage.setItem('si3dc_token', token);
    localStorage.setItem('si3dc_user', JSON.stringify(user));
}

function authHeaders(): Record<string, string> {
    const token = getStoredToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
            ...(options.headers || {}),
        },
    });
    return response;
}

// ── Auth Service ─────────────────────────────────────────────────────

export const authService = {
    async login(professionalId: string, password: string, healthNetwork: string) {
        const response = await apiFetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ professionalId, password, healthNetwork }),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Erro ao autenticar.');
        }
        storeAuth(data.token, data.user);
        return data;
    },

    logout() {
        clearAuth();
    },

    isAuthenticated(): boolean {
        return !!getStoredToken();
    },
};

// ── Patient Service ──────────────────────────────────────────────────

export const patientService = {
    async search(query: string) {
        const response = await apiFetch(`/patients/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro na busca.');
        return data.patients;
    },

    async getById(patientId: string) {
        const response = await apiFetch(`/patients/${patientId}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Paciente não encontrado.');
        return data;
    },
};

// ── Emergency Service ────────────────────────────────────────────────

export const emergencyService = {
    async getSummary(identifier: string) {
        const response = await apiFetch(`/emergency/summary?q=${encodeURIComponent(identifier)}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro no modo emergência.');
        return data;
    },
};

// ── Clinical Service ─────────────────────────────────────────────────

export const clinicalService = {
    async uploadDocument(file: File, patientName: string, documentType: string) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('patientName', patientName);
        formData.append('documentType', documentType);

        const token = getStoredToken();
        const response = await fetch(`${API_BASE}/clinical/upload`, {
            method: 'POST',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            body: formData,
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro no upload.');
        return data;
    },

    async saveNote(patientName: string, noteType: string, content: string) {
        const response = await apiFetch('/clinical/notes', {
            method: 'POST',
            body: JSON.stringify({ patientName, noteType, content }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro ao salvar nota.');
        return data;
    },
};

// ── Dashboard Service ────────────────────────────────────────────────

export const dashboardService = {
    async getStats() {
        const response = await apiFetch('/dashboard/stats');
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro ao carregar dashboard.');
        return data;
    },
    async startNext() {
        const response = await apiFetch('/dashboard/appointments/next', { method: 'POST' });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro ao iniciar próximo atendimento.');
        return data;
    },
    async endCurrent() {
        const response = await apiFetch('/dashboard/appointments/end', { method: 'POST' });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro ao encerrar atendimento.');
        return data;
    }
};

// ── Session / LGPD Service ───────────────────────────────────────────

export const sessionService = {
    async startAccess(patientId: string) {
        const response = await apiFetch('/session/access', {
            method: 'POST',
            body: JSON.stringify({ patientId, action: 'start' }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro ao iniciar sessão.');
        return data;
    },

    async endAccess(patientId: string) {
        const response = await apiFetch('/session/access', {
            method: 'POST',
            body: JSON.stringify({ patientId, action: 'end' }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro ao encerrar sessão.');
        return data;
    },
};
