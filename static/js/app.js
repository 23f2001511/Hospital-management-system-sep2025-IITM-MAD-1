/* ============================================================
   HMS Portal - Global App JS
   Dark mode, toasts, sidebar, tilt, count-up, reveal, typewriter
   ============================================================ */
(function () {
    'use strict';

    /* ===== Dark mode ===== */
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('hms_theme', theme);
        document.querySelectorAll('.dark-toggle-icon').forEach(function (el) {
            el.className = 'bi ' + (theme === 'dark' ? 'bi-sun-fill dark-toggle-icon' : 'bi-moon-stars-fill dark-toggle-icon');
        });
    }

    function initDarkMode() {
        var saved = localStorage.getItem('hms_theme');
        var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        applyTheme(saved || (prefersDark ? 'dark' : 'light'));
        document.querySelectorAll('.dark-toggle').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
                applyTheme(current);
            });
        });
    }

    /* ===== Toast notifications ===== */
    function showToast(message, category) {
        var stack = document.getElementById('toast-stack');
        if (!stack) {
            stack = document.createElement('div');
            stack.id = 'toast-stack';
            stack.className = 'toast-stack';
            document.body.appendChild(stack);
        }
        var icons = { success: 'bi-check-circle-fill', danger: 'bi-x-circle-fill', error: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill', red: 'bi-x-circle-fill' };
        var el = document.createElement('div');
        el.className = 'hms-toast toast-' + (category || 'info');
        el.innerHTML = '<span class="toast-icon"><i class="bi ' + (icons[category] || 'bi-info-circle-fill') + '"></i></span>'
            + '<span>' + (message || '') + '</span>'
            + '<span class="toast-close">&times;</span>';
        el.querySelector('.toast-close').addEventListener('click', function () { dismiss(el); });
        stack.appendChild(el);
        setTimeout(function () { dismiss(el); }, 5000);
    }

    function dismiss(el) {
        if (!el) return;
        el.classList.add('hide');
        setTimeout(function () { el.remove(); }, 300);
    }

    /* ===== Convert Flask flash messages to toasts ===== */
    function initFlashToasts() {
        document.querySelectorAll('[data-flash-message]').forEach(function (el) {
            showToast(el.getAttribute('data-flash-message'), el.getAttribute('data-flash-category') || 'info');
            el.remove();
        });
    }

    /* ===== Sidebar collapse (desktop) + mobile drawer ===== */
    function initSidebar() {
        var shell = document.querySelector('.app-shell');
        var toggle = document.querySelector('.sidebar-toggle-btn');
        var overlay = document.querySelector('.sidebar-overlay');
        var sidebar = document.querySelector('.sidebar');
        if (!shell || !sidebar) return;

        if (toggle) {
            toggle.addEventListener('click', function () {
                if (window.innerWidth < 992) {
                    sidebar.classList.toggle('open');
                    if (overlay) overlay.classList.toggle('show', sidebar.classList.contains('open'));
                } else {
                    shell.classList.toggle('sidebar-collapsed');
                    try { localStorage.setItem('hms_sidebar_collapsed', shell.classList.contains('sidebar-collapsed') ? '1' : '0'); } catch (e) {}
                }
            });
        }
        if (overlay) {
            overlay.addEventListener('click', function () {
                sidebar.classList.remove('open');
                overlay.classList.remove('show');
            });
        }

        try {
            if (localStorage.getItem('hms_sidebar_collapsed') === '1' && window.innerWidth >= 992) {
                shell.classList.add('sidebar-collapsed');
            }
        } catch (e) {}

        /* auto-highlight active nav link */
        var path = window.location.pathname;
        document.querySelectorAll('.sidebar .nav-link').forEach(function (link) {
            var href = link.getAttribute('href') || '';
            var item = link.closest('.nav-item');
            if (!item) return;
            if (path === '/' && href === '/') { item.classList.add('active'); return; }
            if (href !== '/' && href && path.indexOf(href) === 0) {
                item.classList.add('active');
            }
        });
    }

    /* ===== 3D tilt on hover ===== */
    function initTilt() {
        document.querySelectorAll('.tilt-card').forEach(function (card) {
            card.addEventListener('mousemove', function (e) {
                var rect = card.getBoundingClientRect();
                var x = (e.clientX - rect.left) / rect.width - 0.5;
                var y = (e.clientY - rect.top) / rect.height - 0.5;
                card.style.transform = 'perspective(800px) rotateX(' + (-y * 8) + 'deg) rotateY(' + (x * 8) + 'deg)';
                card.style.setProperty('--mx', (x * 100 + 50) + '%');
                card.style.setProperty('--my', (y * 100 + 50) + '%');
            });
            card.addEventListener('mouseleave', function () {
                card.style.transform = 'perspective(800px) rotateX(0) rotateY(0)';
            });
        });
    }

    /* ===== Count-up ===== */
    function animateCount(el) {
        var target = parseInt(el.getAttribute('data-count'), 10) || 0;
        if (el.getAttribute('data-counted') === '1') return;
        el.setAttribute('data-counted', '1');
        var duration = 1400, start = null;
        function step(ts) {
            if (!start) start = ts;
            var progress = Math.min((ts - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.floor(eased * target);
            if (progress < 1) requestAnimationFrame(step);
            else el.textContent = target;
        }
        requestAnimationFrame(step);
    }

    function initCountUp() {
        var els = document.querySelectorAll('[data-count]');
        if (!els.length) return;
        if ('IntersectionObserver' in window) {
            var obs = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) { animateCount(entry.target); obs.unobserve(entry.target); }
                });
            }, { threshold: 0.2 });
            els.forEach(function (el) { obs.observe(el); });
        } else {
            els.forEach(animateCount);
        }
    }

    /* ===== Scroll reveal ===== */
    function initReveal() {
        var els = document.querySelectorAll('.reveal');
        if (!els.length) return;
        if ('IntersectionObserver' in window) {
            var obs = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) { entry.target.classList.add('visible'); obs.unobserve(entry.target); }
                });
            }, { threshold: 0.1 });
            els.forEach(function (el) { obs.observe(el); });
        } else {
            els.forEach(function (el) { el.classList.add('visible'); });
        }
    }

    /* ===== Typewriter ===== */
    function initTypewriter() {
        document.querySelectorAll('.typewriter').forEach(function (el) {
            var words = (el.getAttribute('data-words') || el.textContent).split('|').filter(Boolean);
            if (!words.length) return;
            var wi = 0, ci = 0, deleting = false;
            el.textContent = '';
            function tick() {
                var word = words[wi];
                if (!deleting) {
                    el.textContent = word.substring(0, ci + 1); ci++;
                    if (ci === word.length) { deleting = true; setTimeout(tick, 1600); return; }
                    setTimeout(tick, 70);
                } else {
                    el.textContent = word.substring(0, ci - 1); ci--;
                    if (ci === 0) { deleting = false; wi = (wi + 1) % words.length; }
                    setTimeout(tick, 40);
                }
            }
            setTimeout(tick, 300);
        });
    }

    /* ===== Live notifications via SocketIO ===== */
    function initLiveNotifications() {
        if (typeof io === 'undefined') return;
        var socket = io();
        socket.on('notification', function () {
            var badge = document.getElementById('notifBadge');
            if (badge) {
                var n = parseInt(badge.textContent, 10) || 0;
                badge.style.display = 'flex';
                badge.textContent = n + 1;
            }
            var panel = document.getElementById('notifPanel');
            if (panel && panel.classList.contains('show')) loadNotifications();
        });
        socket.on('new_message', function () {
            var badge = document.getElementById('notifBadge');
            if (badge && badge.style.display !== 'flex') {
                var n = parseInt(badge.textContent, 10) || 0;
                badge.style.display = 'flex';
                badge.textContent = n + 1;
            }
        });
    }

    /* ===== Notification panel (global, overrides partial JS) ===== */
    function loadNotifications() {
        var list = document.getElementById('notifList');
        if (!list) return;
        fetch('/notifications?page=1&format=json', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.notifications || data.notifications.length === 0) {
                    list.innerHTML = '<div class="text-center text-muted py-4" style="font-size:.8rem;">No notifications yet</div>';
                    return;
                }
                var html = '';
                data.notifications.slice(0, 8).forEach(function (n) {
                    html += '<a href="' + (n.link || '#') + '" class="notif-item ' + (n.is_read ? '' : 'unread') + '">'
                        + '<span class="notif-icon"><i class="bi ' + (n.is_read ? 'bi-bell' : 'bi-bell-fill') + '"></i></span>'
                        + '<span style="flex:1;min-width:0;"><span class="notif-title d-block">' + n.title + '</span>'
                        + '<span class="notif-msg d-block">' + n.message + '</span>'
                        + '<span class="notif-time">' + (n.created_at || '') + '</span></span></a>';
                });
                list.innerHTML = html;
            })
            .catch(function () { list.innerHTML = '<div class="text-center text-muted py-4">Could not load</div>'; });
    }

    function updateUnreadCount() {
        var badge = document.getElementById('notifBadge');
        if (!badge) return;
        fetch('/notifications/unread_count')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.unread_count > 0) { badge.style.display = 'flex'; badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count; }
                else { badge.style.display = 'none'; }
            });
    }

    function initNotifBell() {
        var trigger = document.querySelector('.notif-trigger');
        var panel = document.getElementById('notifPanel');
        if (!trigger || !panel) return;
        trigger.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            var isOpen = panel.classList.contains('show');
            panel.classList.toggle('show', !isOpen);
            panel.style.display = isOpen ? 'none' : 'flex';
            if (!isOpen) loadNotifications();
        });
        document.addEventListener('click', function (e) {
            if (!panel.contains(e.target) && !trigger.contains(e.target)) {
                panel.classList.remove('show');
                panel.style.display = 'none';
            }
        });
    }

    /* ===== Glass navbar scroll (home) ===== */
    function initGlassNav() {
        var nav = document.querySelector('.glass-nav');
        if (!nav) return;
        window.addEventListener('scroll', function () {
            nav.classList.toggle('scrolled', window.scrollY > 40);
        });
    }

    /* ===== Auto-submit disabled state on forms ===== */
    function initSubmitButtons() {
        document.querySelectorAll('form').forEach(function (form) {
            var btn = form.querySelector('button[type="submit"].btn-submit-state');
            if (!btn) return;
            form.addEventListener('submit', function () {
                btn.disabled = true;
                var spin = btn.querySelector('.submit-spinner');
                if (spin) spin.style.display = 'inline-block';
                btn.setAttribute('data-original', btn.innerHTML);
            });
        });
    }

    /* ===== Init ===== */
    document.addEventListener('DOMContentLoaded', function () {
        initDarkMode();
        initFlashToasts();
        initSidebar();
        initTilt();
        initCountUp();
        initReveal();
        initTypewriter();
        initLiveNotifications();
        initNotifBell();
        updateUnreadCount();
        initGlassNav();
        initSubmitButtons();
    });

    window.hmsToast = showToast;
    window.showToast = showToast;
    window.hmsLoadNotifications = loadNotifications;
    window.hmsUpdateUnread = updateUnreadCount;
})();
