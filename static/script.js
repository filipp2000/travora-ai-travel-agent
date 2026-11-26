
const STORAGE_KEY = "travora_conversation_v1";

let isLoading = false;


function createEmptyState() {
    return {
        threadId: null,
        status: "idle",
        messages: [],
        brief: null,
        answer: "",

        // Prevent unsafe continuation when the result of
        // a previous API request is uncertain.
        blocked: false
    };
}


function loadState() {
    try {
        const saved = sessionStorage.getItem(STORAGE_KEY);

        if (saved) {
            const parsed = JSON.parse(saved);

            if (
                parsed &&
                Array.isArray(parsed.messages)
            ) {
                return {
                    ...createEmptyState(),
                    ...parsed
                };
            }
        }

    } catch (error) {
        console.warn("Could not restore conversation.", error);
    }

    return createEmptyState();
}


let state = loadState();


function saveState() {
    try {
        sessionStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(state)
        );

    } catch (error) {
        // The application can continue in memory even if
        // browser storage is unavailable.
        console.warn("Could not persist conversation.", error);
    }
}


function isPendingSession() {
    return Boolean(state.threadId) && (
        state.status === "requires_input" ||
        state.status === "requires_confirmation"
    );
}


function addMessage(role, content) {
    state.messages.push({
        role: role,
        content: content
    });
}



function renderMessages() {
    const container = document.getElementById("chatMessages");

    // Rebuild the conversation from the current UI state.
    container.replaceChildren();

    const messages = state.messages.length
        ? state.messages
        : [{
            role: "assistant",
            content: (
                "Hi! I'm Travora, your AI travel assistant. " +
                "Where would you like to travel?"
            )
        }];

    for (const message of messages) {
        const bubble = document.createElement("div");

        const role = message.role === "user"
            ? "user"
            : "assistant";

        bubble.className = `chat-message ${role}`;

        const label = document.createElement("span");
        label.className = "message-label";

        label.textContent = role === "user"
            ? "You"
            : "Travora";

        const content = document.createElement("div");
        content.className = "message-content";

        // Never insert raw user or LLM text as HTML.
        content.textContent = message.content;

        bubble.append(label, content);
        container.appendChild(bubble);
    }

    // Keep the most recent conversational turn visible.
    container.scrollTop = container.scrollHeight;
}


function renderTripBrief(brief) {
    const destination = document.getElementById(
        "briefDestination"
    );

    const details = document.getElementById("briefDetails");

    destination.textContent =
        brief.destination || "Destination";

    details.replaceChildren();

    const budget = brief.budget
        ? (
            `${brief.budget.amount} ${brief.budget.currency} ` +
            `(${brief.budget.scope === "total_trip"
                ? "Total trip"
                : "Per night"})`
        )
        : "Not specified";

    const fields = [
        ["Origin", brief.origin],
        [
            "Duration",
            brief.duration_days != null
                ? `${brief.duration_days} days`
                : null
        ],
        ["Travel period", brief.travel_period],
        ["Travelers", brief.travelers],
        ["Budget", budget],
        [
            "Preferences",
            brief.preferences?.join(", ")
        ],
        [
            "Services",
            brief.capabilities?.join(", ")
        ]
    ];

    for (const [label, value] of fields) {
        const row = document.createElement("div");
        row.className = "brief-row";

        const term = document.createElement("dt");
        term.textContent = label;

        const description = document.createElement("dd");

        description.textContent =
            value ?? "Not specified";

        if (description.textContent === "") {
            description.textContent = "Not specified";
        }

        row.append(term, description);
        details.appendChild(row);
    }
}


function renderTravelResult(answer) {
    const resultBox = document.getElementById("resultBox");

    // Default to plain text if a rendering dependency fails.
    resultBox.textContent = answer;
    resultBox.style.whiteSpace = "pre-wrap";

    if (
        typeof marked === "undefined" ||
        typeof DOMPurify === "undefined" ||
        !DOMPurify.isSupported
    ) {
        return;
    }

    try {
        // Convert Markdown to HTML and sanitize before rendering.
        const html = marked.parse(answer, {
            async: false
        });

        const cleanHtml = DOMPurify.sanitize(html, {
            ALLOWED_TAGS: [
                "h1", "h2", "h3", "h4",
                "p", "br", "strong", "em",
                "ul", "ol", "li",
                "table", "thead", "tbody",
                "tr", "th", "td",
                "blockquote", "pre", "code",
                "a", "hr"
            ],
            ALLOWED_ATTR: ["href", "title"]
        });

        resultBox.innerHTML = cleanHtml;
        resultBox.style.whiteSpace = "";

    } catch (error) {
        // Keep the safe plain-text fallback.
        console.warn("Markdown rendering failed.", error);
    }
}

