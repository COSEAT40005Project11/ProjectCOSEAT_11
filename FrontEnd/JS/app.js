// Traditional Knowledge Repository - web frontend (Sprint 2)
// Picks its data source on load:
//   - served by the FastAPI backend (uvicorn API.app:app)  -> real API
//   - opened directly / Live Server / no backend running   -> built-in SAMPLE DATA
// The mock below returns the same shapes as the endpoints in API/app.py.
// Hiding things in the browser is for usability only. The backend MUST enforce roles and access levels.

let USE_API = false;   // set by detectApi() at start-up
const API = "";  // same origin when served by FastAPI. Set to "http://127.0.0.1:8000" if serving separately.

const ACCESS = {
  public:     { label: "Public",         icon: "globe" },
  community:  { label: "Community only", icon: "users" },
  restricted: { label: "Restricted",     icon: "lock" },
  sacred:     { label: "Sacred",         icon: "shield-alert" }
};
// DEMO ACCOUNTS ONLY. Replace with POST /auth/login once the backend has real authentication.
const USERS = {
  member: { pw: "member123", role: "member", name: "Community member" },
  admin:  { pw: "admin123",  role: "admin",  name: "Admin reviewer" }
};
const CAN = { guest: ["public"], member: ["public", "community"], admin: ["public", "community", "restricted", "sacred"] };
const NEED = { submit: ["member", "admin"], review: ["admin"] };
// highest level each role may ask about (retrieval.py never returns sacred items)
const ASK_LEVEL = { guest: "public", member: "community", admin: "restricted" };
// offline copy: only PUBLIC items are ever saved on the device (shared kiosk / shared computer safety)
const CACHE_KEY = "tkr_public_cache";

// ---------------------------------------------------------------------------
// small helpers
// ---------------------------------------------------------------------------
const store = {
  get(area, k) { try { return JSON.parse(window[area].getItem(k)); } catch (e) { return null; } },
  set(area, k, v) { try { window[area].setItem(k, JSON.stringify(v)); } catch (e) { /* private mode */ } },
  del(area, k) { try { window[area].removeItem(k); } catch (e) { /* ignore */ } }
};

let session = store.get("sessionStorage", "tkr");
let next = null;          // page to return to after logging in
let byId = {};            // items currently on screen, for the Listen button
let viewGen = 0;          // bumps on every page change, so a slow load can't draw over a newer page
const stale = g => g !== viewGen;
const role = () => (session && CAN[session.role] ? session.role : "guest");
const canSee = i => CAN[role()].includes(i.access);

const app = document.getElementById("app");
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const empty = (icon, text) => `<div class="empty"><div class="big">${ic(icon)}</div><p>${text}</p></div>`;
const badge = (txt, cls = "") => `<span class="badge ${cls}">${esc(txt)}</span>`;
const accessBadge = k => { const a = ACCESS[k] || ACCESS.community; return `<span class="badge lvl-${k}">${ic(a.icon)} ${a.label}</span>`; };

function fmtDate(iso) {
  const d = new Date(iso);
  return iso && !isNaN(d) ? d.toLocaleString("en-AU", { dateStyle: "medium", timeStyle: "short" }) : "Not recorded";
}

function summaryLabel(method) {
  return ({
    manual: "Written by the person who submitted it",
    extractive: "Sentences picked by the AI, checked by a reviewer",
    abstractive: "Written by the AI, checked by a reviewer"
  })[method] || "Not recorded";
}

let toastTimer;
function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2800);
}

