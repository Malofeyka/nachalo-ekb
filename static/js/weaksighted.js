/* ========================================
   Образовательный центр «Начало»
   Версия для слабовидящих (weaksighted.js)
   ======================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    const weaksightedBtn = document.getElementById('weaksighted-btn');
    const weaksightedStyles = document.getElementById('weaksighted-styles');
    const STORAGE_KEY = 'weaksighted_mode_enabled';
    
    // --- Check saved preference ---
    const isWeaksightedEnabled = localStorage.getItem(STORAGE_KEY) === 'true';
    
    if (isWeaksightedEnabled) {
        enableWeaksightedMode();
    }
    
    // --- Toggle Button Handler ---
    if (weaksightedBtn) {
        weaksightedBtn.addEventListener('click', function() {
            const isEnabled = document.body.classList.contains('weaksighted-active');
            
            if (isEnabled) {
                disableWeaksightedMode();
            } else {
                enableWeaksightedMode();
            }
        });
    }
    
    // --- Enable WeakSighted Mode ---
    function enableWeaksightedMode() {
        document.body.classList.add('weaksighted-active');
        
        if (weaksightedStyles) {
            weaksightedStyles.disabled = false;
        }
        
        localStorage.setItem(STORAGE_KEY, 'true');
        
        // Update button aria-label
        if (weaksightedBtn) {
            weaksightedBtn.setAttribute('aria-label', 'Выключить версию для слабовидящих');
            weaksightedBtn.setAttribute('title', 'Выключить версию для слабовидящих');
        }
        
        // Announce change for screen readers
        announceChange('Версия для слабовидящих включена');
    }
    
    // --- Disable WeakSighted Mode ---
    function disableWeaksightedMode() {
        document.body.classList.remove('weaksighted-active');
        
        if (weaksightedStyles) {
            weaksightedStyles.disabled = true;
        }
        
        localStorage.setItem(STORAGE_KEY, 'false');
        
        // Update button aria-label
        if (weaksightedBtn) {
            weaksightedBtn.setAttribute('aria-label', 'Включить версию для слабовидящих');
            weaksightedBtn.setAttribute('title', 'Включить версию для слабовидящих');
        }
        
        // Announce change for screen readers
        announceChange('Версия для слабовидящих выключена');
    }
    
    // --- Announce Change for Screen Readers ---
    function announceChange(message) {
        let announcer = document.getElementById('weaksighted-announcer');
        
        if (!announcer) {
            announcer = document.createElement('div');
            announcer.id = 'weaksighted-announcer';
            announcer.setAttribute('role', 'status');
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            announcer.style.cssText = 'position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0;';
            document.body.appendChild(announcer);
        }
        
        announcer.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            announcer.textContent = '';
        }, 1000);
    }
    
    // --- Keyboard Shortcut (Alt + W) ---
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key === 'w') {
            e.preventDefault();
            const isEnabled = document.body.classList.contains('weaksighted-active');
            
            if (isEnabled) {
                disableWeaksightedMode();
            } else {
                enableWeaksightedMode();
            }
        }
    });
    
    // --- Increase/Decrease Font Size (Optional) ---
    // Can be added if needed for more granular control
    
});
