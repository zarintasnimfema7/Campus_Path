// Run from frontend: node scripts/check-phase2.mjs. No test framework required.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";
import * as jsxRuntime from "react/jsx-runtime";
import { renderToStaticMarkup } from "react-dom/server";

const read = path => readFileSync(new URL(`../src/${path}`, import.meta.url), "utf8");
const load = (source, globals = {}) => {
  const exports = {};
  const js = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
  } }).outputText;
  vm.runInNewContext(js, { exports, ...globals });
  return exports;
};
const jobId = "12345678-1234-1234-1234-123456789abc";
const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
function polling(responses, id = jobId) {
  const timers = new Map(), states = [], results = [], requests = [];
  let sequence = 0;
  const { pollWorkflow } = load(read("lib/workflow-polling.ts"), {
    AbortController,
    setTimeout(fn, delay) { assert.equal(delay, 3000); timers.set(++sequence, fn); return sequence; },
    clearTimeout(key) { timers.delete(key); },
  });
  const stop = pollWorkflow(id, async (path, init) => {
    requests.push({ path, init });
    const next = responses.shift();
    if (next instanceof Error) throw next;
    if (typeof next === "function") return next();
    return { ok: !next.http, status: next.http ?? 200, json: async () => ({ job_id: jobId, ...next }) };
  }, value => states.push(value), value => results.push(value));
  return { timers, states, results, requests, stop, async tick() {
    assert.equal(timers.size, 1);
    const [key, fn] = timers.entries().next().value;
    timers.delete(key); fn(); await flush();
  } };
}

let check = polling([{ status: "queued", retry_count: 2 }, { status: "processing" }, { status: "completed", result: {} }]);
await flush();
assert.equal(check.requests[0].path, `/workflow/${jobId}`);
assert.equal(check.requests[0].init.method, "GET");
await check.tick(); await check.tick();
assert.deepEqual(check.states, ["queued", "processing", "completed"]);
assert.equal(check.results.length, 1); assert.equal(check.timers.size, 0);
for (const [response, expected] of [[{ status: "failed" }, "failed"], [{ http: 404 }, "not-found"], [{ http: 403 }, "auth-error"]]) {
  check = polling([response]); await flush();
  assert.deepEqual(check.states, [expected]); assert.equal(check.timers.size, 0); assert.equal(check.results.length, 0);
}
check = polling([new Error(), { status: "queued" }, new Error(), new Error(), new Error()]);
await flush(); assert.equal(check.states.length, 0);
await check.tick(); await check.tick(); await check.tick();
assert.deepEqual(check.states, ["queued"]);
await check.tick(); assert.equal(check.states.at(-1), "connection-error"); assert.equal(check.timers.size, 0);
check = polling([{ status: "queued" }]); await flush(); check.stop();
assert.equal(check.timers.size, 0); assert.equal(check.requests[0].init.signal.aborted, true);
let resolve;
check = polling([() => new Promise(done => { resolve = done; })]); await flush();
assert.equal(check.requests.length, 1); assert.equal(check.timers.size, 0);
check.stop(); resolve({ ok: true, status: 200, json: async () => ({ job_id: jobId, status: "completed" }) });
await flush(); assert.equal(check.results.length, 0); assert.equal(check.states.length, 0);
check = polling([], "invalid"); await flush(); assert.equal(check.requests.length, 0);

const savedSource = read("lib/saved-workflow.ts");
const storage = { value: null, getItem() { return this.value; } };
const { readSavedWorkflow } = load(savedSource, { sessionStorage: storage });
assert.equal(readSavedWorkflow(), null);
for (const invalid of ["bad json", "null", "[]", '{"plan":{"tasks":[null]}}', '{"skill_gap":{"matched_skills":42}}']) {
  storage.value = invalid; assert.throws(readSavedWorkflow);
}
storage.value = JSON.stringify({ plan: { tasks: [{ title: "Fixture task", target_skill: "Fixture skill", goal: "Learn", action: "Build", estimated_hours: 2, priority: 1, evidence_required: ["Repository"] }] } });
assert.equal(readSavedWorkflow().plan.tasks[0].target_skill, "Fixture skill");

