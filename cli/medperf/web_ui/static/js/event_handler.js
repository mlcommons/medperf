/*
 * Streams the logs of the running task from the server (Server-Sent Events
 * on /events) and displays them: stages list, log panel, messages, prompts
 * and YAML output.
 */

/** Create a paragraph holding the given HTML. */
function create_p(msg) {
    var p = document.createElement("p");
    p.innerHTML = msg;
    return p;
}

/** Smoothly scroll to the element matching a selector. */
function scrollToElement(selector) {
    var el = document.querySelector(selector);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

/**
 * Stream the events of the running task (window.taskId) and display them.
 * With `streamOld`, the events already emitted are sent again first.
 * Stops at the end of the task (calling window.onPromptComplete with its
 * response) or when a prompt waits for the user's answer.
 */
function streamEvents(logPanel, stagesList, currentStageElement, streamOld) {
    var url = "/events?";
    url += streamOld ? "stream_old=true" : "stream_old=false";
    
    var eventSource = new EventSource(url);
    window.evSource = eventSource;

    eventSource.onmessage = function (event) {
        var data = JSON.parse(event.data);
        if (data.task_id != null && data.task_id !== window.taskId) return;
        if (data.end) {
            eventSource.close();
            window.evSource = null;
            if (typeof window.onPromptComplete === "function") {
                window.onPromptComplete(data.response);
                window.onPromptComplete = null;
            }
            return;
        }
        currentStageElement = handleEvents(data, logPanel, stagesList, currentStageElement);
        if (window.isPromptReceived) {
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

/** Remove terminal color/style escape sequences from a message. */
function cleanMsg(message) {
    return message.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, "");
}

/**
 * Display one event (or chunk of log lines) of the running task, according
 * to its type. Returns the stage element currently in progress.
 */
function handleEvents(event, logPanel, stagesList, currentStageElement) {
    if (event.kind === "chunk") {
        var lines = [];
        for (var i = 0; i < (event.events || []).length; i++) lines.push(cleanMsg(event.events[i].message));
        appendManyToLogPanel(lines, logPanel);
        return currentStageElement;
    }
    var cleanMessage = cleanMsg(event.message || "");
    if (event.interactive) {
        if (event.type === "text") {
            if (currentStageElement) markStageAsComplete(currentStageElement);
            currentStageElement = addNewStage(cleanMessage, stagesList);
            return currentStageElement;
        }
        if (event.type === "print") {
            appendToLogPanel(cleanMessage, logPanel);
            return currentStageElement;
        }
    }
    if (event.type === "yaml") cleanMessage = event.message;
    else cleanMessage = cleanMessage.replace("\n", "<br>");

    var content = document.getElementById("content");
    var textContent = document.getElementById("text-content");
    var promptText = document.getElementById("prompt-text");
    var promptContainer = document.getElementById("prompt-container");
    var yamlContent = document.getElementById("yaml-content");
    var yamlContainer = document.getElementById("yaml-container");

    if (event.type === "print") {
        var p = create_p(cleanMessage);
        p.className = "font-bold text-lg text-ink";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
    } else if (event.type === "warning") {
        var p = create_p(cleanMessage);
        p.className = "font-bold text-danger text-xl";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
        scrollToElement("#text-content");
    } else if (event.type === "error") {
        var p = create_p(cleanMessage);
        p.className = "font-bold text-danger text-xl";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
        scrollToElement("#text-content");
    } else if (event.type === "highlight") {
        var p = create_p(cleanMessage);
        p.className = "text-xl text-ink";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
        scrollToElement("#text-content");
    } else if (event.type === "prompt") {
        var p = create_p(cleanMessage);
        p.className = "mt-4 text-xl text-danger font-bold";
        if (promptText) promptText.innerHTML = "";
        if (promptText) promptText.appendChild(p);
        if (promptContainer) { promptContainer.style.display = ""; promptContainer.classList.remove("hidden"); }
        scrollToElement("#prompt-container");
        window.isPromptReceived = true;
    } else if (event.type === "yaml") {
        if (yamlContent) yamlContent.innerHTML = cleanMessage;
        if (yamlContainer) { yamlContainer.style.display = ""; yamlContainer.classList.remove("hidden"); }
        if (window.Prism && yamlContent) Prism.highlightElement(yamlContent);
        scrollToElement("#yaml-container");
    } else if (event.type === "url") {
        var a = document.createElement("a");
        a.href = cleanMessage;
        a.target = "_blank";
        a.textContent = cleanMessage;
        a.className = "text-lg font-bold text-ink text-brand-accent hover:underline";
        if (content) content.appendChild(a);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
    } else if (event.type === "code") {
        var p = create_p(cleanMessage);
        p.className = "text-xl font-bold mt-4 text-ink";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
    }
    return currentStageElement;
}

/** Add a stage (with a spinner) to the stages list of the running task. */
function addNewStage(stageText, stagesList) {
    if (!stagesList) return null;
    var listItem = document.createElement("li");
    listItem.className = "flex items-center gap-2 py-2";
    var spinner = document.createElement("span");
    spinner.className = STAGE_SPINNER_CLASS;
    spinner.setAttribute("role", "status");
    spinner.setAttribute("aria-hidden", "true");
    var strong = document.createElement("strong");
    strong.textContent = stageText;
    listItem.appendChild(spinner);
    listItem.appendChild(strong);
    stagesList.appendChild(listItem);
    return listItem;
}

/** Replace the spinner of a stage by a check mark. */
function markStageAsComplete(stageElement) {
    if (!stageElement) return;
    var spinner = stageElement.querySelector(".animate-spin");
    if (spinner) {
        spinner.remove();
        var check = document.createElement("i");
        check.className = "fas fa-check-circle text-brand-accent flex-shrink-0";
        check.setAttribute("aria-hidden", "true");
        stageElement.insertBefore(check, stageElement.firstChild);
    }
}

var logNodes = [];

/** Show the log panel section when the first log line arrives. */
function showLogPanelSectionIfHidden() {
    var s = document.getElementById("log-panel-section");
    if (s && s.classList.contains("hidden")) {
        s.classList.remove("hidden");
        s.setAttribute("aria-hidden", "false");
    }
}

/**
 * Append log lines to the log panel, keeping only the last
 * window.maxLogMessages lines.
 */
function appendManyToLogPanel(messages, logPanel) {
    if (!messages || !messages.length || !logPanel) return;
    showLogPanelSectionIfHidden();
    for (var i = 0; i < messages.length; i++) {
        var node = document.createTextNode(messages[i] + "\n");
        logPanel.appendChild(node);
        logNodes.push(node);
    }
    var maxLog = window.maxLogMessages || 1000;
    while (logNodes.length > maxLog) {
        var first = logNodes.shift();
        if (first && first.parentNode) first.parentNode.removeChild(first);
    }
    logPanel.scrollTop = logPanel.scrollHeight;
}

/**
 * Append a log line to the log panel, keeping only the last
 * window.maxLogMessages lines.
 */
function appendToLogPanel(message, logPanel) {
    if (!logPanel) return;
    showLogPanelSectionIfHidden();
    var node = document.createTextNode(message + "\n");
    logPanel.appendChild(node);
    logNodes.push(node);
    var maxLog = window.maxLogMessages || 1000;
    while (logNodes.length > maxLog) {
        var first = logNodes.shift();
        if (first && first.parentNode) first.parentNode.removeChild(first);
    }
    logPanel.scrollTop = logPanel.scrollHeight;
}

window.addEventListener("beforeunload", function () {
    if (window.evSource) {
        window.evSource.close();
        window.evSource = null;
    }
});
window.addEventListener("pagehide", function () {
    if (window.evSource) {
        window.evSource.close();
        window.evSource = null;
    }
});
