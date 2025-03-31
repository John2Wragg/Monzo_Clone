// Format currency amounts
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: 'GBP'
    }).format(amount);
}

// Show toast notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast show position-fixed bottom-0 end-0 m-3 text-white bg-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="toast-body">
            ${message}
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Input validation for currency amounts
document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        if (value < 0) {
            e.target.value = 0;
        }
    });
}); 