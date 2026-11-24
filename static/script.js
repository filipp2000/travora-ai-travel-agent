// A thread is persisted only while LangGraph is
// waiting for clarification from the user.
let pendingThreadId =
    localStorage.getItem(
        "pending_travel_thread_id"
    ) || null;

// Keep track of what kind of input the pending thread expects.
let pendingStatus =
    localStorage.getItem("pending_travel_status")
    || (pendingThreadId ? "requires_input" : null);

let latestAnswerMarkdown = "";

// Clean up the legacy behavior where every request
// reused the last completed thread.
localStorage.removeItem(
    "travel_thread_id"
);

function setPrompt(text) {
    document.getElementById("userInput").value = text;
}


function setLoading(isLoading) {
    const btnText = document.getElementById("btnText");
    const btnLoader = document.getElementById("btnLoader");

    // Disable all action buttons while a request is running
    // to prevent competing session actions or duplicate requests.
    const actionButtonIds = [
        "sendBtn",
        "newTripBtn",
        "cancelTripBtn",
        "buildPlanBtn",
        "editBriefBtn"
    ];

    for (const id of actionButtonIds) {
        const button = document.getElementById(id);

        // Safely handle buttons that may not exist in the current UI.
        if (button) {
            button.disabled = isLoading;
        }
    }

    // Toggle the loading indicator on the main submit button.
    if (isLoading) {
        btnText.classList.add("hidden");
        btnLoader.classList.remove("hidden");
    } else {
        btnText.classList.remove("hidden");
        btnLoader.classList.add("hidden");
    }
}


function showError(message) {
    const errorBox = document.getElementById("errorBox");

    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}

function hideError() {
    const errorBox = document.getElementById("errorBox");

    errorBox.classList.add("hidden");
    errorBox.textContent = "";
}

function showResult(answer, threadId) {
    latestAnswerMarkdown = answer;

    const resultSection = document.getElementById("resultSection");
    const resultBox = document.getElementById("resultBox");
    const threadInfo = document.getElementById("threadInfo");

    if (typeof marked !== "undefined") {
        resultBox.innerHTML = marked.parse(answer);
    } else {
        resultBox.innerText = answer;
    }

    threadInfo.textContent = `Thread ID: ${threadId}`;

    resultSection.classList.remove("hidden");

    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}



async function sendMessage() {
    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");

    if (sendBtn.disabled) {
        return;
    }

    const message = input.value.trim();

    if (!message) {
        showError("Please enter your travel request.");
        return;
    }

    hideError();

    // ---------------------------------------------
    // Choose the action using explicit session phase.
    // ---------------------------------------------
    let action = "start";

    if (pendingThreadId) {
        action = pendingStatus === "requires_confirmation"
            ? "edit"
            : "reply";
    }

    setLoading(true);

    try {
        const data = await postTravelAction({
            action: action,
            message: message,
            thread_id: pendingThreadId
        });

        handleTravelResponse(data);

        // Clear text only after successful processing.
        input.value = "";

    } catch (error) {
        showError(
            error.message || "Unable to process your request."
        );

    } finally {
        setLoading(false);
    }
}


function clearPendingThread() {
    // Clear both in-memory and browser-persisted session state.
    pendingThreadId = null;
    pendingStatus = null;

    // Both identifiers must be cleared together.
    localStorage.removeItem("pending_travel_thread_id");
    localStorage.removeItem("pending_travel_status");

    syncSessionControls();
}

function copyResult() {
    const resultBox = document.getElementById("resultBox");
    const text = resultBox.innerText;

    if (!text) {
        return;
    }

    navigator.clipboard.writeText(text)
        .then(() => {
            const copyBtn = document.querySelector(".copy-btn");
            const oldText = copyBtn.textContent;

            copyBtn.textContent = "Copied!";

            setTimeout(() => {
                copyBtn.textContent = oldText;
            }, 1400);
        })
        .catch(() => {
            showError("Could not copy result.");
        });
}

function downloadPDF() {
    const pdfContent = document.getElementById("pdfContent");

    if (!latestAnswerMarkdown || !pdfContent) {
        showError("No travel plan available to download.");
        return;
    }

    const downloadBtn = document.querySelector(".download-btn");
    const oldText = downloadBtn.textContent;

    downloadBtn.textContent = "Preparing PDF...";
    downloadBtn.disabled = true;

    const options = {
        margin: 0.5,
        filename: "ai-travel-plan.pdf",
        image: {
            type: "jpeg",
            quality: 0.98
        },
        html2canvas: {
            scale: 2,
            useCORS: true,
            backgroundColor: "#ffffff"
        },
        jsPDF: {
            unit: "in",
            format: "a4",
            orientation: "portrait"
        },
        pagebreak: {
            mode: ["avoid-all", "css", "legacy"]
        }
    };

    html2pdf()
        .set(options)
        .from(pdfContent)
        .save()
        .then(() => {
            downloadBtn.textContent = oldText;
            downloadBtn.disabled = false;
        })
        .catch(() => {
            downloadBtn.textContent = oldText;
            downloadBtn.disabled = false;
            showError("Could not download PDF.");
        });
}

document.addEventListener("keydown", function(event) {
    if (event.ctrlKey && event.key === "Enter") {
        sendMessage();
    }
});


function syncSessionControls() {
    const cancelBtn = document.getElementById("cancelTripBtn");

    if (cancelBtn) {
        // Cancel is useful only while clarification is pending.
        cancelBtn.classList.toggle("hidden", !pendingThreadId);
    }
}


