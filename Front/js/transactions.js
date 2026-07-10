export class TransactionsService {
    constructor(apiClient) {
        this.api = apiClient;
        // Вкажи порт, на якому працює твій Transactions API (за замовчуванням 8000)
        this.api.baseUrl = 'http://localhost:8003'; 
    }

    async getHistory(iban) {
        return await this.api.request(`/history?iban=${iban}`);
    }

    async createTransaction(fromIban, toIban, amount) {
        return await this.api.request('/create_transaction', 'POST', {
            type: 'p2p',
            from_iban: fromIban,
            to_iban: toIban,
            amount: parseFloat(amount) // Передаємо дробом (напр. 15.50), бекенд сам зробить копійки
        });
    }
}