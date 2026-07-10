export class AuthService {
    constructor(apiClient) { this.api = apiClient; }
    async login(username, password) {
        const response = await this.api.request('/login', 'POST', { username, password });
        if (response.access_token) {
            localStorage.setItem('access_token', response.access_token);
            localStorage.setItem('username', username);
        }
        return response;
    }
    async register(username, password) { return await this.api.request('/register', 'POST', { username, password }); }
    logout() { localStorage.removeItem('access_token'); localStorage.removeItem('username'); }
    isAuthenticated() { return !!localStorage.getItem('access_token'); }
}