async function cancelPendingSession() {
    if (!pendingThreadId) {
        return;
    }

    const response = await fetch("/api/travel", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            action: "cancel",
            thread_id: pendingThreadId
        })
    });

    const data = await response.json();

    if (response.status === 409) {
        // The server no longer recognizes this as an active
        // interrupted session. Clear the stale client pointer.
        clearPendingThread();
        return;
    }

    if (!response.ok || !data.success) {
        throw new Error(
            data.error || "Unable to cancel the current trip."
        );
    }

    clearPendingThread();
}


function clearTripUI() {
    document.getElementById("userInput").value = "";
    document.getElementById("resultSection").classList.add("hidden");

    latestAnswerMarkdown = "";
    hideError();
}


async function newTrip() {
    setLoading(true);

    try {
        // Cancel the previous pending session before resetting UI.
        await cancelPendingSession();

        clearPendingThread();
        clearTripUI();

        document.getElementById("userInput").focus();

    } catch (error) {
        showError(error.message);

    } finally {
        setLoading(false);
    }
}


async function cancelTrip() {
    // Reuse the same cancellation semantics.
    // A cancelled trip is no longer resumed by the client.
    await newTrip();
}


// Initialize button visibility after the DOM has loaded.
syncSessionControls();


function rememberPendingSession(threadId, status) {
    pendingThreadId = threadId;
    pendingStatus = status;

    // Restore the correct action after a browser refresh.
    localStorage.setItem("pending_travel_thread_id", threadId);
    localStorage.setItem("pending_travel_status", status);

    syncSessionControls();
}


function showPrePlanMessage(text, threadId) {
    // Intermediate responses are not completed travel plans.
    latestAnswerMarkdown = "";

    const section = document.getElementById("resultSection");
    const resultBox = document.getElementById("resultBox");
    const threadInfo = document.getElementById("threadInfo");

    // Use textContent: no user-provided trip field is parsed as HTML.
    resultBox.textContent = text;
    resultBox.style.whiteSpace = "pre-line";

    threadInfo.textContent = `Thread ID: ${threadId}`;

    // Copy/PDF are intended for completed plans.
    document.querySelector(".result-actions")
        .classList.add("hidden");

    document.getElementById("tripBriefActions")
        .classList.add("hidden");

    section.classList.remove("hidden");
}


function showTripBrief(brief, threadId) {
    const budget = brief.budget;

    const budgetLabel = budget
        ? `${budget.amount} ${budget.currency} (${budget.scope})`
        : "Not specified";

    const lines = [
        "TRIP BRIEF",
        "",
        `Destination: ${brief.destination || "Not specified"}`,
        `Origin: ${brief.origin || "Not specified"}`,
        `Duration: ${brief.duration_days ?? "Not specified"} days`,
        `Travel period: ${brief.travel_period || "Not specified"}`,
        `Travelers: ${brief.travelers ?? "Not specified"}`,
        `Budget: ${budgetLabel}`,
        `Preferences: ${brief.preferences.join(", ") || "None specified"}`,
        `Research: ${brief.capabilities.join(", ")}`,
        "",
        "Review the details before generating your plan."
    ];

    showPrePlanMessage(
        lines.join("\n"),
        threadId
    );

    document.getElementById("tripBriefActions")
        .classList.remove("hidden");

    document.getElementById("resultSection").scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}



function handleTravelResponse(data) {

    // ---------------------------------------------
    // More travel information is required.
    // ---------------------------------------------
    if (data.status === "requires_input") {
        rememberPendingSession(
            data.thread_id,
            data.status
        );

        showPrePlanMessage(
            data.answer,
            data.thread_id
        );

        return;
    }

    // ---------------------------------------------
    // Trip context is ready, but not approved yet.
    // ---------------------------------------------
    if (data.status === "requires_confirmation") {
        if (!data.brief) {
            throw new Error("Trip brief is missing from the response.");
        }

        rememberPendingSession(
            data.thread_id,
            data.status
        );

        showTripBrief(
            data.brief,
            data.thread_id
        );

        return;
    }

    // ---------------------------------------------
    // User approved and generation completed.
    // ---------------------------------------------
    if (data.status === "completed") {
        clearPendingThread();

        document.getElementById("tripBriefActions")
            .classList.add("hidden");

        document.querySelector(".result-actions")
            .classList.remove("hidden");

        document.getElementById("resultBox")
            .style.whiteSpace = "";

        // Reuse the existing final-result renderer.
        showResult(
            data.answer,
            data.thread_id
        );

        return;
    }

    throw new Error(
        `Unexpected workflow status: ${data.status}`
    );
}


async function postTravelAction(payload) {
    const response = await fetch("/api/travel", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.status === 409) {
        // An invalid/stale session must not be silently resumed.
        clearPendingThread();
    }

    if (!response.ok || !data.success) {
        throw new Error(
            data.error || "Unable to process the travel request."
        );
    }

    return data;
}


async function buildPlan() {
    // BUILD is valid only at the confirmation stage.
    if (
        !pendingThreadId ||
        pendingStatus !== "requires_confirmation"
    ) {
        showError("No trip is awaiting confirmation.");
        return;
    }

    hideError();
    setLoading(true);

    try {
        const data = await postTravelAction({
            action: "build",
            thread_id: pendingThreadId
        });

        // This may return completed, or requires_input
        // if a later execution validation needs clarification.
        handleTravelResponse(data);

    } catch (error) {
        showError(
            error.message || "Unable to build the plan."
        );

    } finally {
        setLoading(false);
    }
}


function editTripBrief() {
    if (pendingStatus !== "requires_confirmation") {
        return;
    }

    const input = document.getElementById("userInput");

    // The next textarea submission will use action="edit".
    input.placeholder =
        "Tell me what you want to change in your trip...";

    input.focus();
    input.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
}
