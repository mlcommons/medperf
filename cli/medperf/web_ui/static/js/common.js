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

function formatDates() {
    const createdAt = document.getElementById('created-at');
    const modifiedAt = document.getElementById('modified-at');
    if (createdAt && modifiedAt) {
        createdAt.textContent = formatDate(createdAt.textContent);
        modifiedAt.textContent = formatDate(modifiedAt.textContent);
    }
}