const analysis = read("app/analysis/[jobId]/page.tsx");
assert.match(analysis, /useParams/); assert.match(analysis, /key=\{jobId\}/);
assert.match(analysis, /return pollWorkflow/); assert.match(analysis, /completed.current = true/);
assert.equal((analysis.match(/router.replace\("\/dashboard"\)/g) ?? []).length, 1);
assert.match(analysis, /Try Again<\/Link>/); assert.match(analysis, /Check Again<\/button>/);
assert.match(analysis, /setPollAttempt/); assert.match(analysis, /role="status"/);
assert.doesNotMatch(read("lib/workflow-polling.ts"), /sessionStorage|user_id|setInterval|WebSocket|EventSource/);
const dashboard = read("app/dashboard/page.tsx");
for (const route of ["dashboard", "skill-gap", "learning-path", "evidence", "profile"]) {
  assert.match(dashboard, new RegExp(`router.push\\("/${route}"\\)`));
  assert.ok(read(`app/${route}/page.tsx`));
}
assert.match(dashboard, /id="readiness"/);
const profile = read("app/profile/page.tsx");
assert.match(profile, /user\?\.fullName/); assert.match(profile, /primaryEmailAddress/); assert.match(profile, /openUserProfile/);
const skillGap = read("app/skill-gap/page.tsx");
for (const field of ["matched_skills", "partial_skills", "missing_skills"]) assert.ok(skillGap.includes(field));
assert.match(skillGap, /count \/ total \* 100/);
const plan = read("app/learning-path/page.tsx");
for (const field of ["target_skill", "goal", "action", "estimated_hours", "priority", "evidence_required"]) assert.ok(plan.includes(`task.${field}`));
assert.match(plan, /No previous plan versions yet/); assert.doesNotMatch(plan, /task\.status|Evidence verified|Plan v1|Plan v2/);

// Render the existing pages with contract-shaped fixtures and empty/error storage.
const fixture = { student: { name: "CV name", skills: ["Fixture skill"] }, job: { job_title: "Fixture role" },
  skill_gap: { readiness_score: 61, required_score: 60, preferred_score: 65, matched_skills: ["Fixture skill"], partial_skills: [], missing_skills: ["Another skill"] },
  plan: JSON.parse(storage.value).plan };
function renderPage(source, saved) {
  let state = [], cursor = 0;
  const globals = { sessionStorage: { getItem: () => saved }, require(name) {
    if (name === "react/jsx-runtime") return jsxRuntime;
    if (name === "react") return {
      useState(initial) { const i = cursor++; if (!(i in state)) state[i] = initial; return [state[i], value => { state[i] = value; }]; },
      useEffect(fn) { fn(); },
    };
    if (name === "next/navigation") return { useRouter: () => ({ push() {}, replace() {} }) };
    if (name === "next/link") return { default: props => jsxRuntime.jsx("a", props) };
    if (name === "@clerk/nextjs") return { useAuth: () => ({ isLoaded: true, isSignedIn: true }), useClerk: () => ({}), useUser: () => ({ user: { fullName: "Account name", primaryEmailAddress: { emailAddress: "fixture@example.test" } } }) };
    if (name === "@/lib/saved-workflow") return load(savedSource, globals);
    if (name === "@/components/workflow-data-state") return load(read("components/workflow-data-state.tsx"), globals);
    if (name === "lucide-react" || name === "react-icons/fa") return new Proxy({}, { get: () => () => null });
    throw new Error(`Unexpected dependency ${name}`);
  } };
  const Page = load(source, globals).default;
  Page(); cursor = 0;
  return renderToStaticMarkup(Page());
}
assert.match(renderPage(profile, JSON.stringify(fixture)), /Account name/);
assert.match(renderPage(profile, JSON.stringify(fixture)), /fixture@example.test/);
assert.match(renderPage(profile, null), /No CV analysis is available yet/);
assert.match(renderPage(plan, JSON.stringify(fixture)), /Fixture task/);
assert.match(renderPage(plan, JSON.stringify(fixture)), /Repository/);
assert.match(renderPage(skillGap, JSON.stringify(fixture)), /1 of 2 skills/);
for (const source of [dashboard, plan, skillGap]) {
  assert.match(renderPage(source, null), /Complete your first analysis/);
  assert.match(renderPage(source, "broken"), /Analysis unavailable/);
}
console.log("PASS: Phase 2 polling lifecycle, cleanup, recovery wiring, route navigation, storage states, profile sources, skill counts, and actual plan fields/history checks.");
