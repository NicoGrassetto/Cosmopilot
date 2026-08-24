"use strict";

const APPROVAL_MESSAGE = "Approve and open the coordination case exactly as shown in the pending decision card.";
const STORAGE_KEY = "eu-resilience-desk-state-v1";
const INITIAL_MESSAGE = "EU27 resilience snapshot ready. Which country or priority set should we review?";
const DOCUMENT_PATH_PATTERN = /^\/api\/documents\/[0-9a-f]{32}$/;

const messageStream = document.querySelector("#messageStream");
const messageTemplate = document.querySelector("#messageTemplate");
const composer = document.querySelector("#composer");
const messageInput = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const typingIndicator = document.querySelector("#typingIndicator");
const typingStatusText = document.querySelector("#typingStatusText");
const agentActivity = document.querySelector("#agentActivity");
const activityState = document.querySelector("#activityState");
const activityTitle = document.querySelector("#activityTitle");
const activitySteps = document.querySelector("#activitySteps");
const connectionStatus = document.querySelector("#connectionStatus");
const serviceBanner = document.querySelector("#serviceBanner");
const serviceBannerText = document.querySelector("#serviceBannerText");
const approvalSection = document.querySelector("#approvalSection");
const approvalTitle = document.querySelector("#approvalTitle");
const approvalDescription = document.querySelector("#approvalDescription");
const approvalCheck = document.querySelector("#approvalCheck");
const approveButton = document.querySelector("#approveButton");
const resetSessionButton = document.querySelector("#resetSession");
const sessionLabel = document.querySelector("#sessionLabel");
const navigationPanel = document.querySelector("#navigationPanel");
const controlsPanel = document.querySelector("#controlsPanel");
const openNavigation = document.querySelector("#openNavigation");
const openControls = document.querySelector("#openControls");
const panelBackdrop = document.querySelector("#panelBackdrop");

let state = {
    sessionId: null,
    messages: [],
    pendingApproval: false,
    approvalComplete: false,
};
let requestInFlight = false;
let activityEntries = [];

try {
    const storedState = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null");
    if (storedState && Array.isArray(storedState.messages)) {
        state = {
            sessionId: typeof storedState.sessionId === "string" ? storedState.sessionId : null,
            messages: storedState.messages.slice(-40),
            pendingApproval: Boolean(storedState.pendingApproval),
            approvalComplete: Boolean(storedState.approvalComplete),
        };
    }
} catch {
    sessionStorage.removeItem(STORAGE_KEY);
}

if (state.messages.length === 0) {
    state.messages.push({
        role: "assistant",
        content: INITIAL_MESSAGE,
        time: new Date().toISOString(),
    });
}

function persistState() {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function appendInlineContent(element, text) {
    const tokenPattern = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^)]+\))/g;
    let cursor = 0;

    for (const match of text.matchAll(tokenPattern)) {
        if (match.index > cursor) {
            element.append(document.createTextNode(text.slice(cursor, match.index)));
        }

        const token = match[0];
        if (token.startsWith("**")) {
            const strong = document.createElement("strong");
            strong.textContent = token.slice(2, -2);
            element.append(strong);
        } else if (token.startsWith("`")) {
            const code = document.createElement("code");
            code.textContent = token.slice(1, -1);
            element.append(code);
        } else {
            const linkMatch = /^\[([^\]]+)\]\((https?:\/\/[^)]+)\)$/.exec(token);
            if (linkMatch) {
                const link = document.createElement("a");
                link.textContent = linkMatch[1];
                link.href = linkMatch[2];
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                element.append(link);
            }
        }
        cursor = match.index + token.length;
    }

    if (cursor < text.length) {
        element.append(document.createTextNode(text.slice(cursor)));
    }
}