// chat messages and trip panel rendering
function renderTripPanel() {
    const emptySection = document.getElementById(
        "tripEmptyState"
    );

    const briefSection = document.getElementById(
        "tripBriefSection"
    );

    const resultSection = document.getElementById(
        "resultSection"
    );

    const hasBrief =
        state.status === "requires_confirmation" &&
        state.brief !== null;

    const hasResult =
        state.status === "completed";

    emptySection.classList.toggle(
        "hidden",
        hasBrief || hasResult
    );

    briefSection.classList.toggle(
        "hidden",
        !hasBrief
    );

    resultSection.classList.toggle(
        "hidden",
        !hasResult
    );

    if (hasBrief) {
        renderTripBrief(state.brief);
    }

    if (hasResult) {
        renderTravelResult(state.answer);
    } else {
        document.getElementById("resultBox")
            .replaceChildren();
    }
}


// Ui controls, loading and errors

function renderControls() {
    const input = document.getElementById("userInput");
    const status = document.getElementById("sessionStatus");

    const awaitingConfirmation =
        state.status === "requires_confirmation";

    const completed =
        state.status === "completed";

    const cannotSubmit =
        isLoading || state.blocked || completed;

    document.getElementById("sendBtn").disabled =
        cannotSubmit;

    input.disabled = cannotSubmit;

    document.getElementById("newTripBtn").disabled =
        isLoading;

    const cancelBtn = document.getElementById("cancelTripBtn");

    cancelBtn.disabled = isLoading;

    cancelBtn.classList.toggle(
        "hidden",
        !isPendingSession()
    );

    // Build and Edit are available only at the confirmation gate.
    for (const id of ["buildPlanBtn", "editBriefBtn"]) {
        document.getElementById(id).disabled =
            isLoading ||
            state.blocked ||
            !awaitingConfirmation;
    }

    for (const id of ["copyBtn", "downloadBtn"]) {
        document.getElementById(id).disabled =
            isLoading || !completed;
    }

    document.getElementById("btnText")
        .classList.toggle("hidden", isLoading);

    document.getElementById("btnLoader")
        .classList.toggle("hidden", !isLoading);

    // Display the current conversational phase.
    if (isLoading) {
        status.textContent = "Working on your request...";

    } else if (state.blocked) {
        status.textContent =
            "Session uncertain. Please start a new trip.";

    } else if (state.status === "requires_input") {
        status.textContent = "Collecting trip details";
        input.placeholder = "Reply to Travora...";

    } else if (awaitingConfirmation) {
        status.textContent = "Awaiting your confirmation";
        input.placeholder =
            "Tell me what you would like to change...";

    } else if (completed) {
        status.textContent = "Travel request completed";
        input.placeholder = "Start a new trip to continue.";

    } else {
        status.textContent = "Ready to plan";
        input.placeholder = "Where would you like to travel?";
    }
}


function render() {
    renderMessages();
    renderTripPanel();
    renderControls();
}


function setLoading(value) {
    isLoading = value;
    renderControls();
}


function showError(message) {
    const errorBox = document.getElementById("errorBox");

    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}


function hideError() {
    const errorBox = document.getElementById("errorBox");

    errorBox.textContent = "";
    errorBox.classList.add("hidden");
}


// API communication and conversation actions

async function postTravelAction(payload) {
    const response = await fetch("/api/travel", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        const error = new Error(
            data.error || "Unable to process your request."
        );

        // Preserve the HTTP status for session error handling.
        error.status = response.status;

        throw error;
    }

    return data;
}


function applyTravelResponse(data) {
    const validStatuses = [
        "requires_input",
        "requires_confirmation",
        "completed"
    ];

    if (
        !validStatuses.includes(data.status) ||
        !data.thread_id
    ) {
        throw new Error("Unexpected response from Travora.");
    }

    if (
        data.status === "requires_confirmation" &&
        !data.brief
    ) {
        throw new Error("Trip brief is missing.");
    }

    // Existing sessions must retain the same thread ID.
    if (
        state.threadId &&
        state.threadId !== data.thread_id
    ) {
        throw new Error("Unexpected session change.");
    }

    state.threadId = data.thread_id;
    state.status = data.status;
    state.brief = data.brief ?? null;
    state.blocked = false;

    if (data.status === "completed") {
        state.answer = data.answer || "";

        addMessage(
            "assistant",
            "Your travel plan is ready! Download the plan below to keep it with you. Have a great journey!"
            
        );

    } else {
        state.answer = "";

        addMessage(
            "assistant",
            data.answer || "Please provide more details."
        );
    }

    saveState();
    render();
}


async function submitTravelAction(payload, userMessage) {
    if (isLoading || state.blocked) {
        return false;
    }

    hideError();

    addMessage("user", userMessage);

    // Persist an uncertain-state marker before sending.
    // If the page reloads while the request is running,
    // we must not approve a potentially outdated brief.
    state.blocked = true;

    saveState();
    render();
    setLoading(true);

    try {
        const data = await postTravelAction(payload);

        applyTravelResponse(data);

        return true;

    } catch (error) {

        if (error.status === 422) {
            // FastAPI rejected the input before workflow execution.
            state.messages.pop();
            state.blocked = false;
        }

        // For conflicts, network errors and unexpected failures,
        // do not retry or silently start another workflow.

        saveState();
        render();

        showError(error.message);

        return false;

    } finally {
        setLoading(false);
    }
}


