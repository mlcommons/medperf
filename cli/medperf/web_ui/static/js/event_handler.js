function create_p(msg){
    const p = $("<p></p>");
    p.html(msg);
    return p;
}

function scrollToElement(selector){
    // .stop(true) to avoid scroll lagging during multiple scrolls
    $("html, body").stop(true).animate({
        scrollTop: $(selector).offset().top
    }, 1000);
}

function streamEvents(logPanel, stagesList, currentStageElement, streamOld) {
    const url = streamOld === true ? `/events?stream_old=true` : `/events`; 
    const eventSource = new EventSource(url);
    window.evSource = eventSource;

    eventSource.onmessage = function (event) {
        const data = JSON.parse(event.data);

        // Only process events from current task
        if (data.task_id !== window.runningTaskId)
            return;

        // If task ended, close the stream
        if (data.end) {
            eventSource.close();
            window.evSource = null;
            if (typeof window.onPromptComplete === "function") {
                window.onPromptComplete(data.response);
            }
            return;
        }

        currentStageElement = handleEvents(data, logPanel, stagesList, currentStageElement);

        if(window.isPromptReceived){
            eventSource.close();
            window.evSource = null;
        }
    };

    eventSource.onerror = function (err) {
        console.error("EventSource failed:", err);
        eventSource.close();
        window.evSource = null;
    };
}

function cleanMsg(message){
    return message.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');
}

// This function handles Events
function handleEvents(event, logPanel, stagesList, currentStageElement) {
    if(event.kind === "chunk"){
        const lines = [];
        for(const ev of event.events){
            lines.push(cleanMsg(ev.message))
        }
        appendManyToLogPanel(lines, logPanel);
        return currentStageElement;
    }
    // Clean the message from ANSI escape sequences
    var cleanMessage = cleanMsg(event.message);
    if(event.interactive){
        if (event.type === 'text'){
            if (currentStageElement)
                markStageAsComplete(currentStageElement);
            
            currentStageElement = addNewStage(cleanMessage, stagesList);
            return currentStageElement;
        }
        else if (event.type === 'print'){
            appendToLogPanel(cleanMessage, logPanel);
            return currentStageElement;
        }        
    }

    if(event.type === "yaml")
        cleanMessage = event.message;
    else
        cleanMessage = cleanMessage.replace("\n", "<br>");
    
    if(event.type === "print"){
        const p = create_p(cleanMessage);
        p.addClass("fw-bold");
        p.addClass("fs-5");
        $("#content").append(p);
        $("#text-content").show();
    }
    else if (event.type === "warning"){
        const p = create_p(cleanMessage);
        p.addClass("fw-bold");
        p.addClass("text-danger");
        p.addClass("fs-4");
        $("#content").append(p);
        $("#text-content").show();
        scrollToElement("#text-content");
    }
    else if (event.type === "error"){
        const p = create_p();
        p.addClass("font-weight-bold");
        p.addClass("text-danger");
        p.addClass("fs-4");
        p.html(cleanMessage);
        $("#content").append(p);
        $("#text-content").show();
        scrollToElement("#text-content");
    }
    else if (event.type === "highlight"){
        const p = create_p(cleanMessage);
        p.addClass("fs-4");
        $("#content").append(p);
        $("#text-content").show();
        scrollToElement("#text-content");
    }
    else if (event.type === "prompt"){
        const p = create_p(cleanMessage);
        p.addClass("mt-4");
        p.addClass("fs-4 text-danger fw-bold");
        $("#prompt-text").html(p);
        $("#prompt-container").show();
        scrollToElement("#prompt-container");
        window.isPromptReceived = true;
    }
    else if (event.type === "yaml"){
        // Display the YAML statistics in the <code> element
        $("#yaml-content").html(cleanMessage);
        // Show yaml container
        $("#yaml-container").show();
        // Apply Prism.js highlighting
        Prism.highlightElement(document.getElementById("yaml-content"));
        scrollToElement("#yaml-container");
    }
    else if(event.type === "url"){
        const a = $("<a></a>");
        a.html(cleanMessage);
        a.attr("href", cleanMessage);
        a.attr("target", "_blank");
        a.addClass("fs-5");
        $("#content").append(a);
        $("#text-content").show();
    }
    else if (event.type === "code"){
        const p = create_p(cleanMessage);
        p.addClass("fs-4 fw-bold mt-4");
        $("#content").append(p);
        $("#text-content").show();
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

function appendManyToLogPanel(messages, logPanel) {
    if (!messages || !messages.length)
        return;

    // Appends chunk messages to the log panel
    const frag = document.createDocumentFragment();
    for (const m of messages) {
        const node = document.createTextNode(m + "\n");
        frag.appendChild(node);
        logNodes.push(node);
    }
    logPanel.appendChild(frag);

    const overflow = logNodes.length - window.maxLogMessages;
    if (overflow > 0) {
        for (let i = 0; i < overflow; i++) {
            logPanel.removeChild(logNodes.shift());
        }
    }
    // Scroll to the bottom of the log panel to show the latest logs
    logPanel.scrollTop = logPanel.scrollHeight;
}

function appendToLogPanel(message, logPanel) {
    // Appends log messages to the log panel
    const node = document.createTextNode(message + "\n");
    logPanel.appendChild(node);
    logNodes.push(node);

    while (logNodes.length > window.maxLogMessages) {
        logPanel.removeChild(logNodes.shift());
    }
    // Scroll to the bottom of the log panel to show the latest logs
    logPanel.scrollTop = logPanel.scrollHeight;
}

$(window).on("beforeunload pagehide", () => {
    if(window.evSource){
        window.evSource.close();
        window.evSource = null;
    }
});