function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const options = {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
    };
    if (date.getFullYear() !== now.getFullYear()) {
        options.year = 'numeric';
    }
    return date.toLocaleDateString(undefined, options);
}

function applyDateFormatting() {
    console.log("Date formatter started");
    const dateElements = document.querySelectorAll('[data-date]');
    dateElements.forEach(element => {
        const date = element.getAttribute('data-date');
        element.textContent = formatDate(date);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    applyDateFormatting();
});
