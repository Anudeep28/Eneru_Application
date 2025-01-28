// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.custom-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert) {
                dismissAlert(alert);
            }
        }, 5000);
    });
});

function dismissAlert(alert) {
    alert.classList.add('fade-out');
    setTimeout(() => {
        if (alert.parentElement) {
            alert.parentElement.removeChild(alert);
        }
    }, 500);
}
