function create_p(msg){
    const p = $("<p></p>")
    p.text(msg)
    return p
}

function scrollToElement(selector){
    $("html, body").animate({
        scrollTop: $(selector).offset().top
    }, 1000);
}

// Recursively get events(logs, prompts, etc..)
function getEvents(logPanel, stagesList, currentStageElement) {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: "/events",
            type: "GET",
            dataType: "json",
            success: function(response) {
                if (response.task_id === window.runningTaskId){
                    if (response.end){
                        resolve(response);
                        return;
                    }
                }
                currentStageElement = handleEvents(response, logPanel, stagesList, currentStageElement);
                if(!window.isPromptReceived)
                    getEvents(logPanel, stagesList, currentStageElement).then(resolve).catch(reject);
            },
            error: function(xhr, status, error) {
                console.log("Error getEvents");
                console.log(xhr);
                console.log(status);
                console.log(error);
                reject(error);
            }
        });
    });
}

function processPreviousEvents(logPanel, stagesList, currentStageElement){
    if(window.previousEvents){
        window.previousEvents.forEach(event => {
            currentStageElement = handleEvents(event, logPanel, stagesList, currentStageElement);
        });
    }
    return currentStageElement;
}

// This function handles Events
function handleEvents(event, logPanel, stagesList, currentStageElement) {
    if (event.task_id !== window.runningTaskId){
        return currentStageElement;
    }
    // Clean the message from ANSI escape sequences
    var cleanMessage = event.message.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');
    if(event.interactive){
        if (event.type === 'text'){
            if (currentStageElement)
                markStageAsComplete(currentStageElement);
            
            currentStageElement = addNewStage(cleanMessage, stagesList);
        }
        else{
            appendToLogPanel(cleanMessage, logPanel);
        }

        return currentStageElement;
    }
    
    if(event.type === "yaml")
        cleanMessage = event.message;
    else
        cleanMessage = cleanMessage.replace("\n", "<br>");
    
    if(event.type === "print"){
        const p = create_p(cleanMessage);
        p.addClass("fw-bold")
        p.addClass("fs-5");
        $("#content").append(p);
        $("#text-content").show();
    }
    else if (event.type === "warning"){
        const p = create_p(cleanMessage);
        p.addClass("fw-bold")
        p.addClass("text-danger");
        p.addClass("fs-4");
        $("#content").append(p);
        $("#text-content").show();
        scrollToElement("#text-content")
    }
    else if (event.type === "error"){
        const p = create_p()
        p.addClass("font-weight-bold")
        p.addClass("text-danger");
        p.addClass("fs-4");
        p.html(cleanMessage);
        $("#content").append(p);
        $("#text-content").show();
        scrollToElement("#text-content")
    }
    else if (event.type === "highlight"){
        const p = create_p(cleanMessage);
        p.addClass("fs-4");
        $("#content").append(p);
        $("#text-content").show();
        scrollToElement("#text-content")
    }
    else if (event.type === "prompt"){
        const p = create_p(cleanMessage);
        p.addClass("mt-4");
        p.addClass("fs-4 text-danger fw-bold");
        $("#prompt-text").html(p);
        $("#prompt-container").show()
        scrollToElement("#prompt-container")
        window.isPromptReceived = true;
    }
    else if (event.type === "yaml"){
        // Display the YAML statistics in the <code> element
        $("#yaml-content").html(cleanMessage)
        // Show yaml container
        $("#yaml-container").show()
        // Apply Prism.js highlighting
        Prism.highlightElement(document.getElementById("yaml-content"));
        scrollToElement("#yaml-container")
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


function appendToLogPanel(message, logPanel) {
    // Appends log messages to the log panel
    logPanel.innerHTML += `${message}\n`;
    // Scroll to the bottom of the log panel to show the latest logs
    logPanel.scrollTop = logPanel.scrollHeight;
}
