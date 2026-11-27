const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const script = readFileSync(path.join(__dirname, "../static/script.js"), "utf8");
const storageKey = "travora_conversation_v1";
const firstThread = "trip_" + "a".repeat(32);
const nextThread = "trip_" + "b".repeat(32);

function createBrowser(storage = new Map()) {
    function createElement() {
        const classes = new Set();
        return {
            disabled: false,
            style: {},
            value: "",
            classList: {
                add: (name) => classes.add(name),
                remove: (name) => classes.delete(name),
                contains: (name) => classes.has(name),
                toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name)
            },
            replaceChildren() {},
            append() {},
            appendChild() {},
            addEventListener() {},
            scrollIntoView() {},
            focus() {}
        };
    }

    const elements = new Map();
    function element(id) {
        if (!elements.has(id)) {
            elements.set(id, createElement());
        }
        return elements.get(id);
    }

    const requests = [];
    const responses = [];
    const context = vm.createContext({
        document: { getElementById: element, createElement },
        sessionStorage: {
            getItem: (key) => storage.get(key),
            setItem: (key, value) => storage.set(key, value)
        },
        fetch: async (url, options) => {
            assert.equal(url, "/api/travel");
            requests.push(JSON.parse(options.body));
            const response = responses.shift();
            assert.ok(response, "Unexpected request");
            return response;
        }
    });
    vm.runInContext(script, context);

    return {
        element,
        requests,
        run: (expression) => vm.runInContext(expression, context),
        respond(body) {
            responses.push({ ok: true, json: async () => ({ success: true, ...body }) });
        },
        snapshot: () => JSON.parse(storage.get(storageKey))
    };
}

for (const { label, message, answer, travelMessage } of [
    {
        label: "scope reply",
        message: "Who invented Python?",
        answer: "I can help with travel planning.",
        travelMessage: "Plan a trip to Rome."
    },
    {
        label: "greeting",
        message: "Hi",
        answer: "Hi! I can help you plan a trip. Where would you like to go?",
        travelMessage: "Hi, plan a trip to London."
    }
]) {
    test(`${label} preserves history across refresh and permits a fresh START`, async () => {
        const storage = new Map();
        const browser = createBrowser(storage);
        browser.respond({
            status: "completed", response_type: "message", thread_id: firstThread,
            answer
        });
        browser.element("userInput").value = message;
        await browser.run("sendMessage()");

        const snapshot = browser.snapshot();
        assert.equal(snapshot.threadId, null);
        assert.equal(snapshot.messages[1].content, answer);
        assert.equal(browser.element("userInput").disabled, false);
        assert.equal(browser.element("resultSection").classList.contains("hidden"), true);
        assert.equal(browser.element("copyBtn").disabled, true);
        assert.equal(browser.element("downloadBtn").disabled, true);

        const refreshed = createBrowser(storage);
        refreshed.respond({
            status: "requires_input", response_type: "clarification", thread_id: nextThread,
            answer: "When would you like to travel?"
        });
        refreshed.element("userInput").value = travelMessage;
        await refreshed.run("sendMessage()");

        assert.deepEqual(refreshed.requests, [{ action: "start", message: travelMessage }]);
        assert.deepEqual(refreshed.snapshot().messages.slice(0, 2), snapshot.messages);
        assert.equal(refreshed.snapshot().threadId, nextThread);
        assert.equal(refreshed.snapshot().status, "requires_input");
    });
}

test("BUILD displays and enables export for an itinerary-only travel result", async () => {
    const storage = new Map([[storageKey, JSON.stringify({
        status: "requires_confirmation", threadId: firstThread, messages: [],
        brief: { destination: "Rome" }
    })]]);
    const browser = createBrowser(storage);
    assert.equal(browser.element("buildPlanBtn").disabled, false);
    assert.equal(browser.element("tripBriefSection").classList.contains("hidden"), false);

    browser.respond({
        status: "completed", response_type: "travel_result", thread_id: firstThread,
        answer: "Three days in Rome", flight_results: "", hotel_results: "",
        activity_results: ""
    });
    await browser.run("buildPlan()");

    assert.deepEqual(browser.requests, [{ action: "build", thread_id: firstThread }]);
    assert.equal(browser.element("resultSection").classList.contains("hidden"), false);
    assert.equal(browser.element("resultBox").textContent, "Three days in Rome");
    assert.equal(browser.element("copyBtn").disabled, false);
    assert.equal(browser.element("downloadBtn").disabled, false);
    assert.equal(browser.element("userInput").disabled, true);
});

test("wrong-thread resume keeps the pending session blocked, including after refresh", async () => {
    const storage = new Map([[storageKey, JSON.stringify({
        status: "requires_confirmation", responseType: "trip_brief",
        threadId: firstThread, messages: [], brief: { destination: "Rome" }
    })]]);
    const browser = createBrowser(storage);
    browser.respond({
        status: "requires_confirmation", response_type: "trip_brief", thread_id: nextThread,
        brief: { destination: "Paris" }, answer: "Review this trip."
    });
    browser.element("userInput").value = "Change the destination to Paris.";
    await browser.run("sendMessage()");

    assert.equal(browser.snapshot().threadId, firstThread);
    assert.equal(browser.snapshot().brief.destination, "Rome");
    assert.equal(browser.snapshot().blocked, true);
    assert.match(browser.element("errorBox").textContent, /Unexpected session change/);
    assert.equal(browser.element("buildPlanBtn").disabled, true);

    const refreshed = createBrowser(storage);
    assert.equal(refreshed.element("buildPlanBtn").disabled, true);
    await refreshed.run("buildPlan()");
    assert.deepEqual(refreshed.requests, []);
});

test("CANCEL still clears the active session after a typed cancellation", async () => {
    const storage = new Map([[storageKey, JSON.stringify({
        status: "requires_input", responseType: "clarification",
        threadId: firstThread, messages: []
    })]]);
    const browser = createBrowser(storage);
    browser.respond({
        status: "cancelled", response_type: "message", thread_id: firstThread,
        answer: "Trip planning cancelled."
    });

    await browser.run("newTrip()");

    assert.deepEqual(browser.requests, [{ action: "cancel", thread_id: firstThread }]);
    assert.equal(browser.snapshot().threadId, null);
    assert.equal(browser.snapshot().status, "idle");
    assert.equal(browser.element("userInput").disabled, false);
});

test("legacy completed snapshots keep chat history with export disabled", () => {
    const messages = [{ role: "user", content: "Plan a trip to Rome." }];
    const storage = new Map([[storageKey, JSON.stringify({
        status: "completed", threadId: firstThread, messages, answer: "Ambiguous old answer"
    })]]);
    const browser = createBrowser(storage);

    assert.deepEqual(JSON.parse(browser.run("JSON.stringify(state.messages)")), messages);
    assert.equal(browser.run("state.threadId"), null);
    assert.equal(browser.element("userInput").disabled, false);
    assert.equal(browser.element("resultSection").classList.contains("hidden"), true);
    assert.equal(browser.element("copyBtn").disabled, true);
    assert.equal(browser.element("downloadBtn").disabled, true);
});
