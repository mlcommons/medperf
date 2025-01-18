function scroll(element_id){
    $("html, body").animate({
        scrollTop: $(`#${element_id}`).offset().top
    }, 1000);
}
function create_p(msg){
    const p = $("<p></p>")
    p.text(msg)
    return p
}
function getEvents(logPanel, stagesList, currentStageElement) { // Recursively get events(logs, prints, etc..)
    $.ajax({
        url: "/datasets/events",
        type: "GET",
        dataType: "json",
        success: function(response) {
            if (response.end)
                return;
            currentStageElement = handleEvents(response, logPanel, stagesList, currentStageElement);
            getEvents(logPanel, stagesList, currentStageElement);
        },
        error: function(xhr, status, error) {
            console.log("Error getEvents");
            console.log(xhr);
            console.log(status);
            console.log(error);
        }
    });
}

// This function handles Events
function handleEvents(log, logPanel, stagesList, currentStageElement) {
    // Clean the message from ANSI escape sequences
    var cleanMessage = log.message.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');
    if(log.interactive){
        if (log.type === 'text'){
            if (currentStageElement)
                markStageAsComplete(currentStageElement);
            
            currentStageElement = addNewStage(cleanMessage, stagesList);
        }
        else{
            appendToLogPanel(cleanMessage, logPanel);
        }

        return currentStageElement;
    }
    
    if(log.type === "yaml")
        cleanMessage = log.message;
    else
        cleanMessage = cleanMessage.replace("\n", "<br>");
    
    if(log.type === "print"){
        const p = create_p(cleanMessage);
        p.html(cleanMessage);
        $("#content").append(p);
        $("#text-content").show();
    }
    else if (log.type === "warning"){
        const p = create_p(cleanMessage);
        p.addClass("fw-bold")
        p.addClass("text-danger");
        p.addClass("fs-4");
        $("#content").append(p);
        $("#text-content").show();
        scroll("text-content");
    }
    else if (log.type === "error"){
        const p = create_p()
        p.addClass("font-weight-bold")
        p.addClass("text-danger");
        p.addClass("fs-4");
        p.html(cleanMessage);
        $("#content").append(p);
        $("#text-content").show();
        scroll("text-content");
    }
    else if (log.type === "highlight"){
        const p = create_p(cleanMessage);
        p.addClass("highlighted-text");
        p.addClass("fs-4");
        $("#content").append(p);
        $("#text-content").show();
        scroll("text-content");
    }
    else if (log.type === "prompt"){
        const p = create_p(cleanMessage);
        p.addClass("mt-4");
        p.addClass("fs-4 text-danger fw-bold");
        $("#prompt-text").html(p);
        $("#prompt-div").show()
        scroll("prompt-div");
    }
    else if (log.type === "yaml"){
        // Display the YAML statistics in the <code> element
        $("#yaml-content").html(cleanMessage)
        // Show yaml div
        $("#yaml-div").show()
        // Apply Prism.js highlighting
        Prism.highlightElement(document.getElementById("yaml-content"));
        scroll("yaml-div");
    }
    return currentStageElement;
}

// Adds a new stage (text type message) to the stage tracker
function addNewStage(stageText, stagesList) {
    const listItem = document.createElement('li');
    listItem.className = 'list-group-item d-flex align-items-center';
    listItem.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
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
