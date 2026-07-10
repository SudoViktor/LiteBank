export class UIManager {
    constructor() {
        this.authView = document.getElementById('auth-view');
        this.dashboardView = document.getElementById('dashboard-view');
        this.alertBox = document.getElementById('alert-box');
        this.userGreeting = document.getElementById('user-greeting');
        
        // Елементи каруселі
        this.carouselContent = document.getElementById('carousel-content');
        this.carouselDots = document.getElementById('carousel-dots');
        this.prevBtn = document.getElementById('prev-slide');
        this.nextBtn = document.getElementById('next-slide');
        
        // Модалка карток
        this.cardModal = document.getElementById('card-modal');
        this.cardModalBody = document.getElementById('card-modal-body');
        document.getElementById('close-modal-btn').addEventListener('click', () => this.closeModal());

        // 🔥 ВИПРАВЛЕННЯ: Ініціалізуємо модалку переказу та активуємо хрестик
        this.transferModal = document.getElementById('transfer-modal');
        document.getElementById('close-transfer-btn').addEventListener('click', () => this.closeTransferModal());

        // Стан додатку
        this.accountsData = []; 
        this.currentIndex = 0;
        this.isLoginMode = true;
    }

    // --- Авторизація ---
    toggleAuthMode() {
        this.isLoginMode = !this.isLoginMode;
        this.clearAlert();
        document.getElementById('password').value = '';
        if (this.isLoginMode) {
            document.getElementById('auth-title').textContent = 'Вхід у LiteBank';
            document.getElementById('auth-submit-btn').textContent = 'Увійти';
            document.getElementById('auth-toggle-msg').textContent = 'Ще немає акаунту?';
            document.getElementById('auth-toggle-link').textContent = 'Зареєструватися';
        } else {
            document.getElementById('auth-title').textContent = 'Реєстрація';
            document.getElementById('auth-submit-btn').textContent = 'Створити акаунт';
            document.getElementById('auth-toggle-msg').textContent = 'Вже є акаунт?';
            document.getElementById('auth-toggle-link').textContent = 'Увійти';
        }
    }
    showAlert(msg, type = 'error') { this.alertBox.textContent = msg; this.alertBox.className = `alert ${type}`; }
    clearAlert() { this.alertBox.className = 'alert hidden'; }
    showDashboard() { this.authView.classList.replace('active', 'hidden'); this.dashboardView.classList.replace('hidden', 'active'); }
    showAuth() { this.dashboardView.classList.replace('active', 'hidden'); this.authView.classList.replace('hidden', 'active'); }
    setGreeting(username) { this.userGreeting.textContent = `Привіт, ${username}!`; }

    // --- Логіка Каруселі ---
    // ... твій попередній код конструктора та методів авторизації ...

    // --- Логіка Каруселі з Анімацією ---
    initAccounts(ibans) {
        // ДОДАНО: Тепер в стані є масив транзакцій
        this.accountsData = ibans.map(iban => ({ iban, balance: null, cards: [], transactions: [] }));
        this.currentIndex = 0;
        this.renderCarouselSlide();
    }

    updateAccountData(iban, data) {
        const idx = this.accountsData.findIndex(a => a.iban === iban);
        if (idx > -1) {
            if (data.balance !== undefined) this.accountsData[idx].balance = data.balance;
            if (data.cards !== undefined) this.accountsData[idx].cards = data.cards;
            if (data.transactions !== undefined) this.accountsData[idx].transactions = data.transactions;
            
            if (this.currentIndex === idx) {
                const inner = this.carouselContent.querySelector('.carousel-slide-inner');
                if (inner) this.renderSlideContent(inner);
            }
        }
    }

    // Гортання вперед (Слайд їде вліво)
    async nextSlide() {
        if (this.currentIndex < this.accountsData.length) {
            const inner = this.carouselContent.querySelector('.carousel-slide-inner');
            if (inner) {
                inner.classList.add('slide-out-left');
                await new Promise(r => setTimeout(r, 150)); // Чекаємо половину анімації вильоту
            }
            
            this.currentIndex++;
            this.renderCarouselSlide('left');
        }
    }

    // Гортання назад (Слайд їде вправо)
    async prevSlide() {
        if (this.currentIndex > 0) {
            const inner = this.carouselContent.querySelector('.carousel-slide-inner');
            if (inner) {
                inner.classList.add('slide-out-right');
                await new Promise(r => setTimeout(r, 150));
            }

            this.currentIndex--;
            this.renderCarouselSlide('right');
        }
    }

    renderDots() {
        this.carouselDots.innerHTML = '';
        for (let i = 0; i <= this.accountsData.length; i++) {
            const dot = document.createElement('span');
            dot.className = `dot ${i === this.currentIndex ? 'active' : ''}`;
            this.carouselDots.appendChild(dot);
        }
    }

    // Головний рендер слайду з підготовкою анімації заїзду
    renderCarouselSlide(direction = null) {
        this.renderDots();
        
        this.prevBtn.style.visibility = this.currentIndex === 0 ? 'hidden' : 'visible';
        this.nextBtn.style.visibility = this.currentIndex === this.accountsData.length ? 'hidden' : 'visible';

        // Створюємо внутрішню обгортку, яку будемо рухати
        const inner = document.createElement('div');
        inner.className = 'carousel-slide-inner';

        // Якщо прийшов напрямок — готуємо початкову позицію "за кадром"
        if (direction === 'left') inner.classList.add('slide-in-right');
        if (direction === 'right') inner.classList.add('slide-in-left');

        // Рендеримо логічний вміст
        this.renderSlideContent(inner);

        // Очищаємо карусель і додаємо новий елемент
        this.carouselContent.innerHTML = '';
        this.carouselContent.appendChild(inner);

        // Запускаємо заїзд у наступному кадрі анімації (через мінімальний таймаут)
        setTimeout(() => {
            inner.classList.remove('slide-in-right', 'slide-in-left');
        }, 20);
    }

    // Виніс вміст в окремий метод, щоб не дублювати код
    renderSlideContent(containerElement) {
        if (this.currentIndex === this.accountsData.length) {
            containerElement.innerHTML = `
                <div style="text-align:center; padding: 60px 0; display:flex; flex-direction:column; align-items:center;">
                    <div style="font-size: 48px; margin-bottom: 20px;">🏦</div>
                    <h2>Новий рахунок</h2>
                    <p class="text-muted" style="margin: 15px 0 30px;">Відкрийте новий рахунок для зручних розрахунків, зберігання коштів або P2P переказів.</p>
                    <button id="create-account-btn" class="btn-primary" style="padding: 16px 32px; font-size: 16px; border-radius: 30px;">+ Відкрити рахунок</button>
                </div>
            `;
            return;
        }

        const account = this.accountsData[this.currentIndex];
        const balanceFormatted = account.balance !== null 
            ? Number(account.balance).toLocaleString('uk-UA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
            : '...';

        let cardsHtml = '';
        if (account.cards && account.cards.length > 0) {
            account.cards.forEach(card => {
                const formattedNum = card.card_number.match(/.{1,4}/g).join(' ');
                const statusText = card.is_active ? 'Активна' : 'Заблокована';
                const statusColor = card.is_active ? '#2ecc71' : '#e74c3c';
                cardsHtml += `
                    <div class="bank-card" data-id="${card.id}">
                        <div class="card-number">${formattedNum}</div>
                        <div class="card-details">
                            <div>EXP<span>${card.expiration_date}</span></div>
                            <div>STATUS<span style="color:${statusColor}">${statusText}</span></div>
                        </div>
                        <div class="card-hint">Натисніть для налаштувань</div>
                    </div>
                `;
            });
        } else {
            cardsHtml = `<button class="btn-outline btn-issue-card" data-iban="${account.iban}" style="width:100%; padding: 25px; margin-bottom: 30px; border: 2px dashed #ccc; border-radius: 16px;">+ Випустити віртуальну картку</button>`;
        }

        // ФОРМУЄМО ДИНАМІЧНУ ІСТОРІЮ ТРАНЗАКЦІЙ
        let txHtml = '';
        if (account.transactions && account.transactions.length > 0) {
            // Робимо копію масиву і перевертаємо, щоб найновіші були зверху
            const reversedTx = [...account.transactions].reverse();
            
            reversedTx.forEach(tx => {
                // Сума в базі в копійках, тому ділимо на 100
                const amountFormatted = (Math.abs(tx.amount) / 100).toLocaleString('uk-UA', { minimumFractionDigits: 2 });
                const isPositive = tx.direction === 'in';
                const sign = isPositive ? '+' : '-';
                const amountClass = isPositive ? 'positive' : '';
                const title = isPositive ? `Від: ${tx.counterparty}` : `До: ${tx.counterparty}`;
                
                let statusIcon = '✅';
                if (tx.status === 'pending') statusIcon = '⏳';
                if (tx.status === 'cancel') statusIcon = '❌';

                txHtml += `
                    <div class="transaction-item">
                        <div class="tx-info">
                            <span class="tx-title">${statusIcon} ${title}</span>
                            <span class="tx-date">Транзакція #${tx.transaction_id}</span>
                        </div>
                        <span class="tx-amount ${amountClass}">${sign}${amountFormatted} ₴</span>
                    </div>
                `;
            });
        } else {
            txHtml = '<p class="text-muted" style="text-align: center; margin-top: 15px;">Транзакцій поки немає</p>';
        }

        containerElement.innerHTML = `
            <div class="account-header">
                <div class="account-title">Поточний рахунок</div>
                <div class="account-iban">${account.iban}</div>
                <div class="account-balance">${balanceFormatted} <span class="currency">UAH</span></div>
            </div>

            <div class="account-main-actions">
                <button class="action-btn action-topup">
                    <span style="font-size: 24px;">📥</span> Поповнити
                </button>
                <button class="action-btn action-send">
                    <span style="font-size: 24px;">💸</span> Переказати
                </button>
            </div>

            <div class="cards-container">
                ${cardsHtml}
            </div>

            <div class="transactions-section">
                <h4>Історія транзакцій</h4>
                ${txHtml}
            </div>
        `;
    }

    openTransferModal(iban) {
        document.getElementById('transfer-modal').classList.remove('hidden');
        document.getElementById('transfer-from-iban').value = iban;
        document.getElementById('transfer-from-display').value = iban;
        document.getElementById('transfer-to-iban').value = '';
        document.getElementById('transfer-amount').value = '';
        document.getElementById('transfer-alert').classList.add('hidden');
    }

    closeTransferModal() {
        document.getElementById('transfer-modal').classList.add('hidden');
    }

    showTransferAlert(msg, type = 'error') {
        const alertBox = document.getElementById('transfer-alert');
        alertBox.textContent = msg;
        alertBox.className = `alert ${type}`;
    }

    // ... Твій незмінний код модалки openCardModal, closeModal і т.д. ...

    // --- Модалка Картки ---
    openCardModal(card, iban) {
        this.cardModal.classList.remove('hidden');
        const formattedNum = card.card_number.match(/.{1,4}/g).join(' ');
        
        let actionsHtml = '';
        if (card.is_active) {
            actionsHtml += `<button class="btn-primary btn-deactivate" data-id="${card.id}" data-iban="${iban}" style="background-color: var(--error-color);">Заблокувати картку</button>`;
        } else {
            actionsHtml += `<button class="btn-primary btn-activate" data-id="${card.id}" data-iban="${iban}" style="background-color: var(--success-color);">Активувати картку</button>`;
        }
        actionsHtml += `<button class="btn-outline btn-reissue" data-id="${card.id}" data-iban="${iban}">Перевипустити картку</button>`;

        this.cardModalBody.innerHTML = `
            <div style="text-align: center; margin-bottom: 25px;">
                <p style="font-size: 13px; color:#888; margin-bottom: 8px;">Номер картки</p>
                <p style="font-family: monospace; font-size: 20px; letter-spacing: 2px;">${formattedNum}</p>
                <p style="font-size: 14px; font-weight: 600; margin-top: 10px; color: ${card.is_active ? '#2ecc71' : '#e74c3c'}">
                    ${card.is_active ? '● АКТИВНА' : '● ЗАБЛОКОВАНА'}
                </p>
            </div>
            <div class="modal-actions">
                ${actionsHtml}
            </div>
        `;
    }

    closeModal() {
        this.cardModal.classList.add('hidden');
    }
}