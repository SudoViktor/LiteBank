export class LedgerService {
    constructor(apiClient) { this.api = apiClient; }
    async getBalance(iban) { return await this.api.request(`/balance?iban=${iban}`); }
}