// ─── Navbar scroll effect ────────────────────────────────
const navbar = document.getElementById('navbar');
let lastScroll = 0;

window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;
    if (currentScroll > 60) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    lastScroll = currentScroll;
});

// Trigger on page load
if (window.scrollY > 60) navbar.classList.add('scrolled');

// ─── Mobile nav toggle ──────────────────────────────────
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');

if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
        navLinks.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
        if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
            navLinks.classList.remove('open');
        }
    });
}

// ─── Auto-dismiss flash messages ─────────────────────────
document.querySelectorAll('.flash-message').forEach(msg => {
    setTimeout(() => {
        msg.style.opacity = '0';
        msg.style.transform = 'translateX(30px)';
        setTimeout(() => msg.remove(), 300);
    }, 5000);
});

// ─── Smooth scroll for anchor links ──────────────────────
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// ─── Intersection Observer for scroll animations ─────────
const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.location-card, .category-card, .vision-card, .tip-card, .why-feature').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

document.head.insertAdjacentHTML('beforeend', `
<style>
.animate-in {
    opacity: 1 !important;
    transform: translateY(0) !important;
}
</style>`);
