'use strict';

document.addEventListener('DOMContentLoaded', () => {

  //  CSRF TOKEN 
  function getCsrfToken() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
  }

  //  THEME MANAGEMENT 
  const html      = document.documentElement;
  const themeBtn  = document.getElementById('theme-toggle');
  const themeIcon = document.getElementById('theme-icon');

  function applyTheme(dark) {
    html.classList.toggle('dark', dark);
    if (themeIcon) {
      themeIcon.className = dark ? 'fas fa-sun text-base' : 'fas fa-moon text-base';
    }
  }

  const saved       = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved ? saved === 'dark' : prefersDark);

  themeBtn?.addEventListener('click', () => {
    const isDark = html.classList.contains('dark');
    applyTheme(!isDark);
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
    document.dispatchEvent(new CustomEvent('themeChanged', { detail: { dark: !isDark } }));
  });

  //  CURSOR GLOW — desktop only 
  const glow = document.getElementById('cursor-glow');
  if (glow && window.innerWidth > 768) {
    glow.style.opacity = '1';
    let rAF;
    window.addEventListener('mousemove', (e) => {
      cancelAnimationFrame(rAF);
      rAF = requestAnimationFrame(() => {
        glow.style.left = e.clientX + 'px';
        glow.style.top  = e.clientY + 'px';
      });
    }, { passive: true });
  }

  //  NAVBAR — scroll hide/show + scrolled state 
  const navbar  = document.getElementById('navbar');
  let   lastY   = 0;
  let   ticking = false;

  function handleScroll() {
    const y = window.scrollY;
    if (navbar) {
      navbar.classList.toggle('scrolled', y > 20);
      navbar.style.transform = (y > lastY && y > 100) ? 'translateY(-100%)' : 'translateY(0)';
    }
    lastY   = y;
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(handleScroll); ticking = true; }
  }, { passive: true });

  //  MOBILE MENU 
  const mobileBtn  = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');

  mobileBtn?.addEventListener('click', () => {
    const isOpen = !mobileMenu.classList.contains('hidden');
    mobileMenu.classList.toggle('hidden', isOpen);
    mobileBtn.setAttribute('aria-expanded', String(!isOpen));
    const icon = mobileBtn.querySelector('i');
    if (icon) icon.className = isOpen ? 'fas fa-bars text-base' : 'fas fa-times text-base';
  });

  document.addEventListener('click', (e) => {
    if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
      if (!mobileMenu.contains(e.target) && !mobileBtn?.contains(e.target)) {
        mobileMenu.classList.add('hidden');
        mobileBtn?.setAttribute('aria-expanded', 'false');
        const icon = mobileBtn?.querySelector('i');
        if (icon) icon.className = 'fas fa-bars text-base';
      }
    }
  });

  //  SKILL BAR ANIMATION 
  
  function animateBarsIn(container) {
    container.querySelectorAll('.skill-bar-fill').forEach((bar, i) => {
      // Stagger each bar slightly for a nicer cascade effect
      setTimeout(() => bar.classList.add('animated'), i * 80);
    });
  }

  // Stamp --bar-target on every bar and reset width to 0 so the
  // inline style from the template doesn't bypass our animation.
  document.querySelectorAll('.skill-bar-fill').forEach((bar) => {
    const pct = bar.style.width || '0%';
    bar.style.setProperty('--bar-target', pct);
    bar.style.width = '';          // clear inline width — CSS sets it to 0
  });

  //  SCROLL REVEAL (Intersection Observer) 
  
  const revealEls = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
  if (revealEls.length) {
    const revealObs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;

        const el = entry.target;
        el.classList.add('visible');

        // If this card contains skill bars, trigger them now.
        // Use a small delay so the card's own fade-in leads the bars.
        const delay = parseFloat(getComputedStyle(el).transitionDelay || '0') * 1000;
        setTimeout(() => animateBarsIn(el), delay + 120);

        revealObs.unobserve(el);
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    revealEls.forEach((el) => revealObs.observe(el));
  }

  // Animate bars in any cards that are already visible on page load
  // (e.g. cards above the fold that were never "revealed" by scroll).
  requestAnimationFrame(() => {
    document.querySelectorAll('.glass-card').forEach((card) => {
      const rect = card.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        animateBarsIn(card);
      }
    });
  });

  //  ANIMATED COUNTERS 
  function animateCounter(el) {
    const target   = parseFloat(el.dataset.target ?? el.textContent);
    const suffix   = el.dataset.suffix ?? '';
    const duration = 1800;
    const start    = performance.now();

    function update(now) {
      const p     = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      const value = target % 1 !== 0
        ? (eased * target).toFixed(1)
        : Math.floor(eased * target);
      el.textContent = value + suffix;
      if (p < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
  }

  const counterObs = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('[data-counter]').forEach((el) => counterObs.observe(el));

  //  MAGNETIC BUTTONS — desktop only 
  if (window.innerWidth > 768) {
    document.querySelectorAll('.magnetic-btn').forEach((btn) => {
      btn.addEventListener('mousemove', (e) => {
        const r  = btn.getBoundingClientRect();
        const dx = (e.clientX - (r.left + r.width  / 2)) * 0.22;
        const dy = (e.clientY - (r.top  + r.height / 2)) * 0.22;
        btn.style.transform = `translate(${dx}px, ${dy}px)`;
      });
      btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
    });
  }
  //  VANILLA TILT — project cards 
  if (typeof VanillaTilt !== 'undefined') {
    VanillaTilt.init(document.querySelectorAll('.tilt-card'), {
      max: 7, speed: 700, glare: true, 'max-glare': 0.07, perspective: 1000,
    });
  }

  //  PARTICLE BACKGROUND 
  const canvas = document.getElementById('particles-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let W, H, particles, animId;

    const isDarkNow = () => html.classList.contains('dark');

    function resize() {
      W = canvas.width  = canvas.offsetWidth;
      H = canvas.height = canvas.offsetHeight;
    }

    function createParticles(count = 55) {
      return Array.from({ length: count }, () => ({
        x:  Math.random() * W,
        y:  Math.random() * H,
        r:  Math.random() * 1.4 + 0.4,
        vx: (Math.random() - 0.5) * 0.28,
        vy: (Math.random() - 0.5) * 0.28,
      }));
    }

    function drawFrame() {
      ctx.clearRect(0, 0, W, H);
      const base = isDarkNow() ? '99,102,241,' : '79,70,229,';

      for (const p of particles) {
        p.x = (p.x + p.vx + W) % W;
        p.y = (p.y + p.vy + H) % H;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${base}0.5)`;
        ctx.fill();
      }

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const d  = dx * dx + dy * dy;
          if (d < 9000) {
            const dist = Math.sqrt(d);
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(${base}${0.12 * (1 - dist / 95)})`;
            ctx.lineWidth   = 0.5;
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(drawFrame);
    }

    resize();
    particles = createParticles();
    drawFrame();

    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resize, 200);
    }, { passive: true });

    document.addEventListener('visibilitychange', () => {
      document.hidden ? cancelAnimationFrame(animId) : drawFrame();
    });
  }

  //  TYPEWRITER EFFECT 
  const typeTarget = document.getElementById('typewriter');
  if (typeTarget) {
    const phrases = [
      'Full-Stack Engineer',
      'Django & React Builder',
      'AI/ML Practitioner',
      'Fintech Systems Architect',
      'Humanitarian Technologist',
    ];

    let phraseIdx  = 0;
    let charIdx    = 0;
    let isDeleting = false;
    let timer;

    function tick() {
      const phrase = phrases[phraseIdx % phrases.length];
      typeTarget.textContent = isDeleting
        ? phrase.slice(0, charIdx--)
        : phrase.slice(0, charIdx++);

      let delay = isDeleting ? 48 : 80;

      if (!isDeleting && charIdx > phrase.length) {
        isDeleting = true;
        delay = 2000;
      } else if (isDeleting && charIdx < 0) {
        isDeleting = false;
        charIdx = 0;
        phraseIdx++;
        delay = 350;
      }

      timer = setTimeout(tick, delay);
    }

    tick();
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) clearTimeout(timer); else tick();
    });
  }

  //  AI CHAT ASSISTANT 
  const chatBtn   = document.getElementById('ai-chat-btn');
  const chatModal = document.getElementById('ai-chat-modal');
  const closeChat = document.getElementById('close-chat');
  const chatInput = document.getElementById('chat-input');
  const sendBtn   = document.getElementById('send-message');
  const msgArea   = document.getElementById('chat-messages');

  function openChat() {
    if (!chatModal) return;
    chatModal.classList.remove('hidden');
    chatModal.classList.add('flex');
    chatInput?.focus();
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    if (!chatModal) return;
    chatModal.classList.add('hidden');
    chatModal.classList.remove('flex');
    document.body.style.overflow = '';
  }

  chatBtn?.addEventListener('click', () => {
    chatModal?.classList.contains('hidden') ? openChat() : closeModal();
  });

  closeChat?.addEventListener('click', closeModal);

  chatModal?.addEventListener('click', (e) => { if (e.target === chatModal) closeModal(); });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && chatModal && !chatModal.classList.contains('hidden')) closeModal();
  });

  function addMsg(content, isUser = false) {
    if (!msgArea) return;
    const div = document.createElement('div');
    div.className = isUser ? 'chat-bubble-user' : 'chat-bubble-ai';
    div.innerHTML = content;
    msgArea.appendChild(div);
    msgArea.scrollTop = msgArea.scrollHeight;
  }

  function showTyping() {
    if (!msgArea) return;
    const el = document.createElement('div');
    el.id = 'typing-indicator';
    el.className = 'typing-dots';
    el.innerHTML = '<span></span><span></span><span></span>';
    msgArea.appendChild(el);
    msgArea.scrollTop = msgArea.scrollHeight;
  }

  function removeTyping() { document.getElementById('typing-indicator')?.remove(); }

  async function sendMessage(text) {
    const msg = (text ?? chatInput?.value ?? '').trim();
    if (!msg) return;
    if (chatInput) chatInput.value = '';

    addMsg(escHtml(msg), true);
    showTyping();

    try {
      const res  = await fetch('/api/ai-chat/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body:    JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      removeTyping();
      addMsg(data.reply ?? 'Sorry, I could not respond right now.');
    } catch {
      removeTyping();
      addMsg('Connection issue — please try again in a moment.');
    }
  }

  sendBtn?.addEventListener('click', () => sendMessage());
  chatInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) sendMessage();
  });

  window.sendSuggest = (el) => {
    sendMessage(el.textContent.replace(/^[\u{1F000}-\u{1FFFF}]\s*/u, '').trim());
  };

  //  HTML ESCAPE UTILITY 
  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  //  PWA INSTALL PROMPT 
  let deferredPrompt;
  const installBtn = document.getElementById('pwa-install-btn');

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    installBtn?.classList.add('show');
  });

  installBtn?.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') installBtn.classList.remove('show');
    deferredPrompt = null;
  });

  window.addEventListener('appinstalled', () => installBtn?.classList.remove('show'));

  //  PAGE TRANSITION OVERLAY 
  const overlay = document.getElementById('page-transition');
  if (overlay) {
    overlay.style.opacity = '1';
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { overlay.style.opacity = '0'; });
    });

    document.querySelectorAll('a[href]').forEach((link) => {
      const href = link.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('http') ||
          href.startsWith('mailto') || href.startsWith('tel') ||
          link.hasAttribute('download') || link.target === '_blank') return;

      link.addEventListener('click', (e) => {
        e.preventDefault();
        overlay.style.opacity = '1';
        setTimeout(() => { window.location.href = href; }, 360);
      });
    });
  }

  //  GSAP ANIMATIONS — loaded after DOM 
  window.addEventListener('load', () => {
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

    gsap.registerPlugin(ScrollTrigger);

    const tl = gsap.timeline({ defaults: { ease: 'power3.out', duration: 0.7 } });

    const heroLabel = document.querySelector('.hero-label');
    const heroH1    = document.querySelector('h1.font-display');
    const heroSub   = document.querySelector('#typewriter')?.closest('p');
    const heroCopy  = document.querySelector('.hero-copy');
    const heroCtas  = document.querySelector('.hero-ctas');

    if (heroLabel) tl.from(heroLabel,                     { y: 18, opacity: 0 }, '+=0.1');
    if (heroH1)    tl.from(heroH1.querySelectorAll('span'), { y: 40, opacity: 0, stagger: 0.12 }, '-=0.4');
    if (heroSub)   tl.from(heroSub,                        { y: 24, opacity: 0 }, '-=0.4');
    if (heroCopy)  tl.from(heroCopy,                       { y: 20, opacity: 0 }, '-=0.35');
    if (heroCtas)  tl.from(heroCtas.children,              { y: 20, opacity: 0, stagger: 0.1 }, '-=0.3');

    document.querySelectorAll('.glass-card').forEach((card, i) => {
      if (card.closest('.reveal') || card.closest('.reveal-left') || card.closest('.reveal-right')) return;
      gsap.from(card, {
        y: 24, opacity: 0, duration: 0.65, ease: 'power3.out',
        delay: (i % 3) * 0.08,
        scrollTrigger: { trigger: card, start: 'top 88%', once: true },
      });
    });
  });

  //  ACTIVE NAV LINK HIGHLIGHTER 
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach((link) => {
    const href = link.getAttribute('href');
    if (href && currentPath === href) link.classList.add('nav-active');
  });

}); // end DOMContentLoaded