function renderAssistantContent(container, content) {
    const lines = content.replace(/\r/g, "").split("\n");
    let activeList = null;
    let activeListType = null;

    for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
            activeList = null;
            activeListType = null;
            continue;
        }

        const headingMatch = /^(#{1,3})\s+(.+)$/.exec(line);
        const bulletMatch = /^[-*]\s+(.+)$/.exec(line);
        const orderedMatch = /^\d+\.\s+(.+)$/.exec(line);

        if (headingMatch) {
            activeList = null;
            activeListType = null;
            const heading = document.createElement(`h${Math.min(headingMatch[1].length + 1, 4)}`);
            appendInlineContent(heading, headingMatch[2]);
            container.append(heading);
        } else if (bulletMatch || orderedMatch) {
            const listType = bulletMatch ? "ul" : "ol";
            if (!activeList || activeListType !== listType) {
                activeList = document.createElement(listType);
                activeListType = listType;
                container.append(activeList);
            }
            const item = document.createElement("li");
            appendInlineContent(item, (bulletMatch || orderedMatch)[1]);
            activeList.append(item);
        } else if (/^---+$/.test(line)) {
            activeList = null;
            activeListType = null;
            container.append(document.createElement("hr"));
        } else if (line.startsWith("> ")) {
            activeList = null;
            activeListType = null;
            const quote = document.createElement("blockquote");
            appendInlineContent(quote, line.slice(2));
            container.append(quote);
        } else {
            activeList = null;
            activeListType = null;
            const paragraph = document.createElement("p");
            appendInlineContent(paragraph, line);
            container.append(paragraph);
        }
    }
}

function renderDocumentCards(container, documents) {
    if (!Array.isArray(documents)) {
        return;
    }

    for (const documentMetadata of documents) {
        if (
            !documentMetadata
            || typeof documentMetadata.downloadUrl !== "string"
            || !DOCUMENT_PATH_PATTERN.test(documentMetadata.downloadUrl)
        ) {
            continue;
        }

        const card = document.createElement("article");
        card.className = "document-card";

        const iconWrap = document.createElement("div");
        iconWrap.className = "document-card-icon";
        iconWrap.setAttribute("aria-hidden", "true");
        const icon = document.createElement("img");
        icon.src = "/assets/database.svg";
        icon.alt = "";
        iconWrap.append(icon);

        const details = document.createElement("div");
        const title = document.createElement("h4");
        title.textContent = typeof documentMetadata.title === "string"
            ? documentMetadata.title
            : "EU resilience briefing";
        const metadata = document.createElement("p");
        const scope = documentMetadata.scope === "eu_priorities" ? "EU27 priorities" : "Country briefing";
        const chartCount = Number.isInteger(documentMetadata.chartCount)
            ? `${documentMetadata.chartCount} charts`
            : "Chart pack";
        metadata.textContent = `${scope} · ${chartCount} · DOCX`;
        details.append(title, metadata);

        const download = document.createElement("a");
        download.className = "document-download";
        download.href = documentMetadata.downloadUrl;
        if (typeof documentMetadata.fileName === "string") {
            download.download = documentMetadata.fileName;
        }
        const downloadIcon = document.createElement("img");
        downloadIcon.src = "/assets/arrow-up-right.svg";
        downloadIcon.alt = "";
        downloadIcon.setAttribute("aria-hidden", "true");
        download.append(downloadIcon, document.createTextNode("Download DOCX"));

        card.append(iconWrap, details, download);
        container.append(card);
    }
}

function renderMessages() {
    messageStream.replaceChildren();
    for (const message of state.messages) {
        const fragment = messageTemplate.content.cloneNode(true);
        const article = fragment.querySelector(".message");
        const author = fragment.querySelector(".message-author");
        const time = fragment.querySelector("time");
        const content = fragment.querySelector(".message-content");
        const documents = fragment.querySelector(".message-documents");

        article.dataset.role = message.role;
        author.textContent = message.role === "user" ? "You" : message.role === "error" ? "Service" : "Resilience agent";
        const timestamp = new Date(message.time);
        time.dateTime = timestamp.toISOString();
        time.textContent = timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

        if (message.role === "assistant") {
            renderAssistantContent(content, message.content);
            renderDocumentCards(documents, message.documents);
        } else {
            content.textContent = message.content;
        }
        messageStream.append(fragment);
    }
    messageStream.scrollTop = messageStream.scrollHeight;
}

function renderActivity() {
    activitySteps.replaceChildren();
    for (const entry of activityEntries.slice(-5)) {
        const item = document.createElement("li");
        item.dataset.state = entry.state;
        item.textContent = entry.message;
        activitySteps.append(item);
    }
}

function startActivity() {
    activityEntries = [];
    agentActivity.hidden = false;
    agentActivity.dataset.state = "working";
    activityState.textContent = "Agent working";
    activityTitle.textContent = "Starting the governed workflow";
    typingStatusText.textContent = "Starting governed workflow";
    renderActivity();
}

function updateActivity(message, state = "working") {
    if (typeof message !== "string" || !message) {
        return;
    }
    agentActivity.hidden = false;
    agentActivity.dataset.state = state === "error" ? "error" : "working";
    activityState.textContent = state === "error" ? "Attention required" : "Live agent activity";
    activityTitle.textContent = message;
    typingStatusText.textContent = message;
    const previous = activityEntries.at(-1);
    if (!previous || previous.message !== message) {
        activityEntries.push({ message, state });
        renderActivity();
    } else {
        previous.state = state;
        renderActivity();
    }
}