// ---------------------------------------------------------------------------
// MOCK BACKEND (used while USE_API = false). Placeholder content only - no real community knowledge.
// Same paths and response shapes as API/app.py. Resets when the page reloads.
// ---------------------------------------------------------------------------
const mock = (() => {
  const day = n => new Date(Date.now() - n * 86400000).toISOString();
  const item = (id, title, text, extra) => ({
    id, title, summary: text, original_text: text, status: "pending", confidence: 0.8, access: "community",
    source: "Sample source - " + title, source_file: "sample.pdf", chunk_index: 0, summary_method: "extractive",
    reviewed_by: null, reviewed_at: null, ...extra
  });
  const approved = [
    item("s1", "Sample: about this repository", "This is placeholder text. The repository stores knowledge only after an authorised elder or reviewer approves it.", { status: "approved", access: "public", reviewed_by: "Demo reviewer", reviewed_at: day(6) }),
    item("s2", "Sample: seasonal calendar entry", "Placeholder text for a public seasonal calendar entry. Real content will come from approved sources.", { status: "approved", access: "public", reviewed_by: "Demo reviewer", reviewed_at: day(3) }),
    item("s3", "Sample: community-only story", "Placeholder text that only signed-in community members should see.", { status: "approved", access: "community", summary_method: "manual", reviewed_by: "Demo reviewer", reviewed_at: day(2) }),
    item("s4", "Sample: restricted record", "Placeholder text that only reviewers should see.", { status: "approved", access: "restricted", reviewed_by: "Demo reviewer", reviewed_at: day(1) })
  ];
  const pending = [
    item("p1", "Sample: transcript awaiting review", "Placeholder transcript text from the speech-to-text step. A reviewer checks it against the recording before it is published.", { confidence: 0.82, summary: "Placeholder AI summary of the transcript." }),
    item("p2", "Sample: document extract", "Placeholder text extracted from an approved source document.", { confidence: 0.55, access: "public", summary: "Placeholder AI summary of the document extract." }),
    item("p3", "Sample: off-topic extract", "Placeholder text about road works that the AI scored as not relevant.", { confidence: 0.12, status: "needs_review", summary: "Placeholder AI summary of an off-topic extract." })
  ];
  let rejected = 0;
  const RANK = { public: 0, community: 1, restricted: 2 };   // sacred never returned by Ask (same as retrieval.py)
  const words = s => String(s).toLowerCase().match(/[a-z0-9]+/g) || [];
  const take = (list, id) => { const i = list.findIndex(x => x.id === id); return i < 0 ? null : list.splice(i, 1)[0]; };

  return async function (path, opts = {}) {
    await new Promise(r => setTimeout(r, 150));              // feel like a network call
    const body = opts.body ? JSON.parse(opts.body) : {};
    const url = new URL(path, location.href);
    const p = url.pathname;
    if (p === "/api/pending") return pending.map(x => ({ ...x }));
    if (p === "/api/approved") return approved.map(x => ({ ...x }));
    if (p === "/api/stats") return { pending: pending.length, approved: approved.length, rejected };
    if (p === "/api/submit") {
      const id = "m" + Date.now();
      pending.push(item(id, body.title, body.text, { access: body.access, confidence: 1, summary_method: "manual", source: body.source || "Manual submission" }));
      return { ok: true, id };
    }
    let m = p.match(/^\/api\/items\/(.+)\/(approve|reject)$/);
    if (m) {
      const rec = take(pending, decodeURIComponent(m[1]));
      if (!rec) throw new Error("404 item not found in pending queue");
      if (m[2] === "reject") { rejected++; return { ok: true, status: "rejected", id: rec.id }; }
      approved.push({ ...rec, status: "approved", access: body.access, summary: body.summary ?? rec.summary,
        original_text: body.original_text ?? rec.original_text, reviewed_by: body.reviewed_by, reviewed_at: new Date().toISOString() });
      return { ok: true, status: "approved", id: rec.id };
    }
    if (p === "/api/ask") {
      const q = new Set(words(url.searchParams.get("q")));
      const lvl = RANK[url.searchParams.get("access")] ?? 1;
      const scored = approved.filter(x => x.access in RANK && RANK[x.access] <= lvl).map(x => {
        const w = words(x.title + " " + x.original_text);
        return { x, score: w.filter(t => q.has(t)).length / Math.max(q.size, 1) };
      }).filter(s => s.score >= 0.3).sort((a, b) => b.score - a.score).slice(0, 3);
      if (!scored.length) return { abstained: true, reason: "no approved source is relevant enough to answer safely", passages: [] };
      return { abstained: false, passages: scored.map(({ x, score }) => ({
        snippet: x.summary, source_text: x.original_text, citation: x.source, score: Math.min(score, 1), access: x.access })) };
    }
    throw new Error("404 unknown mock path " + p);
  };
})();

