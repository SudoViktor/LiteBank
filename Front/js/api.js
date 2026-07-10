export class ApiClient {
    constructor(baseUrl) { this.baseUrl = baseUrl; }
    async request(endpoint, method = 'GET', body = null) {
        const headers = { 'Content-Type': 'application/json' };
        const token = localStorage.getItem('access_token');
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const config = { method, headers };
        if (body) config.body = JSON.stringify(body);
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, config);
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Сталася невідома помилка');
            return data;
        } catch (error) { throw error; }
    }
}