// =====================================================================
// PORTFOLIO V2 JAVASCRIPT: COCKPIT INTERACTION
// =====================================================================

// Tab switching logic
function switchSection(sectionId) {
    // Hide all tab sections
    document.querySelectorAll('.tab-section').forEach(section => {
        section.style.display = 'none';
        section.classList.remove('active');
    });
    
    // Deactivate all navigation links
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(`sec-${sectionId}`);
    if (targetSection) {
        targetSection.style.display = 'flex';
        // Force reflow for transitions
        void targetSection.offsetWidth;
        targetSection.classList.add('active');
        
        // Use GSAP to animate entry nicely
        gsap.fromTo(targetSection, 
            { opacity: 0, y: 15 },
            { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' }
        );
    }
    
    // Activate target navigation button
    const targetBtn = document.getElementById(`btn-${sectionId}`);
    if (targetBtn) {
        targetBtn.classList.add('active');
    }
}

// Project Deck Filter System
function filterDeck(category) {
    // Update active state on filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Highlight the pressed button
    const eventTarget = window.event ? window.event.currentTarget : null;
    if (eventTarget) {
        eventTarget.classList.add('active');
    }
    
    const cards = document.querySelectorAll('.project-deck-card');
    
    // Animate card exits
    gsap.to(cards, {
        opacity: 0,
        scale: 0.95,
        duration: 0.25,
        stagger: 0.03,
        onComplete: () => {
            cards.forEach(card => {
                const cardCat = card.getAttribute('data-category');
                if (category === 'all' || cardCat === category) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Filter only visible cards for entrance animation
            const visibleCards = Array.from(cards).filter(c => c.style.display !== 'none');
            
            // Animate card entries
            gsap.fromTo(visibleCards, 
                { opacity: 0, scale: 0.95 },
                { opacity: 1, scale: 1, duration: 0.45, stagger: 0.05, ease: 'power2.out' }
            );
        }
    });
}

// --- OPTIMIZED PARTICLE BACKGROUND CONTROLLER ---
const canvas = document.getElementById('particles-bg');
const ctx = canvas.getContext('2d');

let particles = [];
const particleCount = 65;
let width = window.innerWidth;
let height = window.innerHeight;

// Mouse coordinates tracker for subtle attraction
const mouse = { x: null, y: null, radius: 140 };

window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
});

window.addEventListener('mouseleave', () => {
    mouse.x = null;
    mouse.y = null;
});

function resizeCanvas() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
}

window.addEventListener('resize', resizeCanvas);
resizeCanvas();

class Particle {
    constructor() {
        this.reset();
        this.y = Math.random() * height; // Distribute vertically at start
    }
    
    reset() {
        this.x = Math.random() * width;
        this.y = height + 10;
        this.size = Math.random() * 1.5 + 0.5;
        this.speedX = Math.random() * 0.4 - 0.2;
        this.speedY = -(Math.random() * 0.5 + 0.15); // Flow upwards
        this.opacity = Math.random() * 0.5 + 0.15;
    }
    
    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        
        // Interaction with mouse attraction
        if (mouse.x && mouse.y) {
            const dx = mouse.x - this.x;
            const dy = mouse.y - this.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < mouse.radius) {
                const force = (mouse.radius - dist) / mouse.radius;
                this.x += (dx / dist) * force * 0.8;
                this.y += (dy / dist) * force * 0.8;
            }
        }
        
        // Reset if particle moves out of viewport
        if (this.y < -10 || this.x < -10 || this.x > width + 10) {
            this.reset();
        }
    }
    
    draw() {
        ctx.fillStyle = `rgba(0, 240, 255, ${this.opacity})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

function initParticles() {
    particles = [];
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
}

function animateParticles() {
    ctx.clearRect(0, 0, width, height);
    
    particles.forEach(p => {
        p.update();
        p.draw();
    });
    
    requestAnimationFrame(animateParticles);
}

// Initialize on page load
function init() {
    initParticles();
    animateParticles();
    
    // Initial entrance animations
    gsap.from('.nav-bar', { y: -50, opacity: 0, duration: 1.0, ease: 'power3.out' });
    gsap.from('.profile-sidebar', { x: -50, opacity: 0, duration: 1.0, delay: 0.2, ease: 'power3.out' });
    gsap.from('.main-content-area', { x: 50, opacity: 0, duration: 1.0, delay: 0.2, ease: 'power3.out' });
}

window.onload = init;
