// Initialize dropdown menus
document.addEventListener('DOMContentLoaded', function() {
    // Handle dropdown menus
    const dropdowns = document.querySelectorAll('.group');
    dropdowns.forEach(dropdown => {
        const button = dropdown.querySelector('button');
        const menu = dropdown.querySelector('.group-hover\\:block');
        
        // Show menu on hover
        dropdown.addEventListener('mouseenter', () => {
            menu.classList.remove('hidden');
        });
        
        // Hide menu when mouse leaves
        dropdown.addEventListener('mouseleave', () => {
            menu.classList.add('hidden');
        });
    });

    // Handle mobile menu
    const mobileMenuButton = document.querySelector('[data-mobile-menu]');
    const mobileMenu = document.querySelector('[data-mobile-menu-content]');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Handle flash messages auto-dismiss
    const flashMessages = document.querySelectorAll('.custom-alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
});

// Handle form submissions
document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.hasAttribute('data-confirm')) {
        const message = form.getAttribute('data-confirm') || 'Are you sure?';
        if (!confirm(message)) {
            e.preventDefault();
        }
    }
});

// Handle dynamic form validation
document.addEventListener('input', function(e) {
    if (e.target.hasAttribute('data-validate')) {
        validateField(e.target);
    }
});

function validateField(field) {
    const value = field.value;
    const type = field.getAttribute('data-validate');
    let isValid = true;
    let message = '';

    switch (type) {
        case 'email':
            isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
            message = 'Please enter a valid email address';
            break;
        case 'phone':
            isValid = /^\+?[\d\s-]{10,}$/.test(value);
            message = 'Please enter a valid phone number';
            break;
        case 'required':
            isValid = value.trim().length > 0;
            message = 'This field is required';
            break;
    }

    const errorElement = field.nextElementSibling;
    if (!isValid) {
        if (!errorElement || !errorElement.classList.contains('error-message')) {
            const error = document.createElement('div');
            error.className = 'error-message text-red-500 text-sm mt-1';
            error.textContent = message;
            field.parentNode.insertBefore(error, field.nextSibling);
        }
        field.classList.add('border-red-500');
    } else {
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.remove();
        }
        field.classList.remove('border-red-500');
    }

    return isValid;
}

// Handle dynamic content loading
function loadContent(url, targetId) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            document.getElementById(targetId).innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading content:', error);
        });
}