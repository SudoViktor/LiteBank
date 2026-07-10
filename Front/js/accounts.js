export class AccountsService {
    constructor(apiClient) { this.api = apiClient; }
    async getMyAccounts() { return await this.api.request('/my-accounts'); }
    async getCardsByIban(iban) { return await this.api.request(`/get-cards?iban=${iban}`); }
    async createAccount() { return await this.api.request('/create_account', 'POST'); }
    async createCard(iban) { return await this.api.request('/create_card', 'POST', { iban }); }
    async activateCard(cardId) { return await this.api.request(`/activate_card/${cardId}`, 'POST'); }
    async deactivateCard(cardId) { return await this.api.request(`/deactivate_card/${cardId}`, 'POST'); }
    async reissueCard(cardId) { return await this.api.request(`/reissue_card/${cardId}`, 'POST'); }
}