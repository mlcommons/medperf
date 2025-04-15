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

document.addEventListener('DOMContentLoaded', function() {
    $('#hide-yaml').on('click', function(event){
        event.preventDefault();
        $('#yaml-panel').hide();
        $('#hide-yaml').hide();
    });
    $('.yaml-link').on('click', function(event) {
        console.log("YAML link clicked");
        console.log($(this));
        event.preventDefault();
        const entity = $(this).data('entity');
        const id = $(this).data('id');
        const field = $(this).data('field');
        $('#yaml-panel').show();
        $('.detail-container').addClass('yaml-panel-visible');
        $('#loading-indicator').show();
        $('#yaml-code').hide();
        $.get('/fetch-yaml', {entity: entity, entity_uid: id, field_to_fetch: field}, function(data) {
            $('#yaml-code').html(data.content);
            Prism.highlightElement($('#yaml-code')[0]);
            $('#loading-indicator').hide();
            $('#yaml-code').show();
            $('#hide-yaml').show();
        }).fail(function() {
            $('#yaml-code').text('Failed to load content');
            $('#loading-indicator').hide();
            $('#yaml-code').show();
            $('#hide-yaml').show();
        });
    });
});

// Floating alert notifications
function displayAlert(type, message) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show floating-alert`;
    alertContainer.setAttribute('role', 'alert');
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;
    document.body.appendChild(alertContainer);
}

// Clear all alerts
function clearAlerts() {
    document.querySelectorAll('.floating-alert').forEach(alert => alert.remove());
}
