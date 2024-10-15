// This function handles log messages, parsing and cleaning ANSI escape sequences.
function handleLogMessage(log, logPanel, stagesList, currentStageElement) {
    // Clean the message from ANSI escape sequences
    const cleanMessage = log.message.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');

    if (log.type === 'text') {
        // If it's a new stage, display it in bold and mark the previous stage as complete
        if (currentStageElement) {
            markStageAsComplete(currentStageElement);
        }
        currentStageElement = addNewStage(cleanMessage, stagesList);
    } else if (log.type === 'print') {
        // Append standard logs to the log panel
        appendToLogPanel(cleanMessage, logPanel);
    }
    return currentStageElement;
}

// Adds a new stage (text type message) to the stage tracker
function addNewStage(stageText, stagesList) {
    const listItem = document.createElement('li');
    listItem.className = 'list-group-item d-flex align-items-center';
    listItem.innerHTML = `
        <span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>
        <strong>${stageText}</strong>
    `;
    stagesList.appendChild(listItem);
    return listItem; // Return the newly added stage element for future reference
}

// Marks a stage as complete by replacing the spinner with a checkmark
function markStageAsComplete(stageElement) {
    if (!stageElement) {
        return;
    }
    const spinner = stageElement.querySelector('.spinner-border');
    if (spinner) {
        spinner.classList.remove('spinner-border', 'spinner-border-sm');
        spinner.classList.add('text-success', 'fas', 'fa-check-circle');
    }
}

// Appends log messages to the log panel
function appendToLogPanel(message, logPanel) {
    logPanel.innerHTML += `${message}\n`;
    logPanel.scrollTop = logPanel.scrollHeight;  // Scroll to the bottom to always show the latest logs
}