async function api(path, opts = {}) {
  if (!USE_API) return mock(path, opts);
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 10000);   // don't hang forever on a slow connection
  try {
    const res = await fetch(API + path, { ...opts, signal: ctl.signal });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return await res.json();
  } finally { clearTimeout(timer); }
}

const postJSON = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

// Approved items the current user may see. Falls back to the saved public copy when offline.
async function getApproved() {
  try {
    const list = await api("/api/approved");
    store.set("localStorage", CACHE_KEY, { at: new Date().toISOString(), items: list.filter(i => i.access === "public") });
    return { items: list.filter(canSee), offline: false };
  } catch (e) {
    const c = store.get("localStorage", CACHE_KEY);
    if (c && Array.isArray(c.items)) return { items: c.items.filter(canSee), offline: true, at: c.at };
    throw e;
  }
}

const offlineBanner = at => `<div class="offline" role="status">${ic("wifi-off")}
  <span>Can't reach the server. Showing the public items saved on this device (${esc(fmtDate(at))}).</span></div>`;

// ---------------------------------------------------------------------------
// Listen (read aloud) - for people who prefer listening to reading
// ---------------------------------------------------------------------------
const SPEECH = "speechSynthesis" in window;
let speakingId = null;

const listenBtn = i => SPEECH
  ? `<button class="btn ghost sm" data-listen="${esc(i.id)}" aria-pressed="false">${ic("volume-2")} Listen</button>` : "";

function resetListenButtons() {
  document.querySelectorAll("[data-listen]").forEach(b => { b.innerHTML = `${ic("volume-2")} Listen`; b.setAttribute("aria-pressed", "false"); });
}

function stopSpeaking() {
  if (SPEECH) speechSynthesis.cancel();
  speakingId = null;
  resetListenButtons();
}

function toggleListen(btn) {
  const id = btn.dataset.listen;
  const wasThis = speakingId === id;
  stopSpeaking();
  if (wasThis) return;
  const i = byId[id];
  if (!i) return;
  const u = new SpeechSynthesisUtterance(`${i.title}. ${i.summary}`);
  u.lang = "en-AU";
  u.onend = u.onerror = () => { if (speakingId === id) { speakingId = null; resetListenButtons(); } };
  speakingId = id;
  btn.innerHTML = `${ic("square")} Stop`;
  btn.setAttribute("aria-pressed", "true");
  speechSynthesis.speak(u);
}

// ---------------------------------------------------------------------------
// cards
// ---------------------------------------------------------------------------
function approvedCard(i) {
  byId[i.id] = i;
  return `<article class="card">
    <h3>${esc(i.title)}</h3>
    <div class="badges">${badge("Approved", "approved")} ${accessBadge(i.access)} ${badge(i.source)}</div>
    <p>${esc(i.summary)}</p>
    ${SPEECH ? `<div class="actions">${listenBtn(i)}</div>` : ""}
    <details>
      <summary>Source text and history</summary>
      <p class="src">${esc(i.original_text)}</p>
      <dl class="prov">
        <dt>Source</dt><dd>${esc(i.source)}</dd>
        <dt>Approved by</dt><dd>${esc(i.reviewed_by || "Not recorded")}</dd>
        <dt>Approved on</dt><dd>${esc(fmtDate(i.reviewed_at))}</dd>
        <dt>Summary</dt><dd>${esc(summaryLabel(i.summary_method))}</dd>
      </dl>
    </details>
  </article>`;
}

function accessSelect(id, current, levels = Object.keys(ACCESS)) {
  return `<select id="acc-${esc(id)}" aria-label="Access level">` +
    levels.map(k => `<option value="${k}" ${k === current ? "selected" : ""}>${ACCESS[k].label}</option>`).join("") +
    `</select>`;
}

