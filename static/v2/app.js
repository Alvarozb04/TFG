// =====================================================================
// PORTFOLIO V2 JAVASCRIPT: MAP-CENTRIC DASHBOARD LOGIC
// =====================================================================

// --- INTRO SCREEN TRANSITION SYSTEM ---
const introOverlay = document.getElementById('intro-overlay');
const introVideo = document.getElementById('intro-video');
const skipIntroBtn = document.getElementById('skip-intro-btn');
const portfolioViewport = document.getElementById('portfolio-viewport');

function transitionToPortfolio() {
    // Prevent duplicate triggers
    if (introOverlay.style.display === 'none') return;
    
    // Pause video to save CPU/resources
    introVideo.pause();
    
    // Fade out overlay
    gsap.to(introOverlay, {
        opacity: 0,
        duration: 0.8,
        ease: 'power2.inOut',
        onComplete: () => {
            introOverlay.style.display = 'none';
            
            // Reveal portfolio
            portfolioViewport.style.display = 'block';
            gsap.fromTo(portfolioViewport, 
                { opacity: 0 },
                { 
                    opacity: 1, 
                    duration: 1.0, 
                    ease: 'power2.out',
                    onComplete: triggerEntranceAnimations
                }
            );
        }
    });
}

// Bind intro termination events
if (introVideo) {
    introVideo.addEventListener('ended', () => {
        // Hold the final frame for 500ms before starting the fade-out transition
        setTimeout(transitionToPortfolio, 500);
    });
}
if (skipIntroBtn) {
    skipIntroBtn.addEventListener('click', transitionToPortfolio);
}

// Fallback in case autoplay is blocked or video fails to load
setTimeout(() => {
    if (introOverlay && introOverlay.style.display !== 'none') {
        // If still showing intro overlay after 12 seconds, auto skip
        transitionToPortfolio();
    }
}, 12000);


const regionNames = {
    'path-galicia': 'Galicia',
    'path-asturias': 'Principado de Asturias',
    'path-cantabria': 'Cantabria',
    'path-paisvasco': 'País Vasco',
    'path-navarra': 'Comunidad Foral de Navarra',
    'path-aragon': 'Aragón',
    'path-cataluna': 'Cataluña',
    'path-castillaleon': 'Castilla y León',
    'path-extremadura': 'Extremadura',
    'path-castillalamancha': 'Castilla-La Mancha',
    'path-valencia': 'Comunidad Valenciana',
    'path-andalucia': 'Andalucía',
    'path-baleares': 'Islas Baleares',
    'path-canarias': 'Islas Canarias',
    'path-rioja': 'La Rioja',
    'path-ceuta': 'Ceuta',
    'path-melilla': 'Melilla'
};

let activeGenericRegionId = null;

// --- REGIONAL DETAILS DRAWERS CONTROLLER ---
function openDrawer(region) {
    // Close other drawers first
    closeAllDrawers();
    
    // If it is a generic region (represented by its ID starting with 'path-')
    if (region.startsWith('path-')) {
        const name = regionNames[region];
        const titleEl = document.getElementById('generic-drawer-title');
        if (titleEl) titleEl.innerText = name;
        
        const drawer = document.getElementById('drawer-generic');
        if (drawer) {
            drawer.classList.add('open');
            activeGenericRegionId = region;
            
            // Highlight region path/polygon
            const path = document.getElementById(region);
            if (path) {
                path.style.fill = 'rgba(255, 255, 255, 0.15)';
                path.style.stroke = '#ffffff';
                path.style.strokeWidth = '2px';
            }
            
            // Stagger entrance of sections inside the drawer
            gsap.fromTo(drawer.querySelectorAll('.info-section'),
                { opacity: 0, x: 40 },
                { 
                    opacity: 1, 
                    x: 0, 
                    duration: 0.55, 
                    stagger: 0.08, 
                    ease: 'power2.out', 
                    delay: 0.25 
                }
            );
        }
        return;
    }
    
    // Hardcoded regions (madrid, murcia)
    const drawer = document.getElementById(`drawer-${region}`);
    if (drawer) {
        drawer.classList.add('open');
        
        // Stagger entrance of sections inside the drawer
        gsap.fromTo(drawer.querySelectorAll('.info-section'),
            { opacity: 0, x: 40 },
            { 
                opacity: 1, 
                x: 0, 
                duration: 0.55, 
                stagger: 0.08, 
                ease: 'power2.out', 
                delay: 0.25 
            }
        );
        
        // Highlight corresponding map path
        const path = document.getElementById(`path-${region}`);
        if (path) {
            path.style.fill = region === 'madrid' ? 'rgba(157, 78, 221, 0.18)' : 'rgba(0, 240, 255, 0.18)';
            path.style.strokeWidth = '2.5px';
        }
    }
}

