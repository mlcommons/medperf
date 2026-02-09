
function create_p(msg) {
    var p = document.createElement("p");
    p.innerHTML = msg;
    return p;
}

function scrollToElement(selector) {
    var el = document.querySelector(selector);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function streamEvents(logPanel, stagesList, currentStageElement, streamOld) {
    var url = streamOld ? "/events?stream_old=true" : "/events";
    var eventSource = new EventSource(url);
    window.evSource = eventSource;

    eventSource.onmessage = function (event) {
        var data = JSON.parse(event.data);
        if (data.task_id !== window.runningTaskId) return;
        if (data.end) {
            eventSource.close();
            window.evSource = null;
            if (typeof window.onPromptComplete === "function") window.onPromptComplete(data.response);
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

function cleanMsg(message) {
    return message.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, "");
}

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
        p.className = "font-bold text-lg";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
    } else if (event.type === "warning") {
        var p = create_p(cleanMessage);
        p.className = "font-bold text-red-600 dark:text-red-400 text-xl";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
        scrollToElement("#text-content");
    } else if (event.type === "error") {
        var p = create_p(cleanMessage);
        p.className = "font-bold text-red-600 dark:text-red-400 text-xl";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
        scrollToElement("#text-content");
    } else if (event.type === "highlight") {
        var p = create_p(cleanMessage);
        p.className = "text-xl";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
        scrollToElement("#text-content");
    } else if (event.type === "prompt") {
        var p = create_p(cleanMessage);
        p.className = "mt-4 text-xl text-red-600 dark:text-red-400 font-bold";
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
        a.className = "text-lg";
        if (content) content.appendChild(a);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
    } else if (event.type === "code") {
        var p = create_p(cleanMessage);
        p.className = "text-xl font-bold mt-4";
        if (content) content.appendChild(p);
        if (textContent) { textContent.style.display = ""; textContent.classList.remove("hidden"); }
    }
    return currentStageElement;
}

function addNewStage(stageText, stagesList) {
    if (!stagesList) return null;
    var listItem = document.createElement("li");
    listItem.className = "flex items-center gap-2 py-2";
    listItem.innerHTML = "<span class=\"inline-block w-5 h-5 border-2 border-[#2e7d32] dark:border-green-400 border-t-transparent rounded-full animate-spin\" role=\"status\" aria-hidden=\"true\"></span><strong>" + stageText + "</strong>";
    stagesList.appendChild(listItem);
    return listItem;
}

function markStageAsComplete(stageElement) {
    if (!stageElement) return;
    var spinner = stageElement.querySelector(".animate-spin");
    if (spinner) {
        spinner.remove();
        var check = document.createElement("i");
        check.className = "fas fa-check-circle text-green-600 dark:text-green-400";
        check.setAttribute("aria-hidden", "true");
        stageElement.insertBefore(check, stageElement.firstChild);
    }
}

var logNodes = [];
function appendManyToLogPanel(messages, logPanel) {
    if (!messages || !messages.length || !logPanel) return;
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

function appendToLogPanel(message, logPanel) {
    if (!logPanel) return;
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