function finishActivity(success, message) {
    agentActivity.hidden = false;
    agentActivity.dataset.state = success ? "complete" : "error";
    activityState.textContent = success ? "Completed" : "Request failed";
    activityTitle.textContent = message;
    typingStatusText.textContent = message;
}

function handleAgentEvent(event) {
    if (!event || typeof event.type !== "string") {
        return null;
    }
    if (event.type === "status" || event.type === "tool_start") {
        updateActivity(event.message, "working");
    } else if (event.type === "tool_complete") {
        updateActivity(event.message, event.success === false ? "error" : "complete");
    } else if (event.type === "document") {
        updateActivity(event.message || "Downloadable document ready", "complete");
    } else if (event.type === "error") {
        throw new Error(event.detail || event.error || "The agent request failed.");
    } else if (event.type === "result") {
        return event;
    }
    return null;
}

async function readAgentEventStream(response) {
    if (!response.body) {
        throw new Error("This browser cannot read live agent progress.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let result = null;

    while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
            if (!line.trim()) {
                continue;
            }
            let event;
            try {
                event = JSON.parse(line);
            } catch {
                throw new Error("The live agent progress stream was malformed.");
            }
            result = handleAgentEvent(event) || result;
        }
        if (done) {
            break;
        }
    }

    if (buffer.trim()) {
        try {
            result = handleAgentEvent(JSON.parse(buffer)) || result;
        } catch (error) {
            if (error instanceof SyntaxError) {
                throw new Error("The live agent progress stream was incomplete.");
            }
            throw error;
        }
    }
    if (!result) {
        throw new Error("The agent stream ended before returning a response.");
    }
    return result;
}

function updateApprovalState() {
    approvalCheck.checked = false;

    if (state.approvalComplete) {
        approvalSection.dataset.state = "complete";
        approvalTitle.textContent = "Case instruction submitted";
        approvalDescription.textContent = "The execution result is recorded in the conversation.";
        approvalCheck.disabled = true;
        approveButton.disabled = true;
        approveButton.textContent = "Submission completed";
        return;
    }

    if (state.pendingApproval) {
        approvalSection.dataset.state = "pending";
        approvalTitle.textContent = "Decision pending approval";
        approvalDescription.textContent = "Review the visible decision card before authorizing one case submission.";
        approvalCheck.disabled = false;
        approveButton.disabled = true;
        approveButton.replaceChildren();
        const icon = document.createElement("img");
        icon.src = "/assets/check-circle-2.svg";
        icon.alt = "";
        icon.setAttribute("aria-hidden", "true");
        approveButton.append(icon, document.createTextNode("Approve and open case"));
        return;
    }

    approvalSection.dataset.state = "idle";
    approvalTitle.textContent = "No decision pending";
    approvalDescription.textContent = "A reviewed decision card is required before a case can be opened.";
    approvalCheck.disabled = true;
    approveButton.disabled = true;
    approveButton.replaceChildren();
    const icon = document.createElement("img");
    icon.src = "/assets/check-circle-2.svg";
    icon.alt = "";
    icon.setAttribute("aria-hidden", "true");
    approveButton.append(icon, document.createTextNode("Approve and open case"));
}

function setBusy(isBusy) {
    requestInFlight = isBusy;
    messageInput.disabled = isBusy;
    sendButton.disabled = isBusy;
    typingIndicator.hidden = !isBusy;
    document.querySelectorAll("[data-prompt]").forEach((button) => {
        button.disabled = isBusy;
    });
    if (isBusy) {
        messageStream.scrollTop = messageStream.scrollHeight;
    }
}

function showServiceError(message) {
    serviceBannerText.textContent = message;
    serviceBanner.hidden = false;
}

function clearServiceError() {
    serviceBanner.hidden = true;
    serviceBannerText.textContent = "";
}

