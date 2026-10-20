/* ========================================
   Образовательный центр «Начало»
   Основная логика (main.js)
   ======================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    // --- Mobile Menu Toggle ---
    const hamburger = document.querySelector('.hamburger');
    const headerNav = document.querySelector('.header-nav');
    
    if (hamburger && headerNav) {
        hamburger.addEventListener('click', function() {
            headerNav.classList.toggle('active');
            this.classList.toggle('active');
        });
        
        // Close menu on link click
        headerNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                headerNav.classList.remove('active');
                hamburger.classList.remove('active');
            });
        });
        
        // Close menu on outside click
        document.addEventListener('click', function(e) {
            if (!headerNav.contains(e.target) && !hamburger.contains(e.target)) {
                headerNav.classList.remove('active');
                hamburger.classList.remove('active');
            }
        });
    }
    
    // --- Smooth Scroll for Anchor Links ---
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.length > 1) {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // --- Modal Functionality ---
    const modalTriggers = document.querySelectorAll('[data-modal]');
    const modalClosers = document.querySelectorAll('[data-close-modal]');
    const modals = document.querySelectorAll('.modal');
    
    // Open modal
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.getAttribute('data-modal') + '-modal';
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
                
                // Focus first input
                const firstInput = modal.querySelector('input, select, textarea');
                if (firstInput) {
                    setTimeout(() => firstInput.focus(), 100);
                }
            }
        });
    });
    
    // Close modal
    modalClosers.forEach(closer => {
        closer.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });
    
    // Close modal on overlay click
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal-overlay')) {
                this.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            modals.forEach(modal => {
                modal.classList.remove('active');
            });
            document.body.style.overflow = '';
        }
    });
    
    // --- Header Scroll Effect ---
    const header = document.querySelector('.site-header');
    let lastScroll = 0;
    
    if (header) {
        window.addEventListener('scroll', function() {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll > 100) {
                header.style.boxShadow = '0 2px 10px rgba(0,0,0,0.15)';
            } else {
                header.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
            }
            
            lastScroll = currentScroll;
        });
    }
    
    // --- Phone Input Mask ---
    const phoneInputs = document.querySelectorAll('input[type="tel"]');

    function buildPhone(digits) {
        digits = digits.slice(0, 10);
        if (digits.length === 0) return '';
        let r = '+7 (' + digits.slice(0, 3);
        if (digits.length > 3) r += ') ' + digits.slice(3, 6);
        if (digits.length > 6) r += '-' + digits.slice(6, 8);
        if (digits.length > 8) r += '-' + digits.slice(8, 10);
        return r;
    }

    function extractDigits(val) {
        let d = val.replace(/\D/g, '');
        if (d.startsWith('7') || d.startsWith('8')) d = d.slice(1);
        return d.slice(0, 10);
    }

    phoneInputs.forEach(input => {
        input.addEventListener('keydown', function(e) {
            // Navigation / clipboard — не мешаем
            if (e.ctrlKey || e.metaKey) return;
            const nav = ['Tab','Escape','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'];
            if (nav.includes(e.key)) return;

            if (e.key === 'Backspace') {
                e.preventDefault();
                let digits = extractDigits(this.value);
                digits = digits.slice(0, -1);               // удаляем последнюю цифру
                this.value = digits.length ? buildPhone(digits) : '';
                this.setSelectionRange(this.value.length, this.value.length);
                return;
            }

            if (e.key === 'Delete') {
                e.preventDefault();
                this.value = '';
                return;
            }

            // Разрешаем только цифры
            if (!/^\d$/.test(e.key)) {
                e.preventDefault();
                return;
            }

            // Добавляем цифру
            e.preventDefault();
            let digits = extractDigits(this.value);
            if (digits.length >= 10) return;
            digits += e.key;
            this.value = buildPhone(digits);
            this.setSelectionRange(this.value.length, this.value.length);
        });

        // Обработка вставки через Ctrl+V / контекстное меню
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            const pasted = (e.clipboardData || window.clipboardData).getData('text');
            let digits = extractDigits(pasted);
            if (digits.length) {
                this.value = buildPhone(digits);
                this.setSelectionRange(this.value.length, this.value.length);
            }
        });

        input.addEventListener('focus', function() {
            if (!this.value) {
                this.value = '+7 (';
                this.setSelectionRange(this.value.length, this.value.length);
            }
        });

        input.addEventListener('blur', function() {
            if (this.value === '+7 (' || this.value === '+7') {
                this.value = '';
            }
        });
    });
    
    // --- Active Menu Item on Scroll ---
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.main-menu a');
    
    if (sections.length > 0 && navLinks.length > 0) {
        window.addEventListener('scroll', function() {
            let current = '';
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.clientHeight;
                
                if (pageYOffset >= sectionTop - 200) {
                    current = section.getAttribute('id');
                }
            });
            
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {
                    link.classList.add('active');
                }
            });
        });
    }
    
    // --- Form Validation ---
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });
            
            // Phone validation
            const phoneField = form.querySelector('input[type="tel"]');
            if (phoneField && phoneField.value.replace(/\D/g, '').length < 10) {
                isValid = false;
                phoneField.classList.add('error');
            }
            
            if (!isValid) {
                e.preventDefault();
                showFormError(form, 'Пожалуйста, заполните все обязательные поля');
            }
        });
    });
    
    function showFormError(form, message) {
        // Remove existing error messages
        const existingError = form.querySelector('.form-error-message');
        if (existingError) {
            existingError.remove();
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error-message';
        errorDiv.style.cssText = 'color: #d32f2f; font-size: 0.9rem; margin-bottom: 16px; padding: 12px; background: #ffebee; border-radius: 4px;';
        errorDiv.textContent = message;
        
        form.insertBefore(errorDiv, form.firstChild);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
    
    // --- Lazy Loading Images ---
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    observer.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // --- Console Welcome Message ---
    console.log('%cОбразовательный центр «Начало»', 'color: #2E7D32; font-size: 20px; font-weight: bold;');
    console.log('%cЕкатеринбург — развитие детей от 5 до 16 лет', 'color: #757575; font-size: 14px;');
    console.log('%cТелефон: +7 (XXX) XXX-XX-XX', 'color: #757575; font-size: 14px;');
});

// --- Yandex Map Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    const mapElement = document.getElementById('map');
    if (mapElement && typeof ymaps !== 'undefined') {
        ymaps.ready(function () {
            const address = mapElement.getAttribute('data-address') || 'Екатеринбург';
            ymaps.geocode(address).then(function (res) {
                const firstGeoObject = res.geoObjects.get(0);
                let coords = [56.786523, 60.536968];
                if (firstGeoObject) {
                    coords = firstGeoObject.geometry.getCoordinates();
                }
                const myMap = new ymaps.Map('map', {
                    center: coords,
                    zoom: 16,
                    controls: ['zoomControl', 'fullscreenControl']
                });
                const myPlacemark = new ymaps.Placemark(coords, {
                    balloonContent: 'Образовательный центр «Начало»',
                    hintContent: address
                }, {
                    preset: 'islands#blueEducationIcon'
                });
                myMap.geoObjects.add(myPlacemark);
                myMap.behaviors.disable('scrollZoom');
            }).catch(function(e) {
                console.error('Geocode error:', e);
            });
        });
    }
});

// --- Autumn Camp Modal Auto-show & Falling Leaves ---
document.addEventListener('DOMContentLoaded', function() {
    const summerModal = document.getElementById('summer-camp-modal');
    const leavesContainer = document.getElementById('falling-leaves');

    function createFallingLeaves(container) {
        if (!container || container.children.length > 0) return;
        const leafSymbols = ['🍁', '🍂', '🍁', '🍂'];
        const colors = ['#E65100', '#D84315', '#BF360C', '#FF8F00', '#FFB300'];
        const count = 18;

        for (let i = 0; i < count; i++) {
            const leaf = document.createElement('span');
            leaf.className = 'falling-leaf';
            leaf.textContent = leafSymbols[Math.floor(Math.random() * leafSymbols.length)];

            const left = Math.random() * 90 + 3; // 3% to 93%
            const duration = Math.random() * 4 + 4.5; // 4.5s to 8.5s
            const delay = Math.random() * 4.5; // 0s to 4.5s
            const size = Math.random() * 14 + 14; // 14px to 28px
            const color = colors[Math.floor(Math.random() * colors.length)];

            leaf.style.left = left + '%';
            leaf.style.animationDuration = duration + 's';
            leaf.style.animationDelay = delay + 's';
            leaf.style.fontSize = size + 'px';
            leaf.style.color = color;

            container.appendChild(leaf);
        }
    }

    if (summerModal) {
        // Create leaves whenever modal opens
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    if (summerModal.classList.contains('active')) {
                        createFallingLeaves(leavesContainer);
                    }
                }
            });
        });
        observer.observe(summerModal, { attributes: true });

        // Auto-show popup on page load
        if (!sessionStorage.getItem('autumnCampBannerShown')) {
            setTimeout(function() {
                summerModal.classList.add('active');
                document.body.style.overflow = 'hidden';
                sessionStorage.setItem('autumnCampBannerShown', 'true');
                createFallingLeaves(leavesContainer);
            }, 1500); // Показываем через 1.5 секунды
        }
    }
});