function reviewCard(i) {
  const pct = Math.round((i.confidence || 0) * 100);
  const level = pct >= 60 ? "high" : pct >= 25 ? "mid" : "low";
  const flagged = i.status === "needs_review";
  const id = esc(i.id);
  return `<article class="card pending" id="card-${id}">
    <h3>${esc(i.title)}</h3>
    <div class="badges">
      ${badge(flagged ? "Needs a closer look" : "Pending", "pending")}
      ${badge(i.source)}
      ${i.summary_method ? badge(summaryLabel(i.summary_method)) : ""}
    </div>
    <div class="conf ${level}">How on-topic the AI thinks this is: ${pct}%${level === "low" ? ". Check it carefully." : ""}
      <div class="bar-track"><div style="width:${pct}%"></div></div></div>
    <div class="compare">
      <div>
        <label for="sum-${id}">Summary shown to users (you can edit)</label>
        <textarea id="sum-${id}" rows="6">${esc(i.summary)}</textarea>
      </div>
      <div>
        <label for="src-${id}">Original source text (stored and cited)</label>
        <textarea id="src-${id}" rows="6">${esc(i.original_text)}</textarea>
      </div>
    </div>
    <label for="acc-${id}">Who can see this</label>
    ${accessSelect(i.id, i.access)}
    <div class="actions" style="margin-top:.9rem">
      <button class="btn approve" data-approve="${id}">${ic("check")} Approve and publish</button>
      <button class="btn reject" data-reject="${id}">${ic("x")} Reject</button>
    </div>
    <div class="reject-box" id="rj-${id}" hidden>
      <label for="why-${id}">Why is this being rejected? (optional, kept in the record)</label>
      <textarea id="why-${id}" rows="2" placeholder="For example: wrong community, needs elder permission, inaccurate"></textarea>
      <div class="actions" style="margin-top:.6rem">
        <button class="btn reject" data-confirm-reject="${id}">Confirm reject</button>
        <button class="btn ghost" data-cancel-reject="${id}">Cancel</button>
      </div>
    </div>
  </article>`;
}