async function sendMessage() {
    if (
        isLoading ||
        state.blocked ||
        state.status === "completed"
    ) {
        return;
    }

    const input = document.getElementById("userInput");
    const message = input.value.trim();

    if (!message) {
        showError("Please enter a travel request.");
        return;
    }

    const payload = {
        action: "start",
        message: message
    };

    // The backend phase determines the allowed session action.
    if (isPendingSession()) {
        payload.thread_id = state.threadId;

        payload.action =
            state.status === "requires_confirmation"
                ? "edit"
                : "reply";
    }

    const success = await submitTravelAction(
        payload,
        message
    );

    if (success) {
        input.value = "";

        if (state.status !== "completed") {
            input.focus();
        }
    }
}


async function buildPlan() {
    if (
        isLoading ||
        state.blocked ||
        state.status !== "requires_confirmation" ||
        !state.threadId
    ) {
        return;
    }

    // Explicit approval without natural-language interpretation.
    await submitTravelAction(
        {
            action: "build",
            thread_id: state.threadId
        },
        "Build Plan"
    );

    // On mobile, bring the completed result into view.
    if (state.status === "completed") {
        document.getElementById("resultSection")
            .scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
    }
}


function editTripBrief() {
    if (
        isLoading ||
        state.blocked ||
        state.status !== "requires_confirmation"
    ) {
        return;
    }

    // The next message will be submitted as EDIT.
    const input = document.getElementById("userInput");

    input.placeholder =
        "What would you like to change?";

    input.focus();
}


async function newTrip() {
    if (isLoading) {
        return;
    }

    hideError();
    setLoading(true);

    try {
        if (isPendingSession()) {
            try {
                // Persistently cancel the previous pending thread.
                const result = await postTravelAction({
                    action: "cancel",
                    thread_id: state.threadId
                });

                if (result.status !== "cancelled") {
                    throw new Error(
                        "Unexpected cancellation response."
                    );
                }

            } catch (error) {

                // A stale session may already be completed,
                // cancelled or otherwise unavailable.
                if (error.status !== 409) {
                    throw error;
                }
            }
        }

        // Reset only the local conversation view.
        // Existing database checkpoints are not deleted.
        state = createEmptyState();

        document.getElementById("userInput").value = "";

        saveState();
        render();

    } catch (error) {
        showError(
            error.message || "Unable to start a new trip."
        );

    } finally {
        setLoading(false);

        if (state.status === "idle") {
            document.getElementById("userInput").focus();
        }
    }
}


// Copy and pdf export actions
async function copyResult() {
    if (
        isLoading ||
        state.status !== "completed"
    ) {
        return;
    }

    try {
        const result = document.getElementById("resultBox");

        await navigator.clipboard.writeText(
            result.innerText
        );

        const button = document.getElementById("copyBtn");

        button.textContent = "Copied!";

        setTimeout(() => {
            button.textContent = "Copy";
        }, 1400);

    } catch (error) {
        showError("Could not copy the travel result.");
    }
}


async function downloadPDF() {
    if (
        isLoading ||
        state.status !== "completed" ||
        !state.answer
    ) {
        return;
    }

    if (typeof html2pdf === "undefined") {
        showError("PDF export is currently unavailable.");
        return;
    }

    hideError();
    setLoading(true);

    try {
        const options = {
            margin: 0.5,
            filename: "travora-travel-plan.pdf",

            image: {
                type: "jpeg",
                quality: 0.98
            },

            html2canvas: {
                scale: 2,
                backgroundColor: "#ffffff"
            },

            jsPDF: {
                unit: "in",
                format: "a4",
                orientation: "portrait"
            },

            // Avoid the previous aggressive avoid-all
            // pagination mode.
            pagebreak: {
                mode: ["css", "legacy"]
            }
        };

        await html2pdf()
            .set(options)
            .from(document.getElementById("pdfContent"))
            .save();

    } catch (error) {
        showError("Could not download the travel plan.");

    } finally {
        setLoading(false);
    }
}


// Application initialization
document.getElementById("chatForm")
    .addEventListener("submit", (event) => {
        event.preventDefault();
        sendMessage();
    });


document.getElementById("userInput")
    .addEventListener("keydown", (event) => {
        if (
            (event.ctrlKey || event.metaKey) &&
            event.key === "Enter"
        ) {
            event.preventDefault();
            sendMessage();
        }
    });


document.getElementById("newTripBtn")
    .addEventListener("click", newTrip);


document.getElementById("cancelTripBtn")
    .addEventListener("click", newTrip);


document.getElementById("buildPlanBtn")
    .addEventListener("click", buildPlan);


document.getElementById("editBriefBtn")
    .addEventListener("click", editTripBrief);


document.getElementById("copyBtn")
    .addEventListener("click", copyResult);


document.getElementById("downloadBtn")
    .addEventListener("click", downloadPDF);


// Restore the existing conversation after a page refresh.
render();

if (state.blocked) {
    showError(
        "The previous request may not have completed. " +
        "Please start a new trip."
    );
}
