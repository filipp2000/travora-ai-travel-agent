# Travora development

<a id="baseline"></a>

## Current baseline and actionable roadmap item

| Item | Status |
|---|---|
| Repository | `filipp2000/travora-ai-travel-agent`. The audited local working directory and Git root were the same checkout, named `TravelAgent`. |
| Audit snapshot | 27 November 2026, `feature/conversational-trip-planning` at `ddc43e0b070cb3d3c151e324293670e24a9477c9`. The local `origin/feature/conversational-trip-planning` tracking ref matched with `+0/-0`. Local `main` and `origin/main` were at `7fe0917`, 11 feature commits behind. No live remote or deployment was queried. |
| Working tree at audit | Only an unstaged `.gitignore` entry for the temporary `TRAVORA_PRODUCTION_HANDOVER.md`. The handover was ignored and untracked. No staged or uncommitted application changes. The consolidation adds the three permanent documentation files only. |
| Last roadmap item with reported functional acceptance | **1E**, committed in `3f6b080`, `83a49a2` and `b2f93f1`. The developer reported integration and real LangSmith smoke success. The current audit verified source and offline paths, including the remaining technical-clarification reapproval gap. |
| Conversational UI baseline | **1F.1**, chat-first UI at `ddc43e0` (26 November 2026). At that baseline, scope replies rendered as travel results. Full UI acceptance is open. |
| Current actionable roadmap item | **1F.1a**, Conversational Response Handling, a corrective sub-increment of **1F.1** within milestone **1F**. Checkpoints 1–3 are committed in `eb529df`. The developer confirmed the greeting behavior in the browser and authorized publication to the feature branch. Broader development verification remains open. See the [implementation tasks and regression matrix](#c7). |
| Current verification | 112 offline Pytest cases, six Node UI regressions and two previous-source resume scenarios in memory. The developer reported that the mixed London request reached clarification and that the standalone greeting rendered correctly after a hard refresh. See [checkpoint evidence and limitations](#c7). |

Checkpoints 1–3 distinguish lifecycle completion from response content, preserve the current question or reviewed brief on unrelated input, and add standalone greeting intent. Explicit `BUILD` remains the only approval action. Review the current source for each affected path before editing. The agreed order after 1F.1a is 1F.1b UI refinement, 1F.2 reliability/E2E, then 1F.3 release readiness. The production boundary and broader roadmap remain unchanged. [Graph and approval paths](ARCHITECTURE.md#b4) · [Roadmap](#c3)

<a id="evidence"></a>

## Evidence vocabulary and source labels

- **Source verified (current)** means inspected in the audited Git checkout. **Executed offline** identifies a test or controlled probe actually run and states its boundaries.
- **Source verified (historical)** means inspected in an earlier uploaded source or archive and specific to that snapshot.
- **Reported implemented / verified** means the developer reported code, a commit, a test pass or a runtime observation. The report retains that provenance where the original execution was not independently repeated.
- **Observed** means supported by supplied UI screenshots, PDF, logs or state dumps in the historical record.
- **Agreed** means a design direction established in discussion. Its implementation can still be pending.
- **Proposed** means a suggested design or code without later confirmation. It requires approval before implementation.
- **Superseded** means replaced by a later implementation or decision. **Deferred** means intentionally postponed. **Unresolved** means a question or issue requiring verification or a decision.

The original handover cutoff was 26 November 2026, with the latest substantive chat-first review on 25 November. The S-labels below preserve the handover's record of its available historical sources. The local audit did not require a raw chat export or access to the original project.

| Label | Historical provenance |
|---|---|
| **S1** | Earlier uploaded loose files and initial tutorial discussion from 27 August 2026. |
| **S2** | `travora_code.zip`, including code, README and tests with files dated through 5 November 2026. |
| **S3** | Pasted historical graph-state dumps and parser/provider code. |
| **S4** | Available earlier project discussion and prior-session summary for 1A–1D. |
| **S5** | Visible historical 1D.2 debugging/commit and 1E implementation, evaluation and verification discussion. |
| **S6** | Visible historical 1F.1 implementation instructions, screenshots and guardrail review. |
| **S7** | Five-page `london-travel-plan.pdf` supplied for UI review. |

The early production review transcript was incomplete. See the [provenance inventory and verification gaps](#c8) for detailed limitations.

<a id="c1"></a>

## C1. Development history and evidence chronology

Dates in the chronology distinguish Git commit dates from conversation and snapshot dates. Source and Git evidence fill the checkout gaps from the handover. Early conversation context was summarized, and some pre-1A subphase names, dates and rationale remain unrecoverable. See [evidence and provenance](#evidence).

| Time / roadmap item | Changes and evidence | Status |
|---|---|---|
| By 27 Aug 2026 | Tutorial reproduced, minor frontend adjustments, GitHub uploaded, Render deployment reported live. User asks how to grow into production app, README demo link discussion. Uvicorn `0.0.0.0` vs browser `127.0.0.1` explained. | Reported complete, S1/S4 |
| From 4 Sep 2026 | Production architecture review. Move toward typed domain requests, validation, deterministic routing, selective external calls, graph persistence, structured testing, reliability and real product experience. | Early transcript partial, S1–S4 |
| Sep–Oct historical source | Capability-specific workflow with `itinerary_node` and `final_response_node`, parallel branch join, typed request and request policy. Split location resolution and validate IATA rather than default origin/LLM guessing. | Source verified loose files, superseded in part |
| Historical graph dumps | One older state had 41 messages with unrelated prior trips/queries (Italy, Japan, Rome, Spain, Milan). Latest query hotel-only Milan USD120/night. Parsed caps hotels, ready true, hotel_results only. Demonstrates accumulation and focused routing, not proof of exact old bug cause. | Observed S3 |
| By 5 Nov snapshot | Single synthesis replacing itinerary/final sequence, scope guardrails, typed HTTP input, pool, independent threads and active interrupt resume, README documents architecture. 1A models/service present but not yet wired in graph. | Source verified S2 |
| Environment isolation | Dev feature branch, Neon dev/prod separation, local LangSmith project. All nine checks reported successful. No production deploy until full Release 1. | Reported verified S4 |
| 1A | Typed context/update/merge, five tests, committed. | Current source and commit `b0238b3` verified. S2 supports the initial implementation. |
| 1B | Unified `extract_trip_turn`, `TripTurn`, capabilities merge, adapter and parser evaluation. Null preference arrays fixed. | Current source and commit `2e0ba74` verified. Live extraction is historical developer-reported evidence (S4). |
| 1C | Deterministic readiness and targeted question service, ten tests. Test directory cleanup. | Current source and commits `b7fec98` / `9185e44` verified. |
| 1D.1 | Multi-turn LangGraph clarification loop and persistent resume. Safe serializer allowlist. Real trace and warnings fixed. | Current wiring and serializer verified. Real trace and warning resolution developer-reported (S4). |
| 1D.2 | Explicit START/REPLY/CANCEL, logical cancellation, validation/error handling, frontend controls, lifecycle tests. | Current source and commits `02e553a`, `922a435` and `1169860` verified. Manual checks developer-reported (S5). |
| 1E (by 25 Nov) | Trip brief deterministic projection, approval interrupt and BUILD/EDIT, session phase checks, temporary frontend actions, tests/trace. Indentation bug fixed. Developer confirms all integration tests passed and commits to dev branch. | Committed at `3f6b080`, `83a49a2` and `b2f93f1` on 24 November. Historical integration and trace checks developer-reported (S5/S6). |
| 1F.1 (25 Nov) | Chat-first interface, dual panels, sessionStorage state, sanitized result, Copy/PDF. London happy path and known scope rendering issue shown in screenshots. | Committed at `ddc43e0` on 26 November. S6/S7 record partial acceptance evidence and an open semantic bug. |
| 1F.1a (response semantics discussion) | Response type separation, GREETING intent and context-aware guardrails proposed. | Corrective sub-increment of 1F.1. Contract and implementation pending. |
| 26 Nov 2026 | User requests a comprehensive handover to Codex. | Original handover cutoff. |
| 27 Nov 2026 | Read-only repository audit against `ddc43e0`. | Current source and Git verification, 87 offline tests passed and controlled application graph/frontend probes. |

<a id="c2"></a>

## C2. Detailed implemented increments

<a id="c2-1"></a>

### C2.1 Pre-conversation refactors and technical findings

Initial tutorial was useful for learning but not production-grade. Problems addressed or identified: unnecessary LLM stages, execution of irrelevant capabilities, inconsistent extraction/validation, raw route text reparsing and guessed origin, implicit/global thread reuse, long-lived DB connection, fragile clarification, raw exceptions, minimal frontend and no evaluation baseline. The source sequence shows capability routing and then single synthesis, rather than a big-bang rewrite. The exact names of early roadmap phases and whether every early recommendation was implemented need historical chat/Git recovery.

Historical provider code included `DEFAULT_ORIGIN_IATA=ATH`, location aliases, raw `parse_route` and fallback. Refactor moved airport resolution into service, activated `search_flights_by_route` with validated IATA, kept legacy helper for compatibility. "My city" must trigger clarification rather than default Athens. Country-to-main-airport policy still accepted in earlier tests (Greece→ATH, Japan→NRT, etc.). Later destination specificity concern is not resolved by resolver success.

S2 graph already guards out-of-scope and unclear. Old parser checks missing intent and explicitly clears capabilities. This prevents unrelated requests from reaching provider nodes, but does not distinguish greetings. S2 `TravelRequestBody` has length/control/thread validation, message required. Later explicit actions supersede that contract. `app.py` raw exceptions corrected in 1D.2.

Source S3 graph dumps show prior message history persisted across independent requests. Do not reproduce those raw traces into the repo. For latest Milan request, parsed only hotels, ready true and no flight/activity results. This supports the earlier shift to scoped capabilities. The old history is a concrete reason to preserve independent thread isolation. The exact causal sequence of old bug fixes beyond this evidence is unknown.

<a id="c2-2"></a>

### C2.2 1A — Typed trip context and deterministic merge

Introduce `BudgetScope`, `TripContext`, `TripContextUpdate`, `merge_trip_context`. Keep domain state independent of LLM output format. Merge only explicit corrections. Preserve prior origin/destination/duration/etc.. Dates mode replacement. Case-insensitive preference remove/add. Validate merged state. Five tests: accumulation, replace one field, preference add/remove, exact dates replace month, missing fields do not clear. Reported committed. Initial S2 `TripContextUpdate` lacked capabilities. Later 1B adds them. Do not overwrite later version with S2.

<a id="c2-3"></a>

### C2.3 1B — Structured conversational understanding

`extract_trip_turn` replaces old parser in `llm/request_parser.py`, returns typed `TripTurn(intent,update)`. Context in state, deterministic adapter `to_travel_request`, policy preserved, graph execution behavior initially unchanged. Real two-turn evaluation: Netherlands 5 days EUR1200 total, then Athens solo December 2026. User reports correct extraction. Provider emitted `add_preferences:null`, `remove_preferences:null`. Normalize only null to arrays using before field validator and prompt, test regression. All tests/smoke reported passed. No LLM-generated full state replacement. `evaluations/inspect_trip_turns.py` real Groq evaluation (JSON dumps of updates/context). Not a formal dataset or automated offline test.

<a id="c2-4"></a>

### C2.4 1C — Trip readiness and targeted clarification

Introduce `TripReadiness`, `ReadinessIssue`, deterministic `assess_trip_readiness(context,today=...)` and `build_targeted_question(max_questions=2)`. Ten tests reported passing. Readiness depends on capability-specific requirements, checks dates/past dates/end without start/year missing, budget optional. Do not confuse exact period/flexible dates with provider inventory. See [domain and readiness](ARCHITECTURE.md#b5) for current edge cases. Test cleanup: moved `validation/request_check.py` to `services/request_validation.py`. moved/merged tests into `tests/`, removed `validation/`, `evaluations/` for real LLM inspection. The earlier reported Pytest configuration `testpaths=["tests"]` and `addopts="-ra"` is absent from the current `pyproject.toml`. The audit passed the tests path explicitly. Use fixed `today` for deterministic tests. User preferred simple file moves rather than unnecessary git-specific mechanics.

<a id="c2-5"></a>

### C2.5 1D.1 — Persistent multi-turn graph

Add `assess_trip_readiness`, `ask_trip_details` interrupt and loop to extraction, `trip_context`, `trip_readiness`, `pending_question`. `route_after_understanding` handles initial nontravel and pending clarification differently. Preserve legacy `clarify_request` for technical airport resolution. No research until requirements ready (explicit approval added later). Real example START "Plan a 5-day trip to France from Athens under $2000" → missing period/travelers → REPLY "Two people, in May 2027." → readiness → flight/hotel parallel → join → generate, same thread. Summary reports approximate first trace 1802 tokens/$0.0006, second 6389 tokens/$0.0023. These are historic observations, not benchmark guarantees. User confirmed real trace and checkpoint serialization warning resolved via explicit allowlist ([persistence design](ARCHITECTURE.md#b7)). Added `tests/test_workflow_conversation.py` with InMemorySaver, partial real nodes, mocked LLM. At that point UI still single textarea/result. Acceptable temporary milestone. 1E supersedes direct ready→check path.

<a id="c2-6"></a>

### C2.6 1D.2 — Explicit session lifecycle

Add `SessionAction.START/REPLY/CANCEL`, Pydantic `model_validator`, session service, persistent cancellation flag, no implicit fallback to new thread, 409 conflict/generic 500, New/Cancel controls and localStorage pending state. `require_pending_session` checks checkpoint validity. `cancel_pending_session` updates marker and is idempotent. No delete SQL because pinned postgres saver version differs from newer API. No need to upgrade dependency simply to implement cancellation. Keep checkpoints for history, retention deferred.

Debug history:

- User showed `travel_planner()` with unconditional `request_data.message.strip()`. CANCEL legitimately has None. Would raise AttributeError and return 500. Remove redundant strip/400 and trust Pydantic validation. No need to alter graph logic.
- `test_valid_travel_input_is_accepted` failed (`action Field required`), 72 passed/1 failed. Old test must specify `SessionAction.START`, preserve whitespace normalization assertion, no thread ID. Do not default action to START to satisfy old test. Expected 73 passed after correction. Exact full rerun count not shown, later user reports all worked.
- Manual Swagger CANCEL initially malformed JSON (`"thread_id": trip_..."`, missing opening quote) → 422 `json_invalid`, `JSON decode error`, `Expecting value`. No workflow executed. Corrected quoting. Do not mistake parse error for session validation.
- User subsequently reports all lifecycle behavior as expected. Manual sequence START incomplete Italy from Athens 5 days EUR1500 → requires_input, CANCEL same thread → cancelled, REPLY same → 409, START Japan from Thessaloniki → different ID. Bonus active REPLY normal flow proposed. Restart persistence/idempotent repeated CANCEL/unknown/completed edge cases should be verified explicitly if not already recorded. No direct evidence of every restart test.

Git status showed modifications to `app.py`, `backend.py`, `pydantic_models/api_request.py`, `static/script.js`, `static/style.css`, `templates/index.html`, `tests/test_input_guardrails.py`, `tests/test_workflow_routing.py`, `workflow/nodes.py`, `workflow/routing.py`, `workflow/state.py`. Untracked `services/session_lifecycle.py`, `tests/test_api_input.py`, `tests/test_session_lifecycle.py`, `tests/test_workflow_conversation.py`. Suggested two commits: `Implement conversational workflow and session lifecycle` (backend/tests), `Add frontend controls for travel session management` (frontend). Git records `02e553a` for the workflow/API, `922a435` for the tests and `1169860` for the frontend, all on 14 November 2026. Both API and input-guardrail test files exist in screenshot despite earlier cleanup plan. Check overlap and retain distinct coverage.

<a id="c2-7"></a>

### C2.7 1E — Trip brief confirmation and Build Plan gate

Purpose: readiness means enough data, not consent to spend provider/LLM resources. Add BUILD and EDIT to request contract, deterministic `build_trip_brief`, state `brief_decision`, `present_trip_brief_node`, `route_after_brief_decision`, change ready route to confirmation. Use `expected_interrupt_types` in session service. Reply only clarification, build/edit only trip_brief. `run_travel_agent` uses typed action and structured resume payload, `_get_interrupt_payload` instead of question-only, `requires_confirmation` status and `brief` in HTTP response. CANCEL valid while pending brief. EDIT reuses parser/context merge/readiness. No second approval LLM. Build not permitted before readiness. Legacy location validation after build remains a risk if it changes data without new confirmation.

Temporary frontend: show plain-text brief, Edit focuses input, text submit maps edit at confirmation, Build explicit action. Keep pending status in localStorage, disable competing buttons. `postTravelAction`, `handleTravelResponse` shared helpers. Copy/PDF only on completed status (later found semantic bug). Superseded by 1F.1 state-driven implementation. User asked full `setLoading`. Proposed loop over send/new/cancel/build/edit buttons with defensive missing DOM guard, later replaced by renderControls.

Tests provided file-by-file: `test_trip_brief.py` (2), `test_api_input.py` (13), `test_session_lifecycle.py` (12), `test_workflow_conversation.py` (3), update `test_workflow_routing.py` ready route. 30 expected cases for four named files (not entire suite). See [test coverage and evidence](#c4). `test_api_input.py` actual first run: 7 passed, 6 failed, all cross-field invalid payloads accepted (`DID NOT RAISE ValidationError`). Valid actions, empty message, unknown action passed. Cause confirmed: `validate_session_action()` was outside `TravelRequestBody` due to indentation. Move it inside class with `@model_validator(mode="after")`. Do not weaken negative tests. This bug recurred from earlier validator placement concern, worth retaining regression tests. User confirms all integration tests passed, real LangSmith trace matches expected, commits made on dev branch `origin/feature/conversational-trip-planning`. Suggested commit messages: `Implement human approval gate for trip planning`, `Add trip brief confirmation controls to frontend`. Git records `3f6b080` `Implement trip brief feature`, `83a49a2` `Add trip brief confirmation controls to frontend` and `b2f93f1` `Add trip brief implementation testing`.

Expected actual trace: first incomplete request→ask_trip_details. reply→ready→present_trip_brief. edit→understand/assess→updated brief. build→check→flight/hotel→join→generate. No provider or synthesis in first three turns. Negative BUILD before readiness and REPLY at brief should be 409. Latest user report confirms expected real trace but no raw 1E trace attached in available context.

<a id="c2-8"></a>

### C2.8 1F.1 — Committed chat-first UI, acceptance open

Replace one result box with left chat and right trip panel, state snapshot in `sessionStorage`, explicit action handling, uncertain-request blocking, sanitized Markdown, safe text rendering, copy/PDF, responsive dark theme. Commit `ddc43e0` updates `templates/index.html`, `static/style.css` and `static/script.js`. It keeps the 1E response contract. Full JS replacement to remove overlapping 1D/1E helpers. UI design inspired by earlier Layla-like reference images, not a clone. No React/maps/booking cards now. No claim screenshots prove all manual acceptance criteria.

Observed screenshot progression (S6):

1. `ui_step_1.png`: idle state, welcome, composer with "Hi, give me a 5 day trip plan to London from Athens under 2500 euros", right empty state.
2. `ui_step_2.png`: user message and deterministic question requesting dates and travelers, status collecting trip details, cancel/new controls. Right empty state.
3. `ui_step_3.png`: "Two travelers, in February 1st 2027.". Awaiting confirmation. Right London, Athens, 5 days, 2027-02-01, 2 travelers, 2500 EUR total, preferences not specified, flights/hotels/itinerary. Build/Edit visible.
4. `ui_step_4.png`: edit "Actually, make it 7 days and increase the total budget to 4000 euros.". Brief updated to 7 days/EUR4000, prior origin/date/travelers retained. Chat scroll shows previous and new messages, fresh confirmation.
5. `input_guardrail_issue.png`: initial Hi results in status Travel request completed, false plan-ready chat bubble, right pane scope refusal text, Copy/PDF visible, composer disabled. See [the proposal](ARCHITECTURE.md#b12). This is latest active issue, user explicitly requested design discussion first, not implementation.
6. `london-travel-plan.pdf`: five-page result, evidence of generated plan/export but date mismatch and formatting concerns. See [known issues](#c5) and [provider grounding](ARCHITECTURE.md#b8). No screenshot of final plan pane itself supplied in this latest set.

Git now verifies `ddc43e0`, dated 26 November 2026, titled `Updated chat ui`, for all three frontend files. The handover had proposed a different commit title and recorded incomplete acceptance. The audit found the UI in the committed tree, with the temporary handover ignore entry as the sole local diff. The scope bug is reproducible with controlled nontravel classification and the committed JS. Browser, export and other acceptance scenarios remain open.

<a id="c3"></a>

## C3. Recovered production roadmap (not a replacement roadmap)

The latest agreed sequence is Release 1 conversational planning, followed by Release 2 draft/revision and Release 3 grounded structured travel results/provider improvements. The earlier broad production areas remain relevant, but exact original numbering prior to 1A and final scheduling beyond Release 1 are not available. The following preserves the latest ordering and explicitly distinguishes future topics without pretending they have a committed sprint allocation.

**Confirmed hierarchy.** Release 1 contains milestone **1F**, split into increments **1F.1**, **1F.2** and **1F.3**. The guardrail review added **1F.1a** and **1F.1b** before closing UI acceptance. The developer confirmed **1F.1a** as a corrective sub-increment under **1F.1**. The [implementation tasks](#c7) are the individual steps within **1F.1a**.

**Inferred and unconfirmed classifications.** The placement of **1F.1b** as a sub-increment of **1F.1** follows its numbering and the recorded UI closure sequence. The **1D.1** and **1D.2** identifiers suggest a **1D** grouping. The available record establishes no independent **1D** objective or acceptance status. **1A**, **1B**, **1C** and **1E** retain their documented Release 1 placement and objectives. C2 describes implemented increments, but the available record does not consistently establish the original formal level of these earlier items.

| Roadmap item | Level / parent | Objective | State / dependency |
|---|---|---|---|
| Tutorial baseline | Historical phase | Reproduce, understand, run, publish/demo | Complete |
| Early production refactor | Historical phase | Typed understanding, deterministic rules, selective graph, parallel research, single synthesis, DB lifecycle and basic guardrails | Historical code verifies main changes |
| Environment isolation | Historical work | Protect Render production. Local branch with dev Neon/LangSmith | Reported complete |
| Release 1 | Release | Conversational planning | In progress. Release gates remain open. |
| 1A | Release 1 / formal level unconfirmed | Typed context and deterministic merging | Complete. Prerequisite to per-turn parsing |
| 1B | Release 1 / formal level unconfirmed | Unified intent + structured turn update | Complete. Prerequisite to readiness |
| 1C | Release 1 / formal level unconfirmed | Deterministic readiness and targeted clarification | Complete. Prerequisite to multi-turn graph |
| 1D.1 | Increment / inferred 1D grouping | Interrupt/resume with accumulated context | Complete. Prerequisite to explicit lifecycle |
| 1D.2 | Increment / inferred 1D grouping | Explicit START/REPLY/CANCEL, safe errors, tests | Complete. Prerequisite to phase-specific approval |
| 1E | Release 1 / formal level unconfirmed | Editable trip brief and explicit BUILD approval before research | Committed and source verified. Historical smoke reported. Reapproval gap remains in 1F.2. |
| 1F | Milestone / Release 1 | Conversational UI, reliability and release readiness through 1F.1–1F.3 | In progress. UI acceptance and release gates remain open. |
| 1F.1 | Increment / 1F | Conversational UI | Committed in `ddc43e0`. Partial historical smoke. Open acceptance depends on the corrective increments. |
| **1F.1a** | **Corrective sub-increment / 1F.1** | **Conversational Response Handling** | **Implemented and verified offline. Developer confirmed greeting rendering in the browser and authorized publication to the feature branch. Broader development smoke remains open.** |
| 1F.1b | Sub-increment / 1F.1 (inferred) | UI/UX refinement | Planned after semantics fixed. Exact styling decisions not yet agreed |
| 1F.2 | Increment / 1F | Reliability & E2E testing | Planned: regression, API/graph/browser correctness, provider/date/context, approval revalidation, security/concurrency |
| 1F.3 | Increment / 1F | Release readiness | Planned: docs, production checkpoint compatibility, regression/release gate, PR/merge/deploy when authorized |
| Release 2 | Release | Post-generation draft approval/revision and follow-up | Future. Current completed plan is terminal in UI. Exact feature scope and approval workflow not finalized. |
| Release 3 | Release | Grounded, structured travel outputs, pricing/provider reliability | Future. Immediate dangerous date/provider claims need handling in 1F.2 before release, not postponed wholesale to Release 3. |
| Supervisor / richer agent orchestration | Deferred topic | Evaluate only if specific measurable need arises | Deferred. No assumption multi-agent beats deterministic graph |

Merge to `main` remains gated on Release 1 readiness and explicit authorization.

### Planned production areas and rationale (not all scheduled to a specific increment)

| Area | Existing baseline | Intended direction / constraints |
|---|---|---|
| API design | FastAPI, Pydantic input, JSON response | Typed response semantics next. Predictable client/server errors, maintain API compatibility consciously |
| Persistence | Neon checkpoint state + bounded pool | Application-level saved trips/user/session records separate from graph checkpoints when needed. Retention and migrations. No invented schema yet |
| Memory | TripContext/checkpoints, temporary UI snapshot | Clarify short-term workflow vs long-term user preferences/history. No vector DB or long-term memory chosen by default |
| Async/concurrency | Synchronous graph and providers, parallel branch fanout | Avoid blocking async endpoint. Choose threadpool or async flow based on actual stack. Serialize per-thread actions/approval safely. Test concurrent users |
| Provider reliability | Basic errors/no-result texts, flight timeout | Explicit failures, timeouts, retries with backoff and limits, fallbacks, distinguish no data vs failed data. Caching only where useful. No provider swap agreed yet |
| Grounding & costs | Prompt instructions, estimates, unstructured results | Structured evidence, date-aware and scope-aware requests, trustworthy provider labels, deterministic arithmetic where possible, no unverified booking claims |
| Auth/rate limiting | No confirmed auth. Thread ID only | Ownership and access checks, request quotas/rate limiting, cost protection before real users. No final auth vendor/model selected |
| Security | Input schema and semantic guards, prompt instruction defense, DOM sanitization | Cross-layer injection tests, safe rendering/links, error redaction, secrets management, stale session handling, production access controls |
| Observability | LangSmith + exception logging | Structured logs, metrics, latency/error/LLM usage/cost tracking, monitoring and alerts. Smallest sensible stack first. No extra vendor agreed |
| Testing/evaluation | Pytest, mocked graph/service tests, manual real traces | Production-graph integration/API/browser E2E, reproducible semantic regression datasets, deterministic quality checks, LLM judge selectively. No formal pipeline or thresholds established |
| Docker/CI/CD | Dockerfile, Render/GitHub, uv lock | Reproducible builds, automated test/release checks, deployment verification and rollback. No CI workflow confirmed |
| Deployment/scaling | Render + Neon | Release gates, connection budgets, concurrent request handling, load testing, health/readiness, scaling strategy only when needed |

No detailed caching technology, authentication library, metrics stack, database schema, microservice split, load target or CI vendor was agreed in the available conversation. Preserve these as roadmap topics. Deployment remains gated on concrete evidence and approval.

<a id="c4"></a>

## C4. Tests, reported results and evaluation evidence

### Test inventory and responsibilities

S2 kept tests in `validation/`. The current checkout contains 11 Pytest modules in `tests/` and a separate live inspection script in `evaluations/`. The audit collected 87 cases. Both API model and input-guardrail files remain and have distinct coverage. The proposed Pytest configuration in the earlier conversation is absent from the current project declaration. [Tests](../tests/) · [Evaluation script](../evaluations/inspect_trip_turns.py)

| Current/expected file | Coverage and exact identifiers where known |
|---|---|
| `tests/test_input_guardrails.py` | Whitespace normalization with START, invalid input and invalid thread. The negative tests `test_invalid_input_is_rejected` and `test_invalid_thread_id_is_rejected` omit `action` and assert generic `ValidationError`. They do not isolate the field error. Focused offline checks supplied a valid action and verified the intended validation paths. |
| `tests/test_api_input.py` | `test_valid_session_actions` parameterized start/reply/cancel/build/edit. `test_invalid_session_actions` reply_without_thread, start_with_existing_thread, cancel_with_message, empty_message, unknown_action, build_without_thread, build_with_message, edit_without_message. 13 cases collected. |
| `tests/test_location_resolver.py` | `test_resolve_location_to_iata` parameterized valid IATA/city/country and unresolved input. Historical mapping tests should be revisited deliberately if product ambiguity rules change. |
| `tests/test_request_rules.py` | Reported merge of old `test_request_check.py` and `test_request_policy.py`. Hotel-only readiness, missing/unresolved origin, valid flight, end-to-end expansion, destination-only itinerary unchanged, hotel-only unchanged. Current source verified. |
| `tests/test_workflow_routing.py` | Merge of old capability/intent routing tests. Complete trip flight+hotel. With activities all branches. Itinerary-only direct synthesis. Hotel-only no flight. invalid→clarify. Initial out-of-scope/unclear no research. The ready→brief path is exercised by the conversational test graph. |
| `tests/test_trip_context.py` | Five original cases: accumulation, explicit correction, preference add/remove, exact dates replace month, missing fields preserve prior values. Five cases collected. |
| `tests/test_trip_turn_parser.py` | Nine cases for structured parsing, existing context and pending question, additive capabilities, policy, nontravel, empty input, null preference arrays and rejection of invalid preference types. |
| `tests/test_trip_readiness.py` | Ten deterministic cases with fixed dates, missing period/travelers, focused capabilities, flexibility, budget requirements, inconsistent/past dates and bounded question counts. Yearless month is implemented in the service. No dedicated yearless-month case is present. |
| `tests/test_session_lifecycle.py` | `FakeGraph` with exists/pending/interrupt_type, values, update_calls, SimpleNamespace tasks/interrupt.value. pending/unknown/completed, cancellation marker/idempotence/nonpending reject, matching/mismatching phase, cancel brief. 12 cases collected. |
| `tests/test_trip_brief.py` | `test_trip_brief_reflects_execution_capabilities`, `test_flexible_dates_do_not_generate_fake_dates`. Deterministic brief, total budget, effective caps and no invented dates/budget. 2 cases collected. |
| `tests/test_workflow_conversation.py` | `build_test_graph(llm)` with real conversational nodes/routing, `InMemorySaver`, fixed `TODAY=date(2026,11,10)`, `partial` injections. Stub check returns `{"final_answer":"READY"}`. `test_multi_turn_collection_preserves_context`, `test_edit_requires_new_brief_confirmation`, `test_out_of_scope_initial_request_finishes_without_collection`. 3 cases collected. |
| `evaluations/inspect_trip_turns.py` | Real LLM two-turn inspection and JSON context. Not offline deterministic Pytest. Replaces `validation/inspect_request_parser.py` command. |

The earlier chat examples and reported counts described the project at the time. The current audit ran all 87 collected tests. The conversational suite builds a partial replica using real conversational nodes, `InMemorySaver`, a fixed date and mocked structured output. Its stub `check_request` returns `{"final_answer":"READY"}`. It exercises collection/edit/BUILD boundaries and extraction call counts. Coverage of the production graph wiring, actual execution nodes, FastAPI transport and PostgreSQL is outside that test graph. A shared graph factory was discussed as a later possibility. It is not part of the current task.

**27 November 2026 offline audit.** Python 3.14.7 and Pytest 9.1.1 in the existing `.venv` collected and passed 87 cases, with 13 LangSmith deprecation warnings for `asyncio.iscoroutinefunction`. The audit used no bytecode writes, disabled dotenv, tracing, plugin autoload, cache, logging and tmpdir plugins, used Python stream capture (`--capture=sys`), and blocked network and file writes. The active invocation passed `tests` explicitly. No live evaluation script ran.

Separate transient probes exercised the application graph wiring, real API handler directly, configured serializer in `InMemorySaver` and mocked LLM, pool and providers. They reproduced initial nontravel completion, pending details re-ask, confirmation degradation after nontravel `EDIT`, wrong-phase 409, post-approval location change with execution, and lost date/scope provider inputs. A Node VM loaded committed `static/script.js` with DOM and storage stubs and confirmed false plan-ready output, enabled export, disabled composer and the stale thread-ID rejection. These were audit probes. The committed suite has no full ASGI transport, browser, PostgreSQL, or live-provider coverage. [Detailed current paths](ARCHITECTURE.md#b4)

### Commands and test results

- `uv run python -m pytest -v` full suite, `-q` short final run.
- `uv run python -m pytest tests/test_input_guardrails.py -v` after 1D.2 missing action failure.
- `uv run python -m pytest tests/test_api_input.py -v`: actual log from 1E collected 13, 7 passed/6 failed. Cross-field validator not registered because indentation placed function outside class. Fix confirmed by user, later passes reported. Do not infer exact count of subsequent full suite.
- `uv run python -m pytest tests/test_trip_brief.py tests/test_workflow_conversation.py tests/test_session_lifecycle.py tests/test_api_input.py -v`: provided focused integration/regression command. Individual files can run separately. Expected 30 cases for supplied versions only.
- Earlier parser evaluation command `uv run python -m validation.inspect_request_parser` from S2 obsolete. Current module `uv run python -m evaluations.inspect_trip_turns`. It calls Groq and is intended only for authorized live development checks.

### Real LLM/graph trace evidence

- 1B actual Groq extraction Netherlands, 5 days, EUR1200 total. Follow-up Athens, solo, December 2026. Prior details retained and normalized. Null arrays regression fixed.
- 1D.1 actual France request interrupted for period/travelers, resumed same checkpoint. Expected parallel branches and one final synthesis. Prior summary reports approximate tokens/cost (see [1D.1 history](#c2-5)). Serializer warning resolved.
- 1D.2 Swagger lifecycle reported works. Malformed JSON error was client syntax, not graph bug.
- 1E user explicitly reports all integration tests passed and real LangSmith trace as expected. No raw current trace IDs or exported screenshots available to cite exact token counts here.
- 1F.1 London screenshots demonstrate UI context/edit preservation and PDF export. Do not infer date correctness or provider availability from successful trace/response.

### Evaluation strategy and acceptance invariants

Prefer deterministic checks: schema validation, intent routing under mocked structured output, state merge, exact requirements, capability selection, date consistency, allowed session actions, unchanged context, no research before approval, no unintended LLM calls, output surface type and PDF visibility. Build datasets for real parser and synthesis cases with representative multi-turn corrections, ambiguities and off-topic messages. LLM-as-a-judge only when evaluating semantic relevance, helpfulness or itinerary quality not reducible to deterministic checks. No finalized dataset format, metric thresholds, evaluation pipeline or judge model confirmed. Track tokens, cost, latency, error and routing distributions as future observability/evaluation capabilities. Do not treat temperature zero or one successful sample as robust model performance.

<a id="c5"></a>

## C5. Known issues and technical debt register

Ordering below groups the issues by the current roadmap, not a new prioritization decision. The immediate issue is the conversational guardrail. provider/date mismatch and approval correctness are major release concerns. Do not let visual polish hide incorrect behavior.

| Issue | Evidence / reproduction | Expected direction / status |
|---|---|---|
| Initial Hi rendered as successful plan | S6 screenshot and offline API/JS probes with a mocked nontravel classification. Scope text in result panel, false plan-ready bubble, Copy/PDF enabled, composer disabled | Typed response, greeting reply and fresh START verified offline. The developer confirmed correct greeting rendering after a hard refresh. Broader browser and provider checks remain open. |
| Nontravel during pending question/brief | Offline application graph reproduced repeated details question and preserved domain context. A nontravel EDIT generated a confirmation brief with empty effective capabilities. The following BUILD ended in scope without research | Fixed in checkpoint 2 with application-graph/API regressions. Pending context, question or brief, and accepted synthesis input are preserved. |
| Stale UI after terminal conversation | `completed` disables composer. Thread mismatch check rejects fresh ID unless active thread cleared | Resolve with response semantics. Exact state transition not yet designed |
| UI scroll/layout polish | Native white scrollbar and differing panel heights visible, large whitespace. Synthetic welcome disappears | 1F.1b discussion. No finalized visual specification |
| Inaccurate trip dates | S7 page 1 shows 25 Nov 2026 flights and 1 Dec 2026 return, while the S6 approved start is 1 Feb 2027. Source and offline probe confirm that dates are lost at the execution adapter and the active flight query is route-only | 1F.2 date propagation and provider semantics. Describe flight status within the actual provider data scope |
| Duration/nights | S7 pages 2–4 state 7 nights but Day 7 departure. Ambiguity between days and nights | Explicit semantics and deterministic checks, no invented stay length. Unresolved |
| Flights not real fares/availability | S2 AviationStack status endpoint accepts route only, S7 suggests selecting/booking current flights | Label limitations, no unsupported future availability/price, provider redesign later |
| Budget scope/currency | Current and S2 hotel query assume per night. The audit sent an approved EUR 4000 total through the active path and observed `4000.0 EUR per night` in the mocked Tavily call. S7 reports `€400 USD (≈ €370)` and estimates | Preserve total/per-night scope and currency through execution and synthesis. Specific historical PDF attribution remains open |
| Estimated arithmetic | Earlier $514 vs $504 sum, user said $10 discrepancy nonblocker | Defer structured cost arithmetic. Semantic accuracy higher priority |
| Unspecified preferences | S6 brief preferences not specified, S7 museums/local cuisine preferences phrased as if provided | Investigate grounding/context inputs. Cause not proven |
| Country-to-city assumptions | France resolves CDG, Japan NRT, Italy FCO by policy | Clarify city/airport if material. No silent assumption. Readiness vs location validation review |
| Approval invalidation | Offline probe confirmed that legacy `clarify_request` after BUILD updates both models and routes directly through check to research without a new brief | Route through context/confirmation when material requirements change. 1F.2 |
| Raw vs effective capabilities | Current 1C readiness checks raw context capability set. A destination-only itinerary can satisfy its readiness without origin. Execution policy expands when both endpoints exist | Verify product intent and effective readiness, avoid overbroad policy changes |
| Incomplete update semantics | None means preserve, no clearing/removing capability. Conflicting date modes/end dates | Explicit semantics later. Do not solve incidentally in greeting fix |
| Research context | The current `to_travel_request()` drops dates, month, flexibility and budget scope. Synthesis uses the adapted request with the latest `user_query`, which is not updated by technical airport clarification | Ensure approved context reaches each relevant provider and synthesis in reliability work |
| Provider failures | Text strings for errors/no data, raw exception leak possibility, no retries/caching | Typed failure/evidence handling as needed, redaction and bounded I/O. Unresolved |
| Async blocking | Sync graph/provider call in async FastAPI endpoint | Threadpool or proper async architecture before scale. Unresolved |
| Session race | read/check/invoke/update not atomic. Multi-tab or concurrent requests | Per-thread concurrency/idempotency design and tests. Not solved by JS |
| Approval version/stale brief | BUILD references thread but not specific reviewed revision | Current blocked UI mitigates local case. Server-side approval correctness must be reviewed |
| Browser recovery | Blocked marker avoids unsafe retry, but lost response/START can orphan session. newTrip cancel failure may trap UI | Recovery endpoint/strategy deferred. No silent retries |
| Session ownership | Opaque UUID is not authentication | Auth/access control/rate limiting before real-user rollout. Design not selected |
| Checkpoint compatibility | Changed graph/schema, old pending production checkpoints | Explicit release migration/recovery plan. Do not blindly resume old states or delete data |
| Checkpoint retention | Logical cancellation/completion retain rows | Retention/cleanup policy not yet defined. No ad hoc SQL deletion |
| Rendering dependency | Historical rendering inserted raw Marked HTML. Current 1F.1 loads DOMPurify 3.5.0 and uses a plain-text fallback. Marked is unpinned | Browser XSS regression, verify scripts/pins and links, CSP/dependency review later |
| PDF rendering | S7 page 1→2 and 2→3 rows split. Day 6 page 4 overlapping label, earlier large blank areas | Visual export validation and layout cleanup, not primary semantic fix |
| Duplicate/outdated code/tests/docs | `validation/` was removed and still appears in README. The obsolete route helper, legacy flight parsing, empty `itinerary` field and unused local `app.TravelRequest` remain | Inspect live checkout, remove only after proving unused, preserve coverage. Cleanup after stable features |
| Observability and evaluation | LangSmith and tests only. No full metrics/CI/production eval pipeline | Incremental expansion. No benchmark claims |

<a id="c6"></a>

## C6. Manual smoke tests already specified and release acceptance

### 1D.2 session lifecycle

Use `/docs`, POST `/api/travel`, copy actual quoted thread IDs. Example sequence:

```json
{"action":"start","message":"Plan a 5-day trip to Italy from Athens with a total budget of 1500 EUR."}
```

Expected HTTP 200 `requires_input`, period/travelers question. Next `{"action":"cancel","thread_id":"trip_<actual hex>"}` → HTTP 200 cancelled (placeholder must be replaced with actual 32 hex). REPLY same thread `"Two people, in May 2027."` → HTTP 409. START Japan 7 days from Thessaloniki EUR3000 → new thread ID, independent context. Bonus normal REPLY active Japan with April 2027, two travelers. After 1E expect confirmation before completion. Verify cancellation survives server restart, idempotent cancel, unknown/completed rejection, no LLM research on cancel/rejected resume. User reports lifecycle working, individual persistence checks not fully evidenced.

### 1E explicit approval

1. START incomplete France/Athens 5 days USD2000 → requires_input.
2. REPLY same thread two travelers May 2027 → requires_confirmation, structured brief.
3. EDIT same thread make it seven days → requires_confirmation with new duration and all unchanged fields.
4. BUILD same thread, no message → execution, completed or further required technical clarification. No research in prior turns. No parser call on build.
5. Negative: BUILD while waiting trip_details → 409. REPLY while waiting trip_brief → 409. CANCEL pending brief works. Use fresh development thread after graph changes.

1E definition of done: readiness routes to brief, accurate effective caps/context, phase-specific BUILD, EDIT reconfirms, no research until approval, cancel works, tests green, local frontend flow. Committed and source verified. Historical live smoke developer-reported. The offline probe confirmed the post-approval technical clarification gap.

### 1F.1 local UI smoke

- Paris/Athens 5 days USD2000 → two travelers May 2027 → edit 7 days/USD2500 → BUILD. Chat retains turns, right panel updates, plan only after approval.
- Refresh at pending confirmation: restore same chat/brief/thread, BUILD allowed if no uncertain request. Reload during in-flight request should not enable stale approval.
- New Trip while pending Italy → cancel → start Japan independent. Cancel and new controls disabled during requests.
- Hotel-only Rome EUR120/night: short path to brief/build without unrelated flights.
- Out-of-scope "What is Generative AI?": no research, correct chat-only behavior desired, currently UI bug (also Hi).
- Copy/PDF works only for actual generated output. Check mobile viewport, browser console and safe rendering.

Definition of done originally ten UI checks: previous user/assistant messages visible. Right brief. EDIT updated. BUILD gated. New Trip independent. Refresh restoration. Controls disabled during request. Copy/PDF functional. Responsive mobile. No console errors. Screenshots cover only some. Guardrail bug added corrective increments before completion. PDF visible quality still imperfect. Backend suite should stay green if frontend-only changes, but response-contract fix will add/update tests.

### 1F.2/1F.3 release gates (agreed topics, detailed tests to be designed)

Resolve/verify graph/provider input correctness, renewed approval after changed requirements, safe output/claims, session concurrency and production security, API and UI E2E regressions, checkpoint migration and environment isolation, README and deployment documentation, test suite and trace verification. Only then prepare PR/merge and deployment to production with explicit user approval. Exact acceptance thresholds, rollback plan, production rollout strategy and CI wiring are unresolved. Do not fabricate them or label release ready now.

<a id="c7"></a>

## C7. 1F.1a implementation tasks — Conversational Response Handling

**Checkpoint 1 review evidence (27 November 2026).** The typed success response and UI transitions are implemented. The affected Pytest modules passed 48 cases. The full offline suite passed 96 cases with one Starlette test-client deprecation warning. The full command was `uv run --offline --locked --no-sync --no-cache python -m pytest -q -p no:cacheprovider tests` with dotenv and LangSmith tracing disabled and dummy provider configuration. The API tests exercise ASGI transport and the application graph with `InMemorySaver`, the configured serializer, mocked extraction and synthesis, and no PostgreSQL startup. `node --check static/script.js` and `node --test tests/test_response_ui.cjs` passed, with five DOM/storage stub regressions. Real browser behavior, PostgreSQL and live providers were outside this verification. Developer review gates checkpoint 2.

**Checkpoint 2 review evidence (27 November 2026).** After checkpoint 1 approval, added same-phase routing for unrelated details replies, unrelated edits and edits with unchanged trip context. ASGI regressions verify the preserved request and prompt through explicit `BUILD`, provider/synthesis calls only after approval, and a material edit that reopens details and produces a new brief. The affected modules passed 54 cases, the full offline Pytest command above passed 102 cases with the same Starlette warning, and the five Node regressions passed. A transient probe compiled the previous graph from `d228ded` and resumed both its pending clarification and brief with the current graph using a shared `InMemorySaver`. This verifies the tested in-memory resumes. PostgreSQL, real browser and live provider verification remain open. Developer review gates checkpoint 3.

**Checkpoint 3 review evidence (27 November 2026).** The developer approved checkpoint 2 and reported passing tests. Checkpoint 3 adds `GREETING` to the existing structured parser, a deterministic initial reply, and regressions for mixed travel input, both pending phases and a fresh START after refresh. The affected Pytest modules passed 73 cases, the full offline command above passed 112 cases with the same Starlette warning, and six Node DOM/storage stub regressions passed. The ASGI tests verify routing, the existing serializer and one structured invocation per turn using mocked model responses. Groq classification, Swagger/browser smoke and PostgreSQL verification require separate development authorization and remain open.

**Developer browser check (28 November 2026).** The developer reported that "Hi, plan a trip to London" entered trip clarification. The standalone "Hi" first produced the expected greeting in the result panel. A read-only check confirmed that the running local server served the updated script and exposed the typed OpenAPI response. After a hard refresh, the developer confirmed the expected greeting behavior and authorized publication to the feature branch. This is a targeted browser check. No raw provider trace, broader Swagger/browser matrix or PostgreSQL verification was collected.

**Starting point.** The chat-first UI was committed at `ddc43e0`. The developer requested a design discussion after observing `Hi` in the travel-result pane. The design separates `response_type` from lifecycle `status`, considers `GREETING` in the existing intent parser and preserves pending context with deterministic messages. The repository audit pinned down the behavior at that baseline. Keep CSS polish, production deployment, supervisor and unrelated refactoring in their existing roadmap positions.

Use the [current architecture](ARCHITECTURE.md#b4) to discuss the following with the developer. Implement only after explicit authorization.

1. Identify how `scope_response_node`, `generate_response_node` and terminal `run_travel_agent` currently encode results. Inspect exact enum/model imports and `TravelState`. Use the offline audit findings for pending questions and ready context as the baseline, and reproduce in focused regression cases.
2. Review `ResponseType` and the [API payload contract](ARCHITECTURE.md#b12). Agree how to distinguish terminal chat-only response vs pending clarification/brief response, how to preserve phase and context on social/nontravel edits, and which field/node owns semantic type. Ensure current request/response client contract consistent. Checkpoint 1 adds `pydantic_models/api_response.py`. Do not rely on string detection.
3. Extend existing `RequestIntent`/`extract_trip_turn` only if agreed. Preserve TRAVEL priority for mixed greeting+travel. Use deterministic reply, no extra extraction or agent. Inspect serializer allowlist when adding types.
4. Ensure no nontravel turn merges trip fields, bypasses confirmation, calls research or terminates a legitimate pending trip. Reconcile old parsed_request/context/brief routing. No new approval inferred from `hi`, `yes` typed in edit, or unrelated content. Exact handling of UNCLEAR and nontravel correction flow requires repository-based design.
5. Update backend/app response mapping and `static/script.js` state/rendering. Initial terminal message goes to chat, right panel stays empty, composer ready, preserve chat, next START new thread without thread mismatch. Pending conversation retains existing ID/brief/question. Completed travel result retains current export UX. No new HTML/CSS needed merely for semantics.
6. Write tests before/with fix. Run affected + full suite, real Groq trace, Swagger/manual browser scenario. Keep no research calls for greetings/unrelated input. Review behavior with screenshots. Commit coherent unit after successful verification. No exact commit message for this fix was agreed yet.

### 1F.1a regression matrix from latest discussion

| Input / context | Required behavior |
|---|---|
| Initial `Hi`, `Hello there!`, `Good morning` | GREETING, friendly deterministic chat-only response, no research, next message enabled |
| Greeting then travel request | Same visible chat history, independent new backend planning thread after terminal greeting, normal readiness |
| `Hi, plan a trip to London` | TRAVEL, normal planning. Greeting does not mask trip intent |
| `I want to go somewhere` | TRAVEL despite missing requirements. Clarify |
| Initial `What is Generative AI?` / coding question | OUT_OF_SCOPE, redirect in chat, no fake plan/PDF, no research |
| Out-of-scope then travel | Can continue naturally without New Trip |
| Ambiguous `What?` | UNCLEAR, useful prompt for supported request, no research |
| `Who invented Python?` during London details | Preserve accumulated context, reply travel-focused and retain question, same thread |
| `Hi` or unrelated content during confirmation | Preserve existing brief and phase, no approval, no research |
| Valid edit | Re-extract/merge, ready check, updated brief, new approval required |
| Completed conversational response | No travel-result pane/export, composer ready |
| Completed actual travel result | Plan pane, Copy/PDF enabled, terminal planning session until revision feature |
| BUILD at wrong phase / CANCEL / malformed payload | Existing lifecycle and validation contract preserved |

Deterministic tests should assert response semantics and phase, no provider/synthesis invocation, context unchanged for nontravel and explicit BUILD behavior. Real extraction eval tests greeting classifications and mixed input. don't require LLM-as-a-judge for transition invariants. Test UI state including new thread following greeting and refresh, not only backend enums.

<a id="c8"></a>

## C8. Provenance, gaps and recovery checklist

### Source inventory to recover separately

| Artifact / context | Use and limitation |
|---|---|
| `project_architecture_diagram.png`, `multi_agent_architecture.png` | Historical diagrams supplied in project. Initial tutorial / architecture references, not current topology. Exact visual content beyond prior discussion not independently transcribed for this handover. |
| Loose `app.py`, `backend.py`, `nodes.py`, `routing.py`, `state.py`, `travel_request.py`, `request_parser.py`, `request_policy.py`, `request_check.py`, `location_resolver.py`, provider files, `test.py`, README and frontend files | Historical stages. Loose files may not be mutually version-consistent. Do not combine them into a current runnable checkout. |
| `travora_code.zip` (5 Nov snapshot) | Inspected tree, models, provider helpers, graph, app, docs, tests, Docker/config. Predates integrated 1B–1F.1. Includes pycache. Not a Git archive/current branch. |
| Historical `Επικολλημένο κείμενο*.txt` state dumps | Inspected summarized keys, 41-message reused history, focused Milan routing. Avoid committing raw LLM/trace payloads. sensitive/unnecessary. |
| `Επικολλημένος κώδικας.py` | Older flight parsing/resolver code with DEFAULT_ORIGIN fallback. Superseded by active structured route. |
| `chat_based_approach*.png`, `guardrail_prompt.png`, `human_feedback.png`, earlier `ai-travel-plan.pdf`, other unnamed screenshots | Reference design/older behavior. Not comprehensively re-inspected. Recover only if needed, label historical. |
| Current visible 1D/1E code blocks, user-edited `run_travel_agent`, test failures and Git status | Exact proposed code and user-reported outcomes, not proof of entire latest repo content. |
| 1E test log (previous `Pasted text.txt`, 435 lines in conversation) | Actual 13 collected, 6 invalid combo failures, 7 passes. Root cause confirmed. Filename reused for latest handover request. Do not assume same mounted file contents. |
| `ui_step_1.png`–`ui_step_4.png`, `input_guardrail_issue.png` | Latest observed chat/brief/edit and semantic failure. |
| `london-travel-plan.pdf` | Historical output with date mismatch, estimates, nights and currency assumptions, and pagination concerns. See [grounding](ARCHITECTURE.md#b8) and [known issues](#c5). |
| Local checkout and live runtime evidence | The local checkout and exact Git refs were recovered in the 27 November audit. Raw LangSmith traces, Neon environment mapping and Render settings remain outside that audit. Retain safe references only if later supplied or authorized. |

### Resolved discrepancies and remaining uncertainties

- The old `validation/` tree and implicit session contract are superseded. The README still carries old references and topology. Current imports, module responsibilities and locked dependencies are recorded in [Architecture](ARCHITECTURE.md#b3).
- Both current context models accept `YYYY-MM` and yearless `MM`. The readiness service asks for the year when a travel period is required. The S2 regex is historical.
- The current brief retains dates and scope and the adapter drops them. The current provider/synthesis inputs were confirmed offline. The exact attribution of historical PDF symptoms to a particular step remains unverified.
- `clarify_request_node` currently updates both models and rechecks execution. The confirmed reapproval gap is the direct route from technical correction to research after BUILD.
- The test cleanup plan considered consolidating API/input tests. Both are tracked with distinct cases, and `tests/test_request_rules.py` is present. The audit identifies the negative guardrail assertions that should isolate the expected validation error.
- At the audit, `.gitignore` excluded the local handover from Git while `.dockerignore` did not exclude it from the Docker build context. The Dockerfile's `COPY . .` would include it if building from that checkout with the temporary file present. This is a local build-context observation. Consolidation leaves both ignore files and the handover intact.
- The old `route_after_research` helper is unreferenced by graph wiring, the `itinerary` response field is legacy and `app.TravelRequest` is unused by the endpoint. Keep cleanup in its planned scope.
- The latest plan-ready copy matches the problematic S6 UI. The template pins DOMPurify 3.5.0 and html2pdf.js 0.10.1 and leaves Marked unpinned. CDN availability and real-browser behavior remain unverified. Prefer checkout signatures to historical snippets.
- Earlier roadmap referenced future broader phases. Only latest Release 1 increments and Release 2/3 themes available. Do not reconstruct fictitious complete phase names/acceptance gates. Exact original production review, all Git commits and full trace histories missing.
- The local branch is `feature/conversational-trip-planning` and the local remote-tracking ref matches `ddc43e0`. 1F.1 is committed and the temporary handover ignore entry was the sole local change at audit time. Live remote and deploy state were not queried.
- Reported 1E real trace confirms expected flow, but direct trace access absent. Tests with stub execution node do not guarantee production no-bypass invariant. Restart persistence and negative actions need explicit evidence if not yet logged.
- Checkpoints 1–3 implement response types, pending nontravel behavior and greeting intent. Live greeting classification, brief revision validation, thread recovery and production checkpoint migration remain open. See the [1F.1a implementation tasks](#c7).

<a id="c9"></a>

## C9. Consolidation audit and outstanding verification

| Topic | Durable location | Evidence or open question |
|---|---|---|
| Product and engineering objectives | [AGENTS.md](../AGENTS.md), [product boundaries](ARCHITECTURE.md#b1) | Preserve current scope and learning-by-doing workflow. Future product scope requires agreement. |
| History and significant bugs | [Chronology](#c1), [implementation history](#c2), [architectural evolution](ARCHITECTURE.md#b2) | Current Git and source reconciled. The early production review transcript and some exact pre-1A phase labels remain unavailable. |
| Current architecture, stack, contracts and providers | [Architecture](ARCHITECTURE.md#b3) | Local source, Git and lockfile inspected. Provider responses and corroborating original traces remain unverified in this audit. |
| Persistence, security and deployment | [Architecture](ARCHITECTURE.md#b7), [planned production areas](#c3), [known issues](#c5) | Actual runtime mapping, checkpoint compatibility, storage policy, concurrency and ownership need release verification or design. |
| Architectural decisions and alternatives | [ADR-01 through ADR-28](ARCHITECTURE.md#b11), [response proposal](ARCHITECTURE.md#b12) | All 28 recorded decisions retained. Any additional early decisions require evidence. The 1F.1a proposal remains pending. |
| Roadmap, acceptance and current actionable item | [Roadmap](#c3), [manual scenarios](#c6), [1F.1a tasks and regression matrix](#c7) | All recovered roadmap IDs and order retained. Additional historical roadmap detail, release thresholds and PR/rollout/rollback plans are unresolved. |
| Collaboration and conventions | [AGENTS.md](../AGENTS.md) | Startup, mentorship, implementation authorization, environment boundaries and maintenance documented. |
| Tests, R&D and evaluation | [Test evidence](#c4), [smoke tests](#c6), [regression matrix](#c7) | 87 offline tests and focused probes recorded. Live providers, PostgreSQL, real browser and evaluation pipeline remain outside current verification. |
| Evidence and remaining knowledge gaps | [Classification](#evidence), [provenance](#c8) | Historical artifacts and developer reports remain traceable without depending on the original conversation for ordinary development. |

The three permanent files carry the available engineering context. A new session should begin with the [baseline and current actionable roadmap item](#baseline), preserve dev/prod isolation and keep Release 1 deployment gated on the remaining verification and explicit authorization.