// ---------------------------------------------------------------------------
// views
// ---------------------------------------------------------------------------
const views = {
  async search() {
    app.innerHTML = `<h2>Ask</h2>
      <p class="sub">Answers come only from approved sources, shown word for word with where they came from. If nothing approved fits, the system says so instead of guessing.</p>
      <div class="toolbar">
        <input id="ask" type="search" placeholder="Ask a question..." aria-label="Ask a question">
        <button class="btn primary" id="askgo">${ic("search")} Ask</button>
      </div>
      <div id="answer" style="margin-top:1.25rem"></div>
      <h2 style="margin-top:2rem">Find by word</h2>
      ${role() === "guest" ? `<p class="sub">Showing public items. Log in to see community knowledge.</p>` : ""}
      <input id="q" type="search" placeholder="Type a word..." aria-label="Filter approved knowledge">
      <div id="results" style="margin-top:1rem"></div>`;

    // Ask: retrieval with citations, or an honest "not enough information"
    const askBox = document.getElementById("ask");
    const runAsk = async () => {
      const query = askBox.value.trim();
      if (!query) return;
      const box = document.getElementById("answer");
      const g = viewGen;
      box.innerHTML = `<p class="sub">Searching approved sources...</p>`;
      try {
        const r = await api(`/api/ask?q=${encodeURIComponent(query)}&access=${ASK_LEVEL[role()]}`);
        if (stale(g)) return;
        if (r.abstained) {
          box.innerHTML = `<div class="card abstain">
            <h3>Not enough information</h3>
            <p>${esc(r.reason ? r.reason[0].toUpperCase() + r.reason.slice(1) : "No approved source is close enough to answer this safely")}.</p>
            <p class="sub">This is on purpose: the repository will not guess.</p></div>`;
          return;
        }
        box.innerHTML = r.passages.map(p => `<article class="card">
          <p>${esc(p.snippet)}</p>
          <details><summary>Full source passage</summary><p class="src">${esc(p.source_text)}</p></details>
          <div class="badges" style="margin-top:.6rem">${badge("Source: " + p.citation)} ${p.access ? accessBadge(p.access) : ""} ${badge("match " + Math.round(p.score * 100) + "%")}</div>
        </article>`).join("");
      } catch (e) {
        if (stale(g)) return;
        box.innerHTML = empty("wifi-off", "Can't reach the server. Asking needs a connection, but Browse still shows public items saved on this device.");
      }
    };
    document.getElementById("askgo").onclick = runAsk;
    askBox.addEventListener("keydown", e => { if (e.key === "Enter") runAsk(); });

    // Find by word: client-side filter over the approved items this user can see
    const results = document.getElementById("results");
    let res;
    const g = viewGen;
    try { res = await getApproved(); } catch (e) { if (!stale(g)) results.innerHTML = empty("wifi-off", "Can't reach the server."); return; }
    if (stale(g)) return;
    const q = document.getElementById("q");
    const draw = () => {
      byId = {};
      const term = q.value.trim().toLowerCase();
      if (!term) { results.innerHTML = res.offline ? offlineBanner(res.at) : ""; return; }
      const found = res.items.filter(i => (i.title + " " + i.summary + " " + i.original_text).toLowerCase().includes(term));
      results.innerHTML = (res.offline ? offlineBanner(res.at) : "") +
        (found.length ? found.map(approvedCard).join("") : empty("search-x", "No approved items match that word."));
    };
    q.addEventListener("input", draw);
    draw();
  },

  async browse() {
    app.innerHTML = `<h2>Browse</h2><p class="sub">Loading...</p>`;
    let res;
    const g = viewGen;
    try { res = await getApproved(); }
    catch (e) { if (!stale(g)) app.innerHTML = `<h2>Browse</h2>` + empty("wifi-off", "Can't reach the server, and nothing is saved on this device yet."); return; }

    if (stale(g)) return;
    const levels = CAN[role()];
    let level = "all";
    app.innerHTML = `<h2>Browse</h2>
      ${res.offline ? offlineBanner(res.at) : ""}
      <p class="sub" id="bcount"></p>
      <div class="toolbar">
        <input id="bq" type="search" placeholder="Filter by word..." aria-label="Filter items by word">
        <select id="bsort" aria-label="Sort order">
          <option value="new">Newest approved first</option>
          <option value="title">Title A to Z</option>
        </select>
      </div>
      <div class="chips" role="group" aria-label="Filter by who can see it">
        <button class="chip active" data-level="all" aria-pressed="true">All</button>
        ${levels.map(k => `<button class="chip" data-level="${k}" aria-pressed="false">${ic(ACCESS[k].icon)} ${ACCESS[k].label}</button>`).join("")}
      </div>
      ${role() === "guest" ? `<p class="hint">You're seeing public items only. Log in to see community knowledge.</p>` : ""}
      <div id="blist" style="margin-top:1rem"></div>`;

    const q = document.getElementById("bq"), sort = document.getElementById("bsort");
    const draw = () => {
      byId = {};
      const term = q.value.trim().toLowerCase();
      let list = res.items.filter(i =>
        (level === "all" || i.access === level) &&
        (!term || (i.title + " " + i.summary + " " + i.original_text).toLowerCase().includes(term)));
      list = sort.value === "title"
        ? list.sort((a, b) => String(a.title).localeCompare(String(b.title)))
        : list.sort((a, b) => String(b.reviewed_at || "").localeCompare(String(a.reviewed_at || "")));
      document.getElementById("bcount").textContent = `Showing ${list.length} of ${res.items.length} item(s) available to you.`;
      document.getElementById("blist").innerHTML = list.length
        ? list.map(approvedCard).join("")
        : empty("book-x", res.items.length ? "No items match these filters." : "Nothing has been approved yet.");
    };
    app.querySelectorAll(".chip").forEach(c => c.onclick = () => {
      level = c.dataset.level;
      app.querySelectorAll(".chip").forEach(x => { x.classList.toggle("active", x === c); x.setAttribute("aria-pressed", x === c); });
      draw();
    });
    q.addEventListener("input", draw);
    sort.addEventListener("change", draw);
    draw();
  },

  login() {
    app.innerHTML = `<h2>Log in</h2><p class="sub">Log in to submit knowledge or review submissions.</p>
      <form id="lf" class="form-card">
        <label for="u">Username</label><input id="u" autocomplete="username">
        <label for="p">Password</label><input id="p" type="password" autocomplete="current-password">
        <p class="err" id="err" role="alert"></p>
        <button class="btn" type="submit">${ic("log-in")} Log in</button>
      </form>
      <div class="hint">Demo accounts (prototype only): <b>member</b> / member123 and <b>admin</b> / admin123</div>`;
    document.getElementById("u").focus();
    document.getElementById("lf").onsubmit = e => {
      e.preventDefault();
      const u = USERS[document.getElementById("u").value.trim().toLowerCase()];
      if (!u || u.pw !== document.getElementById("p").value) {
        document.getElementById("err").textContent = "Wrong username or password. Check both and try again.";
        return;
      }
      session = { role: u.role, name: u.name };
      store.set("sessionStorage", "tkr", session);
      toast("Logged in as " + u.name);
      const dest = next || "search";
      next = null;
      go(dest);
    };
  },

  submit() {
    app.innerHTML = `<h2>Submit</h2><p class="sub">New items go to the review queue. Nothing is published until an elder or reviewer approves it.</p>
      <div class="form-card">
        <label for="t">Title</label>
        <input id="t" placeholder="Short title" maxlength="150">
        <label for="s">Text or source</label>
        <textarea id="s" rows="6" placeholder="Paste the text to be recorded"></textarea>
        <p class="meta" id="scount">0 words</p>
        <label for="acc-new">Who should be able to see it? (the reviewer makes the final call)</label>
        ${accessSelect("new", "community")}
        <label class="check"><input type="checkbox" id="consent">
          <span>I have permission from the person or family this knowledge belongs to, to share it here.</span></label>
        <p class="err" id="serr" role="alert"></p>
        <button class="btn submit" id="go">${ic("upload")} Send for review</button>
      </div>`;
    const s = document.getElementById("s");
    s.addEventListener("input", () => {
      const n = s.value.trim() ? s.value.trim().split(/\s+/).length : 0;
      document.getElementById("scount").textContent = `${n} word${n === 1 ? "" : "s"}`;
    });
    const go = document.getElementById("go");
    go.onclick = async () => {
      const err = document.getElementById("serr");
      const title = document.getElementById("t").value.trim();
      const text = s.value.trim();
      if (!title || !text) { err.textContent = "Add a title and some text first."; return; }
      if (!document.getElementById("consent").checked) { err.textContent = "Please confirm you have permission to share this."; return; }
      err.textContent = "";
      go.disabled = true;
      try {
        await postJSON("/api/submit", {
          title, text,
          access: document.getElementById("acc-new").value,
          source: `Manual submission by ${session.name}; submitter confirmed permission from the knowledge holder`
        });
        toast("Sent for review");
        go(role() === "admin" ? "review" : "browse");
      } catch (e) { err.textContent = "Couldn't send it. Check your connection and try again."; go.disabled = false; }
    };
  },

  async review() {
    app.innerHTML = `<h2>Review queue</h2><p class="sub">Loading...</p>`;
    let list, stats;
    const g = viewGen;
    try { [list, stats] = await Promise.all([api("/api/pending"), api("/api/stats")]); }
    catch (e) { if (!stale(g)) app.innerHTML = `<h2>Review queue</h2>` + empty("wifi-off", "Can't reach the server."); return; }

    if (stale(g)) return;
    const flaggedCount = list.filter(i => i.status === "needs_review").length;
    let only = "all";
    app.innerHTML = `<h2>Review queue</h2>
      <div class="stats">
        <div class="stat"><b>${stats.pending}</b><span>Waiting</span></div>
        <div class="stat ok"><b>${stats.approved}</b><span>Approved</span></div>
        <div class="stat no"><b>${stats.rejected}</b><span>Rejected</span></div>
      </div>
      <p class="sub">Reviewing as <b>${esc(session.name)}</b>. Your name is recorded against every decision. Nothing enters the repository until it's approved.</p>
      <div class="chips" role="group" aria-label="Filter the queue">
        <button class="chip active" data-only="all" aria-pressed="true">All (${list.length})</button>
        <button class="chip" data-only="flagged" aria-pressed="false">${ic("shield-alert")} Needs a closer look (${flaggedCount})</button>
      </div>
      <div id="rlist" style="margin-top:1rem"></div>`;

    const draw = () => {
      const shown = only === "flagged" ? list.filter(i => i.status === "needs_review") : list;
      document.getElementById("rlist").innerHTML = shown.length
        ? shown.map(reviewCard).join("")
        : empty("circle-check", only === "flagged" ? "Nothing is flagged." : "The queue is empty. Nothing is waiting for review.");
    };
    app.querySelectorAll(".chip").forEach(c => c.onclick = () => {
      only = c.dataset.only;
      app.querySelectorAll(".chip").forEach(x => { x.classList.toggle("active", x === c); x.setAttribute("aria-pressed", x === c); });
      draw();
    });
    draw();
  }
};

// ---------------------------------------------------------------------------
// review decisions
// ---------------------------------------------------------------------------
async function decide(id, action) {
  const card = document.getElementById(`card-${id}`);
  card.querySelectorAll("button").forEach(b => (b.disabled = true));
  try {
    if (action === "approve") {
      await postJSON(`/api/items/${encodeURIComponent(id)}/approve`, {
        reviewed_by: session.name,
        access: document.getElementById(`acc-${id}`).value,
        summary: document.getElementById(`sum-${id}`).value,
        original_text: document.getElementById(`src-${id}`).value
      });
      toast("Approved and added to the repository");
    } else {
      await postJSON(`/api/items/${encodeURIComponent(id)}/reject`, {
        reviewed_by: session.name,
        reason: document.getElementById(`why-${id}`).value.trim() || null
      });
      toast("Rejected");
    }
    await refreshCount();
    views.review();
  } catch (e) {
    toast("That didn't save: " + e.message);
    card.querySelectorAll("button").forEach(b => (b.disabled = false));
  }
}

app.addEventListener("click", e => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.listen) return toggleListen(b);
  if (b.dataset.approve || b.dataset.reject || b.dataset.confirmReject || b.dataset.cancelReject) {
    if (role() !== "admin") { toast("Only reviewers can do this."); return; }
  }
  if (b.dataset.approve) return decide(b.dataset.approve, "approve");
  if (b.dataset.reject) {
    const box = document.getElementById(`rj-${b.dataset.reject}`);
    box.hidden = false;
    box.querySelector("textarea").focus();
    return;
  }
  if (b.dataset.cancelReject) { document.getElementById(`rj-${b.dataset.cancelReject}`).hidden = true; return; }
  if (b.dataset.confirmReject) return decide(b.dataset.confirmReject, "reject");
});

// ---------------------------------------------------------------------------
// header, navigation
// ---------------------------------------------------------------------------
async function refreshCount() {
  const c = document.getElementById("count");
  if (role() !== "admin") { c.hidden = true; return; }
  try {
    const s = await api("/api/stats");
    c.textContent = s.pending;
    c.hidden = s.pending === 0;
  } catch (e) { /* offline: leave as is */ }
}

function chrome() {
  document.getElementById("reviewBtn").hidden = role() !== "admin";
  document.getElementById("auth").innerHTML = session
    ? `<span class="who ${esc(session.role)}">${esc(session.name)}</span><button id="lo">${ic("log-out")} Log out</button>`
    : `<button id="li">${ic("log-in")} Log in</button>`;
  const lo = document.getElementById("lo"), li = document.getElementById("li");
  if (lo) lo.onclick = () => { session = null; store.del("sessionStorage", "tkr"); toast("Logged out"); go("search"); };
  if (li) li.onclick = () => go("login");
}

// ---------------------------------------------------------------------------
// page addresses (#search, #browse ...) so the browser Back/Forward buttons work
// ---------------------------------------------------------------------------
const PAGES = ["search", "browse", "submit", "review", "login"];
const TITLES = { search: "Search", browse: "Browse", submit: "Submit", review: "Review queue", login: "Log in" };
const pageFromAddress = () => { const v = location.hash.slice(1); return PAGES.includes(v) ? v : "search"; };

// go() = a normal click: adds a step to the browser history, then the hashchange listener shows the page
function go(view) {
  if (location.hash.slice(1) === view) show(view);
  else location.hash = view;
}
window.addEventListener("hashchange", () => show(pageFromAddress()));

function show(view) {
  viewGen++;
  stopSpeaking();
  if (NEED[view] && !NEED[view].includes(role())) {
    if (role() === "guest") { next = view; toast("Log in to continue."); view = "login"; }
    else { toast("This page is for reviewers only."); view = "search"; }
  }
  // keep the address bar in step without adding an extra history step (e.g. after a redirect to login)
  if (location.hash.slice(1) !== view) history.replaceState(null, "", "#" + view);
  document.title = `${TITLES[view]} - Traditional Knowledge Repository`;
  document.querySelectorAll("nav button").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  chrome();
  views[view]();
  refreshCount();
  window.scrollTo(0, 0);
}

// Use the real API only if /health answers like our FastAPI backend does.
async function detectApi() {
  if (!location.protocol.startsWith("http")) return false;
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 1500);
  try {
    const r = await fetch(API + "/health", { signal: ctl.signal });
    return r.ok && (await r.json()).status === "ok";
  } catch (e) { return false; } finally { clearTimeout(timer); }
}

// ---------------------------------------------------------------------------
// display settings: text size and easy view (remembered on this device only)
// ---------------------------------------------------------------------------
const SIZES = [{ pct: 100, label: "A" }, { pct: 115, label: "A+" }, { pct: 130, label: "A++" }];
const prefs = { size: 0, easy: false, ...(store.get("localStorage", "tkr_display") || {}) };
if (!SIZES[prefs.size]) prefs.size = 0;

function applyDisplay() {
  const size = SIZES[prefs.size];
  document.documentElement.style.fontSize = size.pct + "%";
  document.body.classList.toggle("easy", prefs.easy);
  const t = document.getElementById("textBtn"), e = document.getElementById("easyBtn");
  t.innerHTML = `<span aria-hidden="true">${size.label}</span>`;
  t.setAttribute("aria-label", `Text size ${size.pct}%. Click to change.`);
  t.title = `Text size: ${size.pct}%`;
  e.setAttribute("aria-pressed", prefs.easy);
  e.innerHTML = `${ic("eye")} ${prefs.easy ? "Easy view on" : "Easy view"}`;
  store.set("localStorage", "tkr_display", prefs);
}
document.getElementById("textBtn").onclick = () => {
  prefs.size = (prefs.size + 1) % SIZES.length;
  applyDisplay();
  toast(`Text size ${SIZES[prefs.size].pct}%`);
};
document.getElementById("easyBtn").onclick = () => {
  prefs.easy = !prefs.easy;
  applyDisplay();
  toast(prefs.easy ? "Easy view on: bigger buttons, less text" : "Easy view off");
};
applyDisplay();

document.querySelectorAll("nav button").forEach(b => b.onclick = () => go(b.dataset.view));
detectApi().then(ok => {
  USE_API = ok;
  const mode = document.getElementById("mode");
  if (mode) mode.textContent = ok ? "Connected to the repository API." : "Running on sample data (no backend connected).";
  show(pageFromAddress());
});