function closeDrawer(region) {
    if (region === 'generic' || region.startsWith('path-')) {
        const drawer = document.getElementById('drawer-generic');
        if (drawer) {
            drawer.classList.remove('open');
            if (activeGenericRegionId) {
                const path = document.getElementById(activeGenericRegionId);
                if (path) {
                    path.style.fill = '';
                    path.style.stroke = '';
                    path.style.strokeWidth = '';
                }
                activeGenericRegionId = null;
            }
        }
        return;
    }
    
    const drawer = document.getElementById(`drawer-${region}`);
    if (drawer) {
        drawer.classList.remove('open');
        
        // Reset corresponding map path styling
        const path = document.getElementById(`path-${region}`);
        if (path) {
            path.style.fill = '';
            path.style.strokeWidth = '';
        }
    }
}

function closeAllDrawers() {
    closeDrawer('madrid');
    closeDrawer('murcia');
    closeDrawer('generic');
}

// Bind Close Buttons
document.querySelectorAll('.close-drawer-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const target = btn.getAttribute('data-target');
        closeDrawer(target);
        e.stopPropagation();
    });
});

// Click Outside Map regions to close Drawers
document.addEventListener('click', (e) => {
    const activeDrawer = document.querySelector('.drawer.open');
    if (activeDrawer) {
        const clickedInsideDrawer = activeDrawer.contains(e.target);
        const clickedActiveRegion = e.target.closest('#path-madrid') || 
                                     e.target.closest('#path-murcia') || 
                                     e.target.closest('.map-marker') ||
                                     (activeGenericRegionId && e.target.closest(`#${activeGenericRegionId}`));
                                     
        if (!clickedInsideDrawer && !clickedActiveRegion) {
            closeAllDrawers();
        }
    }
});

// ESC key to close Drawers
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAllDrawers();
    }
});

// Bind Map Paths and Interactions
function bindMapInteractions() {
    const pathMadrid = document.getElementById('path-madrid');
    const markerMadrid = document.getElementById('marker-madrid');
    const pathMurcia = document.getElementById('path-murcia');
    const markerMurcia = document.getElementById('marker-murcia');

    if (pathMadrid) pathMadrid.addEventListener('click', (e) => { openDrawer('madrid'); e.stopPropagation(); });
    if (markerMadrid) markerMadrid.addEventListener('click', (e) => { openDrawer('madrid'); e.stopPropagation(); });
    if (pathMurcia) pathMurcia.addEventListener('click', (e) => { openDrawer('murcia'); e.stopPropagation(); });
    if (markerMurcia) markerMurcia.addEventListener('click', (e) => { openDrawer('murcia'); e.stopPropagation(); });

    // Bind all generic communities to click events
    Object.keys(regionNames).forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('click', (e) => {
                openDrawer(id);
                e.stopPropagation();
            });
            el.style.cursor = 'pointer';
        }
    });
}


// --- ENTRANCE ANIMATIONS ---
function triggerEntranceAnimations() {
    // Map scale/fade in
    gsap.fromTo('.map-container', 
        { scale: 0.85, opacity: 0 }, 
        { scale: 1, opacity: 1, duration: 1.2, ease: 'power2.out' }
    );
    
    // Stagger marker scale-ups
    gsap.fromTo('.map-marker',
        { scale: 0, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.8, stagger: 0.2, delay: 0.4, ease: 'back.out(1.7)' }
    );
}


// --- OPTIMIZED PARTICLE BACKGROUND CONTROLLER ---
const canvas = document.getElementById('particles-bg');
const ctx = canvas.getContext('2d');

let particles = [];
const particleCount = 70;
let width = window.innerWidth;
let height = window.innerHeight;

const mouse = { x: null, y: null, radius: 150 };

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
        this.y = Math.random() * height; // Distribute vertically on initial load
    }
    
    reset() {
        this.x = Math.random() * width;
        this.y = height + 10;
        this.size = Math.random() * 1.5 + 0.5;
        this.speedX = Math.random() * 0.4 - 0.2;
        this.speedY = -(Math.random() * 0.5 + 0.15); // Upward drift
        this.opacity = Math.random() * 0.5 + 0.15;
    }
    
    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        
        // Mouse interactive drift
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
        
        // Reset off-screen particles
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


// --- INITIALIZE APPLICATION ---
function init() {
    initParticles();
    animateParticles();
    bindMapInteractions();
}

window.onload = init;
