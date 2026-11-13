// A thread is persisted only while LangGraph is
// waiting for clarification from the user.
let pendingThreadId =
    localStorage.getItem(
        "pending_travel_thread_id"
    ) || null;

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
    const sendBtn = document.getElementById("sendBtn");
    const btnText = document.getElementById("btnText");
    const btnLoader = document.getElementById("btnLoader");

    sendBtn.disabled = isLoading;

    // Prevent competing session actions while a request is running.
    document.getElementById("newTripBtn").disabled = isLoading;
    document.getElementById("cancelTripBtn").disabled = isLoading;

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
    // Prevent duplicate requests while an API call is running.
    const sendBtn = document.getElementById("sendBtn");

    if (sendBtn.disabled) {
        return;
    }

    hideError();

    const input = document.getElementById("userInput");
    const message = input.value.trim();

    if (!message) {
        showError("Please enter your travel request first.");
        return;
    }

    // A pending thread means the user is answering a
    // clarification. Otherwise, this is a new trip.
    const action = pendingThreadId ? "reply" : "start";

    setLoading(true);

    try {
        const response = await fetch("/api/travel", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                action: action,
                message: message,

                // START sends null; REPLY sends the existing ID.
                thread_id: pendingThreadId
            })
        });

        const data = await response.json();

        // ---------------------------------------------
        // 409 Conflict: the session can no longer resume.
        // ---------------------------------------------
        if (response.status === 409) {
            // Clear the stale client reference.
            // Never retry this message automatically as START.
            clearPendingThread();

            throw new Error(
                data.error ||
                "This trip session is no longer active. Please start a new trip."
            );
        }

        // ---------------------------------------------
        // Handle other API errors.
        // ---------------------------------------------
        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Something went wrong."
            );
        }

        // ---------------------------------------------
        // LangGraph is waiting for clarification.
        // ---------------------------------------------
        if (data.status === "requires_input") {
            // Preserve the same thread for the next message.
            pendingThreadId = data.thread_id;

            localStorage.setItem(
                "pending_travel_thread_id",
                pendingThreadId
            );

            syncSessionControls();
        }

        // ---------------------------------------------
        // Travel workflow has completed.
        // ---------------------------------------------
        else if (data.status === "completed") {
            // Completed threads should not be resumed.
            clearPendingThread();
        }

        // ---------------------------------------------
        // Unexpected successful status.
        // ---------------------------------------------
        else {
            throw new Error(
                `Unexpected workflow status: ${data.status}`
            );
        }

        // Display the clarification question or final plan.
        showResult(
            data.answer,
            data.thread_id
        );

        // Clear the submitted message after successful handling.
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

    localStorage.removeItem("pending_travel_thread_id");

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
