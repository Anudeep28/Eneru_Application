// Function to toggle dropdown menu
function toggleDropdown() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('hidden');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const userMenu = document.getElementById('userMenu');
    const dropdown = document.getElementById('userDropdown');
    
    if (!userMenu.contains(event.target) && !dropdown.classList.contains('hidden')) {
        dropdown.classList.add('hidden');
    }
});
