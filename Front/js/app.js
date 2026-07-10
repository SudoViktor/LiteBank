import { ApiClient } from './api.js';
import { AuthService } from './auth.js';
import { AccountsService } from './accounts.js';
import { LedgerService } from './ledger.js';
import { TransactionsService } from './transactions.js'; // ДОДАНО
import { UIManager } from './ui.js';

const AUTH_API_URL = 'http://localhost:8002';      
const ACCOUNTS_API_URL = 'http://localhost:8001';  
const LEDGER_API_URL = 'http://localhost:8004';    
const TRANSACTIONS_API_URL = 'http://localhost:8000'; // ДОДАНО: Порт Transaction API

const apiAuth = new ApiClient(AUTH_API_URL);
const apiAccounts = new ApiClient(ACCOUNTS_API_URL);
const apiLedger = new ApiClient(LEDGER_API_URL);
const apiTransactions = new ApiClient(TRANSACTIONS_API_URL); // ДОДАНО

const authService = new AuthService(apiAuth);
const accountsService = new AccountsService(apiAccounts);
const ledgerService = new LedgerService(apiLedger);
const transactionsService = new TransactionsService(apiTransactions); // ДОДАНО
const ui = new UIManager();

document.addEventListener('DOMContentLoaded', () => {
    
    // --- ЗАВАНТАЖЕННЯ ДАШБОРДУ ---
    async function loadDashboard() {
        ui.setGreeting(localStorage.getItem('username'));
        ui.showDashboard();

        try {
            const response = await accountsService.getMyAccounts();
            ui.initAccounts(response.accounts); 
            
            // Завантажуємо дані для всіх рахунків
            for (const iban of response.accounts) {
                reloadAccountData(iban);
            }
        } catch (error) {
            console.error(error);
            if (error.message.includes("401") || error.message.includes("token")) {
                authService.logout(); ui.showAuth();
            }
        }
    }

    // Оновлена функція завантаження: тепер тягне ще й історію транзакцій
    async function reloadAccountData(iban) {
        // Робимо всі три запити паралельно для швидкості
        Promise.allSettled([
            ledgerService.getBalance(iban),
            accountsService.getCardsByIban(iban),
            transactionsService.getHistory(iban)
        ]).then(([balRes, cardsRes, histRes]) => {
            const dataToUpdate = {};
            if (balRes.status === 'fulfilled') dataToUpdate.balance = balRes.value.balance;
            if (cardsRes.status === 'fulfilled') dataToUpdate.cards = cardsRes.value.cards;
            if (histRes.status === 'fulfilled') dataToUpdate.transactions = histRes.value.transactions;
            
            ui.updateAccountData(iban, dataToUpdate);
        });
    }

    if (authService.isAuthenticated()) loadDashboard();

    // --- КЕРУВАННЯ КАРУСЕЛЛЮ ---
    let isAnimating = false;
    ui.prevBtn.addEventListener('click', async () => {
        if (isAnimating) return;
        isAnimating = true;
        await ui.prevSlide();
        setTimeout(() => isAnimating = false, 300); 
    });
    ui.nextBtn.addEventListener('click', async () => {
        if (isAnimating) return;
        isAnimating = true;
        await ui.nextSlide();
        setTimeout(() => isAnimating = false, 300);
    });

    // --- ДИНАМІЧНІ КЛІКИ ВСЕРЕДИНІ КАРУСЕЛІ ---
    document.getElementById('carousel-content').addEventListener('click', async (e) => {
        const accountCard = ui.accountsData[ui.currentIndex];
        
        // 1. Поповнити (Cash Deposit)
        if (e.target.closest('.action-topup')) {
            alert("⚠️ Зверніться до касира щоб покласти налічку.");
        }
        
        // 2. Переказати (P2P Transfer)
        if (e.target.closest('.action-send')) {
            if (!accountCard || !accountCard.iban) return;
            ui.openTransferModal(accountCard.iban);
        }

        // 3. Відкриття рахунку
        if (e.target.id === 'create-account-btn') {
            e.target.disabled = true; e.target.textContent = 'Відкриття...';
            try {
                await accountsService.createAccount();
                await loadDashboard(); 
            } catch(err) { alert(err.message); }
        }
        
        // 4. Випуск картки
        if (e.target.classList.contains('btn-issue-card')) {
            const iban = e.target.dataset.iban;
            e.target.disabled = true; e.target.textContent = 'Зачекайте...';
            try {
                await accountsService.createCard(iban);
                await reloadAccountData(iban);
            } catch(err) { alert(err.message); e.target.disabled = false; }
        }

        // 5. Відкриття налаштувань картки
        const cardElement = e.target.closest('.bank-card');
        if (cardElement && accountCard) {
            const card = accountCard.cards.find(c => c.id == cardElement.dataset.id);
            if (card) ui.openCardModal(card, accountCard.iban);
        }
    });

    // --- ВІДПРАВКА ФОРМИ ПЕРЕКАЗУ ---
    // --- ВІДПРАВКА ФОРМИ ПЕРЕКАЗУ ---
    document.getElementById('transfer-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fromIban = document.getElementById('transfer-from-iban').value;
        // Беремо значення, прибираємо пробіли і відразу робимо великими літерами (UA)
        const toIban = document.getElementById('transfer-to-iban').value.trim().toUpperCase(); 
        const amount = document.getElementById('transfer-amount').value;
        const submitBtn = document.getElementById('transfer-submit-btn');

        // 1. Перевірка: чи не переказує сам собі
        if (fromIban === toIban) {
            return ui.showTransferAlert("Ви не можете переказати гроші самі собі на той самий рахунок!");
        }

        // 2. СТРОГА ПЕРЕВІРКА IBAN (має починатися на UA і мати рівно 29 символів)
        if (!toIban.startsWith('UA') || toIban.length !== 29) {
            return ui.showTransferAlert("Некоректний IBAN. Він має починатися на 'UA' та містити рівно 29 символів без пробілів.");
        }

        ui.showTransferAlert('', 'hidden');
        submitBtn.disabled = true; 
        submitBtn.textContent = 'Обробка...';

        try {
            // Передаємо валідований IBAN на бекенд
            await transactionsService.createTransaction(fromIban, toIban, amount);
            ui.showTransferAlert("Переказ успішно створено! Очікуйте обробки.", "success");
            
            // Чекаємо 1.5 секунди, потім закриваємо
            setTimeout(() => {
                ui.closeTransferModal();
                reloadAccountData(fromIban); // Оновлюємо історію та баланс
            }, 1500);

        } catch (err) {
            ui.showTransferAlert(err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Відправити гроші';
        }
    });

    // --- ДИНАМІЧНІ КЛІКИ В МОДАЛЦІ КАРТКИ ---
    document.getElementById('card-modal-body').addEventListener('click', async (e) => {
        const btn = e.target;
        if(!btn.dataset.id) return;

        const cardId = btn.dataset.id;
        const iban = btn.dataset.iban;
        const originalText = btn.textContent;
        btn.disabled = true; btn.textContent = 'Обробка...';

        try {
            if (btn.classList.contains('btn-deactivate')) await accountsService.deactivateCard(cardId);
            if (btn.classList.contains('btn-activate')) await accountsService.activateCard(cardId);
            if (btn.classList.contains('btn-reissue')) await accountsService.reissueCard(cardId);
            
            await reloadAccountData(iban); 
            ui.closeModal(); 
        } catch(err) {
            alert(err.message);
            btn.disabled = false; btn.textContent = originalText;
        }
    });

    // --- АВТОРИЗАЦІЯ ---
    document.getElementById('auth-toggle-link')?.addEventListener('click', (e) => { e.preventDefault(); ui.toggleAuthMode(); });
    document.getElementById('auth-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();
        const submitBtn = document.getElementById('auth-submit-btn');

        if (!username || !password) return ui.showAlert('Заповніть всі поля.');
        
        ui.clearAlert(); 
        submitBtn.disabled = true;
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = 'Зачекайте...';

        try {
            if (ui.isLoginMode) {
                await authService.login(username, password);
                loadDashboard();
            } else {
                await authService.register(username, password);
                ui.showAlert('Реєстрація успішна! Увійдіть.', 'success');
                ui.toggleAuthMode();
                document.getElementById('username').value = username;
            }
        } catch (error) { 
            ui.showAlert(error.message); 
        } finally { 
            submitBtn.disabled = false; 
            submitBtn.textContent = originalBtnText;
        }
    });

    // Вихід
    document.getElementById('logout-btn')?.addEventListener('click', () => { authService.logout(); ui.showAuth(); });
});