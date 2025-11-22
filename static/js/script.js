document.addEventListener('DOMContentLoaded', function () {
        // Account menu toggle principal
        const accountMenuTrigger = document.getElementById('accountMenuTrigger');
        const accountMenu = document.getElementById('accountMenu');
        if (accountMenuTrigger && accountMenu) {
            var __accountMenu_orig = { parent: null, nextSibling: null };

            function restoreAccountMenuToOriginalParent() {
                try {
                    if (__accountMenu_orig.parent) {
                        if (__accountMenu_orig.nextSibling && __accountMenu_orig.nextSibling.parentNode === __accountMenu_orig.parent) {
                            __accountMenu_orig.parent.insertBefore(accountMenu, __accountMenu_orig.nextSibling);
                        } else {
                            __accountMenu_orig.parent.appendChild(accountMenu);
                        }
                    }
                } catch (e) {}
            }

            function closeAccountMenu() {
                try {
                    accountMenu.style.display = 'none';
                    // remove mobile inline positioning applied by us
                    accountMenu.style.position = '';
                    accountMenu.style.top = '';
                    accountMenu.style.right = '';
                    accountMenu.style.left = '';
                    accountMenu.style.maxWidth = '';
                    accountMenu.style.minWidth = '';
                    accountMenu.style.maxHeight = '';
                    accountMenu.style.overflow = '';
                    accountMenu.style.zIndex = '';

                    // if we moved it to body, restore to original parent
                    if (document.body.contains(accountMenu) && __accountMenu_orig.parent && __accountMenu_orig.parent !== document.body) {
                        restoreAccountMenuToOriginalParent();
                    }
                } catch (err) { console.error('closeAccountMenu', err); }
            }

            accountMenuTrigger.addEventListener('click', function(e) {
                e.stopPropagation();
                var shouldOpen = accountMenu.style.display !== 'block';
                if (shouldOpen) {
                    // show menu
                    accountMenu.style.display = 'block';
                    try {
                        var w = window.innerWidth || document.documentElement.clientWidth;
                        if (w <= 420) {
                            // detach menu to body to avoid stacking-context issues
                            if (accountMenu.parentNode !== document.body) {
                                __accountMenu_orig.parent = accountMenu.parentNode;
                                __accountMenu_orig.nextSibling = accountMenu.nextSibling;
                                document.body.appendChild(accountMenu);
                            }

                            var header = document.querySelector('header');
                            var headerH = header ? Math.ceil(header.getBoundingClientRect().height) : 76;
                            accountMenu.style.position = 'fixed';
                            accountMenu.style.top = (headerH + 8) + 'px';
                            accountMenu.style.right = '12px';
                            accountMenu.style.left = 'auto';
                            accountMenu.style.maxWidth = '86vw';
                            accountMenu.style.minWidth = '180px';
                            accountMenu.style.maxHeight = (window.innerHeight - headerH - 24) + 'px';
                            accountMenu.style.overflow = 'auto';
                            accountMenu.style.zIndex = '99999';
                        }
                    } catch (err) { console.error('account menu position error', err); }
                } else {
                    // hide menu and cleanup
                    closeAccountMenu();
                }
            });

            document.addEventListener('click', function(e) {
                if (!accountMenu.contains(e.target) && !accountMenuTrigger.contains(e.target)) {
                    closeAccountMenu();
                }
            });

            // Fecha o menu ao clicar em qualquer link dentro do dropdown
            accountMenu.querySelectorAll('a').forEach(function(link) {
                link.addEventListener('click', function() {
                    closeAccountMenu();
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

// --- Enhancements: unsaved-modal guard, ESC handling, and page-exit animation ---
(function () {
    function hasUnsaved(modal) {
        if (!modal) return false;
        var inputs = modal.querySelectorAll('input, textarea, select');
        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            if (el.type === 'checkbox' || el.type === 'radio') {
                if (el.checked) return true;
            } else if (el.value && el.value.trim() !== '') {
                return true;
            }
        }
        return false;
    }

    function closeModalSafe(modal) {
        if (!modal) return;
        modal.style.display = 'none';
    }

    var modalIds = ['authModal', 'loginModal', 'registerModal'];
    modalIds.forEach(function (id) {
        var modal = document.getElementById(id);
        if (!modal) return;

        modal.addEventListener('click', function (ev) {
            if (ev.target !== modal) return; // only overlay clicks
            if (hasUnsaved(modal)) {
                var ok = confirm('Você tem alterações não salvas. Deseja descartar?');
                if (!ok) {
                    ev.stopPropagation();
                    return;
                }
            }
            closeModalSafe(modal);
        });
    });

    // ESC to close modal with confirmation on unsaved
    document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape') {
            for (var i = 0; i < modalIds.length; i++) {
                var m = document.getElementById(modalIds[i]);
                if (!m) continue;
                if (m.style.display === 'flex' || m.style.display === 'block') {
                    if (hasUnsaved(m)) {
                        if (!confirm('Você tem alterações não salvas. Fechar mesmo assim?')) return;
                    }
                    closeModalSafe(m);
                    return;
                }
            }
        }
    });

        // proteção de saída desativada para não atrapalhar login

   // Smooth page-exit for internal links
    document.addEventListener('click', function (ev) {
        var el = ev.target;
        var a = el.closest && el.closest('a');
        if (!a) return;
        var href = a.getAttribute('href');
        if (!href) return;
        if (href.indexOf('#') === 0) return;
        try {
            var url = new URL(href, window.location.href);
            if (url.origin !== window.location.origin) return;
            if (a.target && a.target !== '_self') return;
            if (url.pathname === window.location.pathname && url.search === window.location.search) return;
            // Intercept
            ev.preventDefault();
            document.body.classList.add('page-exit');
            setTimeout(function () { window.location.href = url.href; }, 260);
        } catch (e) {
            // ignore
        }
    }, true);
})();

// Global helper: show a persistent info panel under the header with a small X to close
window.showInfoPanel = function(id, title, text, options) {
    try {
        options = options || {};
        var exist = document.getElementById(id);
        if (exist) return exist;

        // ensure styles are present once
        if (!document.getElementById('__info_panel_styles')) {
            var style = document.createElement('style');
            style.id = '__info_panel_styles';
            style.textContent = '\n' +
            '.info-panel{position:fixed;left:50%;transform:translateX(-50%);top:72px;z-index:2147483647;max-width:92vw;width:760px;background:#f6fffa;border:1px solid rgba(76,175,80,0.18);box-shadow:0 8px 30px rgba(0,0,0,0.12);border-radius:10px;padding:12px 14px;display:flex;align-items:flex-start;gap:12px;font-family:inherit;color:#0b3a2b;}\n' +
            '.info-panel .info-panel-body{flex:1;white-space:pre-wrap;text-align:left;font-size:14px;line-height:1.5;}\n' +
            '.info-panel .info-panel-title{font-weight:700;color:var(--primary);margin-bottom:6px;display:block;font-size:15px;}\n' +
            '.info-panel-close{background:transparent;border:none;font-size:18px;line-height:1;cursor:pointer;color:#333;padding:6px 8px;border-radius:6px;}\n' +
            '@media (max-width:480px){.info-panel{top:64px;padding:10px;border-radius:8px;width:94vw;} .info-panel .info-panel-body{font-size:13px}}\n';
            document.head.appendChild(style);
        }

        var panel = document.createElement('div');
        panel.className = 'info-panel';
        panel.id = id;

        var body = document.createElement('div');
        body.className = 'info-panel-body';
        if (title) {
            var t = document.createElement('span');
            t.className = 'info-panel-title';
            t.textContent = title;
            body.appendChild(t);
        }
        var p = document.createElement('div');
        p.innerText = text || '';
        body.appendChild(p);

        var btn = document.createElement('button');
        btn.className = 'info-panel-close';
        btn.setAttribute('aria-label', 'Fechar');
        btn.innerHTML = '&times;';
        btn.addEventListener('click', function(){
            try { document.body.removeChild(panel); } catch(e){}
        });

        panel.appendChild(body);
        panel.appendChild(btn);

        document.body.appendChild(panel);

        // optional auto-hide
        if (options.autoHide && typeof options.autoHide === 'number') {
            setTimeout(function(){ try{ if (document.body.contains(panel)) document.body.removeChild(panel); }catch(e){} }, options.autoHide);
        }

        return panel;
    } catch (err) { console.error('showInfoPanel error', err); }
};