async function sendMessage(message, approveCoordinationCase = false) {
    if (requestInFlight || !message.trim()) {
        return;
    }

    closePanels();
    clearServiceError();
    state.messages.push({ role: "user", content: message.trim(), time: new Date().toISOString() });
    state.messages = state.messages.slice(-40);
    persistState();
    renderMessages();
    setBusy(true);
    startActivity();

    try {
        const response = await fetch("/api/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message.trim(),
                sessionId: state.sessionId,
                approveCoordinationCase,
            }),
        });
        if (!response.ok) {
            const payload = await response.json();
            throw new Error(payload.detail || payload.error || "Agent request failed.");
        }
        const payload = await readAgentEventStream(response);

        state.sessionId = payload.sessionId;
        state.messages.push({
            role: "assistant",
            content: payload.message,
            documents: Array.isArray(payload.documents) ? payload.documents : [],
            time: new Date().toISOString(),
        });
        state.messages = state.messages.slice(-40);

        state.pendingApproval = Boolean(payload.pendingApproval);
        state.approvalComplete = Boolean(payload.coordinationCaseSubmitted);
        sessionLabel.textContent = `Review ${state.sessionId.slice(0, 8)}`;
        persistState();
        renderMessages();
        updateApprovalState();
        finishActivity(true, "Response and requested deliverables are ready");
    } catch (error) {
        const messageText = error instanceof Error ? error.message : "The agent request failed.";
        state.messages.push({ role: "error", content: messageText, time: new Date().toISOString() });
        persistState();
        renderMessages();
        showServiceError(messageText);
        finishActivity(false, messageText);
    } finally {
        setBusy(false);
        messageInput.focus();
    }
}

function resizeComposer() {
    messageInput.style.height = "auto";
    messageInput.style.height = `${Math.min(messageInput.scrollHeight, 150)}px`;
}

function closePanels() {
    navigationPanel.dataset.open = "false";
    controlsPanel.dataset.open = "false";
    openNavigation.setAttribute("aria-expanded", "false");
    openControls.setAttribute("aria-expanded", "false");
    panelBackdrop.hidden = true;
}

function openPanel(panel, button) {
    closePanels();
    panel.dataset.open = "true";
    button.setAttribute("aria-expanded", "true");
    panelBackdrop.hidden = false;
}

composer.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = messageInput.value;
    if (!message.trim()) {
        return;
    }
    messageInput.value = "";
    resizeComposer();
    void sendMessage(message);
});

messageInput.addEventListener("input", resizeComposer);
messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        composer.requestSubmit();
    }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
        void sendMessage(button.dataset.prompt || "");
    });
});

approvalCheck.addEventListener("change", () => {
    approveButton.disabled = !approvalCheck.checked || requestInFlight;
});

approveButton.addEventListener("click", () => {
    if (!approvalCheck.checked || !state.pendingApproval || requestInFlight) {
        return;
    }
    approvalCheck.disabled = true;
    approveButton.disabled = true;
    void sendMessage(APPROVAL_MESSAGE, true);
});

resetSessionButton.addEventListener("click", async () => {
    if (requestInFlight) {
        return;
    }
    const previousSessionId = state.sessionId;
    state = {
        sessionId: null,
        messages: [{ role: "assistant", content: INITIAL_MESSAGE, time: new Date().toISOString() }],
        pendingApproval: false,
        approvalComplete: false,
    };
    sessionLabel.textContent = "New review";
    persistState();
    renderMessages();
    updateApprovalState();
    clearServiceError();
    agentActivity.hidden = true;
    activityEntries = [];
    if (previousSessionId) {
        try {
            await fetch("/api/session/reset", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sessionId: previousSessionId }),
            });
        } catch {
            showServiceError("The local session reset could not be confirmed.");
        }
    }
    messageInput.focus();
});

openNavigation.addEventListener("click", () => openPanel(navigationPanel, openNavigation));
openControls.addEventListener("click", () => openPanel(controlsPanel, openControls));
panelBackdrop.addEventListener("click", closePanels);
document.querySelectorAll("[data-close-panels]").forEach((button) => {
    button.addEventListener("click", closePanels);
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closePanels();
    }
});

async function checkHealth() {
    try {
        const response = await fetch("/api/health", { cache: "no-store" });
        const payload = await response.json();
        if (!response.ok || !payload.azureConfigured) {
            throw new Error("Azure environment is not configured for this server.");
        }
        connectionStatus.dataset.state = "online";
        connectionStatus.lastChild.textContent = " Agent ready";
    } catch (error) {
        const message = error instanceof Error ? error.message : "Agent service unavailable.";
        connectionStatus.dataset.state = "offline";
        connectionStatus.lastChild.textContent = " Service unavailable";
        showServiceError(message);
    }
}

renderMessages();
updateApprovalState();
if (state.sessionId) {
    sessionLabel.textContent = `Review ${state.sessionId.slice(0, 8)}`;
}
resizeComposer();
void checkHealth();