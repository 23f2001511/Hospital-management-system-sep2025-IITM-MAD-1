/* ============================================================
   HMS Portal - Global App JS (Phase 2)
   Dark mode, toast notifications, tilt cards, count-up, reveal
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
        var theme = saved || (prefersDark ? 'dark' : 'light');
        applyTheme(theme);
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
        var icons = { success: '✓', danger: '✕', error: '✕', warning: '!', info: 'ℹ', red: '✕' };
        var el = document.createElement('div');
        el.className = 'hms-toast toast-' + (category || 'info');
        el.innerHTML = '<span class="toast-icon">' + (icons[category] || 'ℹ') + '</span>'
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

    /* ===== Count-up animation ===== */
    function animateCount(el) {
        var target = parseInt(el.getAttribute('data-count'), 10) || 0;
        if (el.getAttribute('data-counted') === '1') return;
        el.setAttribute('data-counted', '1');
        var duration = 1400;
        var start = null;
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
                    if (entry.isIntersecting) {
                        animateCount(entry.target);
                        obs.unobserve(entry.target);
                    }
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
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        obs.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });
            els.forEach(function (el) { obs.observe(el); });
        } else {
            els.forEach(function (el) { el.classList.add('visible'); });
        }
    }

    /* ===== Typewriter effect ===== */
    function initTypewriter() {
        document.querySelectorAll('.typewriter').forEach(function (el) {
            var words = (el.getAttribute('data-words') || el.textContent).split('|').filter(Boolean);
            if (!words.length) return;
            var wi = 0, ci = 0, deleting = false;
            el.textContent = '';
            function tick() {
                var word = words[wi];
                if (!deleting) {
                    el.textContent = word.substring(0, ci + 1);
                    ci++;
                    if (ci === word.length) {
                        deleting = true;
                        setTimeout(tick, 1600);
                        return;
                    }
                    setTimeout(tick, 70);
                } else {
                    el.textContent = word.substring(0, ci - 1);
                    ci--;
                    if (ci === 0) {
                        deleting = false;
                        wi = (wi + 1) % words.length;
                    }
                    setTimeout(tick, 40);
                }
            }
            setTimeout(tick, 300);
        });
    }

    /* ===== SocketIO live notifications (bell) ===== */
    function initLiveNotifications() {
        if (typeof io === 'undefined' || !document.getElementById('notifBadge')) return;
        var socket = io();
        socket.on('notification', function () {
            var badge = document.getElementById('notifBadge');
            if (badge) {
                var n = parseInt(badge.textContent, 10) || 0;
                badge.style.display = 'inline';
                badge.textContent = n + 1;
            }
        });
    }

    /* ===== Glass navbar scroll ===== */
    function initGlassNav() {
        var nav = document.querySelector('.glass-nav');
        if (!nav) return;
        window.addEventListener('scroll', function () {
            nav.classList.toggle('scrolled', window.scrollY > 40);
        });
    }

    /* ===== Init on load ===== */
    document.addEventListener('DOMContentLoaded', function () {
        initDarkMode();
        initFlashToasts();
        initTilt();
        initCountUp();
        initReveal();
        initTypewriter();
        initLiveNotifications();
        initGlassNav();
    });

    /* Expose globally */
    window.hmsToast = showToast;
    window.showToast = showToast;
})();
