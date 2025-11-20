document.addEventListener('DOMContentLoaded', function () {
        // Account menu toggle principal
        const accountMenuTrigger = document.getElementById('accountMenuTrigger');
        const accountMenu = document.getElementById('accountMenu');
        if (accountMenuTrigger && accountMenu) {
            accountMenuTrigger.addEventListener('click', function(e) {
                e.stopPropagation();
                accountMenu.style.display = accountMenu.style.display === 'none' || accountMenu.style.display === '' ? 'block' : 'none';
            });
            document.addEventListener('click', function(e) {
                if (!accountMenu.contains(e.target) && !accountMenuTrigger.contains(e.target)) {
                    accountMenu.style.display = 'none';
                }
            });
            // Fecha o menu ao clicar em qualquer link dentro do dropdown
            accountMenu.querySelectorAll('a').forEach(function(link) {
                link.addEventListener('click', function() {
                    accountMenu.style.display = 'none';
                });
            });
        }
    // DOM Elements
    const loginBtn = document.getElementById('loginBtn');
    const donateBtn = document.getElementById('donateBtn');
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');
    const closeModal = document.querySelectorAll('.close-modal');
    const showRegister = document.getElementById('showRegister');
    const showLogin = document.getElementById('showLogin');

    // Modal open buttons
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            loginModal.style.display = 'flex';
        });
    }

    if (donateBtn) {
        donateBtn.addEventListener('click', () => {
            loginModal.style.display = 'flex';
        });
    }

    // Close buttons
    closeModal.forEach(btn => {
        btn.addEventListener('click', () => {
            loginModal.style.display = 'none';
            registerModal.style.display = 'none';
        });
    });

    // Switch between login/register modals
    if (showRegister) {
        showRegister.addEventListener('click', (e) => {
            e.preventDefault();
            loginModal.style.display = 'none';
            registerModal.style.display = 'flex';
        });
    }

    if (showLogin) {
        showLogin.addEventListener('click', (e) => {
            e.preventDefault();
            registerModal.style.display = 'none';
            loginModal.style.display = 'flex';
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === loginModal) {
            loginModal.style.display = 'none';
        }
        if (e.target === registerModal) {
            registerModal.style.display = 'none';
        }
    });

    // Quantity buttons
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('quantity-btn')) {
            const item = e.target.getAttribute('data-item');
            const input = document.querySelector(`input[name="${item}"]`);
            let value = parseInt(input.value);

            if (e.target.textContent === '+') {
                value++;
            } else if (e.target.textContent === '-' && value > 0) {
                value--;
            }

            input.value = value;
        }
    });

    // Set minimum date for doação
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date();
        const minDate = new Date(today);
        minDate.setDate(today.getDate() + 2);

        const year = minDate.getFullYear();
        const month = String(minDate.getMonth() + 1).padStart(2, '0');
        const day = String(minDate.getDate()).padStart(2, '0');

        dateInput.min = `${year}-${month}-${day}`;
        dateInput.value = `${year}-${month}-${day}`;
    }
});
document.addEventListener('DOMContentLoaded', function () {
    // 1. Elementos do Modal e Botões (Corrigido para os IDs do seu HTML)
    
    // O modal único para Login/Registro no HTML é #authModal
    const modal = document.getElementById('authModal'); 

    // Botões que abrem o modal
    const loginBtn = document.getElementById('loginBtn');
    // CORREÇÃO APLICADA AQUI: Seu botão na Hero Section é 'registerCta', não 'donateBtn'
    const registerCta = document.getElementById('registerCta'); 

    // Botão(ões) para fechar o modal
    const closeModal = document.querySelectorAll('.close-modal');

    // 2. Elementos de Troca de Abas DENTRO do Modal
    const loginTabBtn = document.getElementById('loginTabBtn');
    const registerTabBtn = document.getElementById('registerTabBtn');
    const loginContent = document.getElementById('loginContent');
    const registerContent = document.getElementById('registerContent');
    const switchToLogin = document.querySelector('.switch-to-login');


    // FUNÇÃO PRINCIPAL PARA ABRIR O MODAL E MOSTRAR A ABA CORRETA
    // Recebe o ID da aba que deve ser ativada ('login' ou 'register')
    function openModal(defaultTab) {
        if (!modal) return; // Sai se o modal não existir (segurança)
        
        modal.style.display = 'flex'; // Torna o modal visível

        // Lógica para alternar a aba ativa (CSS class 'active')
        if (defaultTab === 'register') {
            loginTabBtn.classList.remove('active');
            registerTabBtn.classList.add('active');
            loginContent.classList.remove('active');
            registerContent.classList.add('active');
        } else { // Padrão: 'login'
            registerTabBtn.classList.remove('active');
            loginTabBtn.classList.add('active');
            registerContent.classList.remove('active');
            loginContent.classList.add('active');
        }
    }


    // 3. OUVINTES DE EVENTOS - ABRIR O MODAL
    if (loginBtn) {
        // Abre o modal na aba de login
        loginBtn.addEventListener('click', () => openModal('login'));
    }

    if (registerCta) {
        // Abre o modal na aba de registro (Quero Doar Agora)
        registerCta.addEventListener('click', () => openModal('register')); 
    }

    // OUVINTES DE EVENTOS - FECHAR O MODAL (o modal único)
    closeModal.forEach(btn => {
        btn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    });

    // Fecha o modal clicando fora
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // OUVINTES DE EVENTOS - TROCAR DE ABAS DENTRO DO MODAL
    if (loginTabBtn) {
        loginTabBtn.addEventListener('click', () => openModal('login'));
    }
    if (registerTabBtn) {
        registerTabBtn.addEventListener('click', () => openModal('register'));
    }
    if (switchToLogin) {
        switchToLogin.addEventListener('click', (e) => {
            e.preventDefault();
            openModal('login');
        });
    }

    // O restante do seu código (Quantity buttons e Set minimum date)
    // Quantity buttons and date handling are defined earlier to avoid duplicate listeners
});
/* byvinnyxp7 03/08/25 */

// Bloqueio de envio múltiplo do formulário de doação
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('donationForm');
    if (!form) return;

    let submitted = false;
    form.addEventListener('submit', function (e) {
        // Validate minimum items before allowing submission
        const required = parseInt(document.getElementById('requiredCount')?.textContent) || 3;
        const inputs = form.querySelectorAll('.quantity-input');
        let total = 0;
        inputs.forEach(function (inp) {
            const v = parseInt(inp.value) || 0;
            total += v;
        });

        const alertEl = document.getElementById('minItemsAlert');
        if (total < required) {
            e.preventDefault();
            // show animated alert
            if (alertEl) {
                alertEl.classList.remove('show');
                // force reflow to restart transition
                void alertEl.offsetWidth;
                alertEl.style.display = 'block';
                alertEl.classList.add('show');
                alertEl.classList.add('shake');
                setTimeout(function () { alertEl.classList.remove('shake'); }, 600);
                try { alertEl.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (err) {}
            }
            submitted = false;
            return;
        }

        if (submitted) {
            e.preventDefault();
            return;
        }
        submitted = true;

        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enviando...';
        }
    });
});
