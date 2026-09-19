// Sentinel web UI. No framework, no dependencies.
// Rule for this file: text that came from a scanned file is untrusted. It is only ever placed with
// textContent / createTextNode, never innerHTML.

const cfg = window.SENTINEL_CONFIG || {};
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === false || v == null) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) if (c != null) node.append(c);
  return node;
}

const SVG = "http://www.w3.org/2000/svg";
function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  node.append(...children);
  return node;
}

// ───────────────────────────────────────────────────────── where is the scanner?
const state = { api: null, offline: false, saved: null, samples: [], bundle: null, view: "edit", last: null };

async function getJSON(url, options = {}, ms = 20000) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetch(url, { ...options, signal: ctl.signal });
    const body = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(body.detail || `The scanner answered ${r.status}.`);
    return body;
  } finally { clearTimeout(timer); }
}

// Is this page on the public internet (as opposed to the copy your own computer serves)?
const HOSTED = location.protocol.startsWith("http") && !/^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);

// A hosted scanner is a serverless function. Its first answer after a quiet spell can take several seconds
// ("cold start"), more from another continent. Giving up after 2.5 s used to strand visitors in saved-results mode.
async function findScanner(patience = 20000) {
  const candidates = [];
  if (cfg.apiBase) candidates.push([cfg.apiBase.replace(/\/+$/, ""), patience]);
  if (location.protocol.startsWith("http")) candidates.push(["", patience]);          // the server that served this page
  if (!HOSTED) candidates.push(["http://127.0.0.1:8000", 2500]);                       // never poke a visitor's own machine from a public site
  const seen = new Set();
  for (const [base, ms] of candidates) {
    if (seen.has(base)) continue;
    seen.add(base);
    try {
      const health = await getJSON(base + "/health", {}, ms);
      if (health.engine) return { base, health };
    } catch { /* try the next one */ }
  }
  return null;
}

// Called when we are showing saved results: try again, and switch to the live scanner the moment it answers.
let reconnecting = null;
function reconnect(patience = 15000) {
  if (!state.offline) return Promise.resolve(true);
  if (!reconnecting) {
    reconnecting = findScanner(patience).then(async (found) => {
      reconnecting = null;
      if (!found) return false;
      state.api = found.base; state.offline = false;
      describeScanner();
      try { await loadSamples(); } catch { /* keep the list we have */ }
      return true;
    });
  }
  return reconnecting;
}
function keepTrying(attempt = 0) {
  if (!state.offline || attempt >= 12) return;
  setTimeout(async () => { if (!(await reconnect(10000))) keepTrying(attempt + 1); else if (state.last) scan(); }, 6000);
}

function scannerHost() {
  if (state.api === "" ) return location.host;
  try { return new URL(state.api).host; } catch { return state.api; }
}
const isLocal = () => /^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$/.test(scannerHost());

function describeScanner() {
  const privacy = $("#privacy");
  if (state.offline) {
    privacy.textContent = HOSTED
      ? "The scanner has not answered yet, so this page is showing saved results for the samples. It keeps trying and switches over by itself."
      : "The scanner is not reachable, so this page shows saved results for the samples. To scan your own files, start it with: bash setup.sh";
  } else if (isLocal()) {
    privacy.textContent = "The scanner is running on this computer. Nothing you scan leaves it.";
    $("#api-docs").hidden = false;
    $("#api-docs").href = state.api + "/docs";
  } else {
    privacy.textContent = `Scans are sent to ${scannerHost()}, checked in a temporary folder and deleted. Nothing is stored. Run Sentinel yourself to keep files on your machine.`;
  }
}

// ───────────────────────────────────────────────────────── hidden content
const isPicto = (ch) => /\p{Extended_Pictographic}/u.test(ch);
const isJoiningScript = (ch) => /[\p{L}\p{M}]/u.test(ch) && ch.codePointAt(0) > 0x024f;

function isInvisible(cp) {
  return cp === 0x200b || cp === 0x200c || cp === 0x200d || cp === 0x2060 || cp === 0xfeff || cp === 0x180e ||
    (cp >= 0x202a && cp <= 0x202e) || (cp >= 0x2066 && cp <= 0x2069) ||
    (cp >= 0xe0000 && cp <= 0xe007f) || (cp >= 0xe0100 && cp <= 0xe01ef);
}

// The same allowlist the engine uses: emoji joiners, flags, a byte-order mark, and scripts that need joiners are fine.
function suspiciousAt(chars, i) {
  const cp = chars[i].codePointAt(0);
  if (!isInvisible(cp)) return false;
  if (cp === 0xfeff && i === 0) return false;
  let p = i - 1;
  while (p >= 0 && (chars[p] === "\ufe0f" || (chars[p].codePointAt(0) >= 0x1f3fb && chars[p].codePointAt(0) <= 0x1f3ff))) p--;
  const prev = p >= 0 ? chars[p] : "", next = chars[i + 1] || "";
  if (cp === 0x200d && prev && next && isPicto(prev) && isPicto(next)) return false;
  if ((cp === 0x200c || cp === 0x200d) && prev && next && isJoiningScript(prev) && isJoiningScript(next)) return false;
  return true;
}

function decodeRun(cps) {
  const tags = cps.filter((c) => c >= 0xe0020 && c <= 0xe007e).map((c) => String.fromCharCode(c - 0xe0000)).join("");
  if (tags.length >= 4) return tags;
  const bits = cps.filter((c) => c === 0x200b || c === 0x200c);
  for (const zero of [0x200b, 0x200c]) {
    let out = "";
    for (let k = 0; k + 8 <= bits.length; k += 8) {
      out += String.fromCharCode(parseInt(bits.slice(k, k + 8).map((c) => (c === zero ? "0" : "1")).join(""), 2));
    }
    const printable = [...out].filter((ch) => ch >= " " && ch <= "~").length;
    if (out.length >= 4 && printable / out.length >= 0.9) return out;
  }
  return null;
}

// Split text into plain pieces, hidden-character runs and HTML comments.
function reveal(text) {
  const chars = [...text];
  const parts = [];
  let plain = "", hiddenChars = 0;
  const flush = () => { if (plain) { parts.push({ kind: "text", value: plain }); plain = ""; } };
  for (let i = 0; i < chars.length; i++) {
    if (chars[i] === "\u{1F3F4}") {                         // subdivision flag: black flag + tag characters + cancel tag
      let j = i + 1;
      while (j < chars.length && chars[j].codePointAt(0) >= 0xe0020 && chars[j].codePointAt(0) <= 0xe007e) j++;
      if (j > i + 1 && j < chars.length && chars[j].codePointAt(0) === 0xe007f) { plain += chars.slice(i, j + 1).join(""); i = j; continue; }
    }
    if (suspiciousAt(chars, i)) {
      const cps = [];
      while (i < chars.length && suspiciousAt(chars, i)) { cps.push(chars[i].codePointAt(0)); i++; }
      i--;
      flush();
      hiddenChars += cps.length;
      parts.push({ kind: "hidden", cps, decoded: decodeRun(cps) });
    } else plain += chars[i];
  }
  flush();
  // second pass: HTML comments inside the plain pieces
  const out = [];
  let comments = 0;
  for (const part of parts) {
    if (part.kind !== "text") { out.push(part); continue; }
    let rest = part.value, m;
    while ((m = /<!--[\s\S]*?-->/.exec(rest))) {
      if (m.index) out.push({ kind: "text", value: rest.slice(0, m.index) });
      out.push({ kind: "comment", value: m[0] });
      comments++;
      rest = rest.slice(m.index + m[0].length);
    }
    if (rest) out.push({ kind: "text", value: rest });
  }
  return { parts: out, hiddenChars, comments };
}

const hex = (cp) => "U+" + cp.toString(16).toUpperCase().padStart(4, "0");

function paintReveal() {
  const text = $("#text").value;
  const { parts, hiddenChars, comments } = reveal(text);
  const pill = [];
  if (hiddenChars) pill.push(`${hiddenChars} invisible character${hiddenChars === 1 ? "" : "s"}`);
  if (comments) pill.push(`${comments} comment${comments === 1 ? "" : "s"} that a preview hides`);
  $("#hidden-count").textContent = pill.join(", ");

  const view = $("#agent-view");
  view.replaceChildren();
  for (const part of parts) {
    if (part.kind === "text") view.append(document.createTextNode(part.value));
    else if (part.kind === "comment") view.append(el("span", { class: "cmt", text: part.value, title: "An HTML comment: hidden in a rendered preview, read by the agent" }));
    else if (part.cps.length < 8 && !part.decoded) {
      for (const cp of part.cps) view.append(el("span", { class: "inv", text: hex(cp), title: "An invisible character" }));
    } else {
      const run = el("span", { class: "run" }, el("b", { text: `${part.cps.length} invisible characters` }));
      run.append(document.createTextNode(part.decoded ? ` that spell: “${part.decoded}”` : " (no known encoding)"));
      view.append(run);
    }
  }
  if (!text) view.append(document.createTextNode("Nothing to show yet."));
}

function setView(which) {
  state.view = which;
  const revealing = which === "reveal";
  $("#view-reviewer").setAttribute("aria-pressed", String(!revealing));
  $("#view-agent").setAttribute("aria-pressed", String(revealing));
  if (revealing) paintReveal();
  $("#text").hidden = revealing || !!state.bundle;
  $("#agent-view").hidden = !revealing || !!state.bundle;
  $("#file-list").hidden = !state.bundle;
}

// ───────────────────────────────────────────────────────── samples
async function loadSamples() {
  if (state.offline) state.samples = state.saved.samples.map(({ file, title, description, result }) => ({ file, title, description, verdict: result.verdict }));
  else state.samples = await getJSON(state.api + "/samples");
  const list = $("#samples");
  list.replaceChildren(...state.samples.map((s) =>
    el("li", {}, el("button", { type: "button", "data-file": s.file, "data-verdict": s.verdict || "",
      title: s.verdict ? `${s.description}. Result: ${s.verdict.toLowerCase()}.` : s.description, onclick: () => pickSample(s.file) }, s.title))));
}

async function pickSample(file) {
  $$("#samples button").forEach((b) => b.setAttribute("aria-current", String(b.dataset.file === file)));
  $("#sample-desc").textContent = (state.samples.find((s) => s.file === file) || {}).description || "";
  clearBundle();
  try {
    const text = state.offline ? state.saved.samples.find((s) => s.file === file).text
                               : (await getJSON(`${state.api}/samples/${encodeURIComponent(file)}`)).text;
    $("#filename").value = file;
    $("#text").value = text;
    const hidden = reveal(text);
    setView(hidden.hiddenChars || hidden.comments ? "reveal" : "edit");
    if (state.view !== "reveal") paintRevealCountOnly();
    await scan();
  } catch (e) { showError(e); }
}

function paintRevealCountOnly() {
  const { hiddenChars, comments } = reveal($("#text").value);
  const pill = [];
  if (hiddenChars) pill.push(`${hiddenChars} invisible character${hiddenChars === 1 ? "" : "s"}`);
  if (comments) pill.push(`${comments} comment${comments === 1 ? "" : "s"} that a preview hides`);
  $("#hidden-count").textContent = pill.join(", ");
}

// ───────────────────────────────────────────────────────── uploads
const SURFACE = new RegExp([
  "^(CLAUDE\\.md|AGENTS\\.md|GEMINI\\.md|\\.cursorrules|\\.mcp\\.json)$", "^\\.github/copilot-instructions\\.md$",
  "^\\.claude/settings(\\.local)?\\.json$", "^\\.gemini/settings\\.json$", "^\\.vscode/(tasks|mcp)\\.json$",
  "^\\.cursor/mcp\\.json$", "^\\.cursor/rules/[^/]+\\.mdc$", "(^|/)SKILL\\.md$",
].join("|"));
const SKIP_DIR = /(^|\/)(node_modules|\.git|dist|build|\.venv|venv|__pycache__)\//;
const SCRIPT_TOKEN = /[\w@.\-/]+\.(?:mjs|cjs|js|ts|py|sh|ps1|rb|pl)\b/g;
const MAX_BYTES = 2_000_000;

function clearBundle() {
  state.bundle = null;
  $("#file-list").replaceChildren();
  $("#scan-btn").textContent = "Scan this file";
  $("#filename").disabled = false;
}

async function takeFiles(fileList, fromFolder) {
  const files = [...fileList].filter((f) => f.size <= MAX_BYTES);
  if (!files.length) return;
  if (!fromFolder && files.length === 1) {                                  // one file: show it in the editor
    clearBundle();
    $("#filename").value = files[0].name;
    $("#text").value = await files[0].text();
    setView("edit"); paintRevealCountOnly();
    return scan();
  }
  const rel = (f) => (fromFolder ? (f.webkitRelativePath || f.name).split("/").slice(1).join("/") : f.name);
  const all = new Map(files.map((f) => [rel(f), f]).filter(([p]) => p && !SKIP_DIR.test(p)));
  const chosen = new Map();
  for (const [path, f] of all) if (!fromFolder || SURFACE.test(path)) chosen.set(path, await f.text());
  if (fromFolder) {                                                         // add the scripts that hooks and tasks point to
    for (const text of [...chosen.values()]) {
      for (const token of text.match(SCRIPT_TOKEN) || []) {
        const path = token.replace(/^\$\{?CLAUDE_PROJECT_DIR\}?\//, "").replace(/^\.\//, "");
        if (all.has(path) && !chosen.has(path) && chosen.size < 200) chosen.set(path, await all.get(path).text());
      }
    }
  }
  if (!chosen.size) return showNotice("No files an agent obeys were found in that folder. Sentinel looks for CLAUDE.md, AGENTS.md, .cursorrules, .claude/settings.json, .vscode/tasks.json, .mcp.json and similar.");
  state.bundle = chosen;
  $("#hidden-count").textContent = "";
  $("#file-list").replaceChildren(...[...chosen].map(([path, text]) =>
    el("li", {}, el("span", { text: path }), el("span", { text: `${text.length.toLocaleString()} characters` }))));
  $("#scan-btn").textContent = `Scan these ${chosen.size} files`;
  $("#filename").disabled = true;
  setView("edit");
  return scan();
}

// ───────────────────────────────────────────────────────── scanning
async function scan() {
  const btn = $("#scan-btn");
  const label = btn.textContent;
  try {
    let result;
    if (state.offline) { btn.disabled = true; btn.textContent = "Waking the scanner"; await reconnect(); }
    if (state.bundle) {
      if (state.offline) return showNotice(OFFLINE_HELP);
      btn.disabled = true; btn.textContent = "Scanning";
      result = await getJSON(state.api + "/scan/bundle", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files: Object.fromEntries(state.bundle) }) }, 30000);
    } else {
      const text = $("#text").value, filename = $("#filename").value.trim() || "CLAUDE.md";
      if (!text.trim()) return showNotice("There is nothing to scan yet. Paste a file, upload one, or pick a sample.");
      if (state.offline) {
        const saved = state.saved.samples.find((s) => s.file === filename && s.text === text);
        if (!saved) return showNotice(OFFLINE_HELP);
        result = saved.result;
      } else {
        btn.disabled = true; btn.textContent = "Scanning";
        result = await getJSON(state.api + "/scan/text", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename, text }) }, 30000);
      }
    }
    state.last = result;
    showResult(result);
  } catch (e) { showError(e); } finally { btn.disabled = false; btn.textContent = label; }
}

const OFFLINE_HELP = HOSTED
  ? "The scanner is still starting up and did not answer in time. Wait a few seconds and press Scan again."
  : "Scanning your own files needs the scanner running. Start it with: bash setup.sh";

const VERDICT = {
  CLEAN: ["Clean", "Nothing here steers an agent somewhere it should not go. That means checked, not safe."],
  SUSPICIOUS: ["Suspicious", "Something here needs a person to approve it before an agent runs in this project."],
  COMPROMISED: ["Compromised", "This would make an agent do something harmful. Do not open the project in an agent until it is fixed."],
};

function findingRow(f) {
  const weight = f.forces_compromised ? "decisive" : f.ceiling ? "needs approval" : f.penalty ? `−${f.penalty}` : "note only";
  const kind = f.forces_compromised ? "decisive" : f.ceiling ? "approval" : f.penalty ? "penalty" : "note";
  const evidence = f.line ? `line ${f.line}: ${f.message}` : f.message;
  return el("li", { "data-weight": kind },
    el("div", { class: "f-top" }, el("span", { class: "f-title", text: f.rule_name }), el("span", { class: "f-meta", text: `${f.rule_id}, ${weight}` })),
    el("dl", { class: "f-body" },
      el("dt", { text: "What happens" }), el("dd", { text: f.impact || f.reconstruction || "" }),
      el("dt", { text: "What to do" }), el("dd", { text: f.fix || "" }),
      el("dt", { text: "Evidence" }), el("dd", { class: "ev", text: evidence })));
}

const VERDICT_MARK = { CLEAN: "m8.6 12.3 2.5 2.5 4.6-5", SUSPICIOUS: "M12 7.6v5.2M12 15.9v.2", COMPROMISED: "m9.2 9.4 5.6 5.6m0-5.6-5.6 5.6" };

function verdictIcon(verdict) {
  return svg("svg", { class: "verdict-icon", viewBox: "0 0 24 24", "aria-hidden": "true" },
    svg("path", { class: "vi-body", d: "M12 2.4 4.2 5.3v6.4c0 4.8 3.1 8.7 7.8 10.2 4.7-1.5 7.8-5.4 7.8-10.2V5.3L12 2.4Z" }),
    svg("path", { class: "vi-mark", d: VERDICT_MARK[verdict] || VERDICT_MARK.SUSPICIOUS }));
}

function showResult(result) {
  const files = result.files || [result];                                   // a bundle has .files; a single scan is one result
  const verdict = result.verdict;
  const score = Math.min(...files.map((f) => f.trust_score), 100);
  const [word, line] = VERDICT[verdict] || [verdict, ""];
  const pane = $("#result");
  pane.dataset.verdict = verdict;

  const pin = el("span", { class: "gauge-pin" });
  const head = [];
  if (state.offline) head.push(el("p", { class: "notice banner", text: "Saved result. The scanner is not running, so this is what it returned for this sample when the page was built." }));
  head.push(el("div", { class: "verdict" },
    verdictIcon(verdict),
    el("div", { class: "verdict-word", text: word }),
    el("div", { class: "score" }, el("span", { class: "score-num", text: String(score) }), el("span", { class: "score-of", text: " of 100" })),
    el("p", { class: "verdict-line", text: line }),
    el("div", { class: "gauge", role: "img", "aria-label": `Trust score ${score} of 100. 39 or less is compromised, 40 to 79 is suspicious, 80 or more is clean.` },
      el("div", { class: "gauge-track" }, el("i"), el("i"), el("i"), pin),
      el("div", { class: "gauge-labels", "aria-hidden": "true" }, el("span", { text: "compromised" }), el("span", { text: "suspicious" }), el("span", { text: "clean" })))));

  const body = [];
  for (const f of files) {
    if (state.bundle || files.length > 1) body.push(el("p", { class: "file-head", text: `${f.filename}  (${(VERDICT[f.verdict] || [f.verdict])[0].toLowerCase()}, ${f.trust_score})` }));
    if (f.findings.length) body.push(el("ul", { class: "findings" }, f.findings.map(findingRow)));
  }
  if (!files.some((f) => f.findings.length)) body.push(el("p", { class: "hint", text: "No findings." }));
  if (state.bundle) {
    const flagged = new Set(files.map((f) => f.filename));
    const quiet = [...state.bundle.keys()].filter((p) => !flagged.has(p));
    if (quiet.length && flagged.size) body.push(el("p", { class: "hint quiet-files", text: `No findings in: ${quiet.join(", ")}` }));
  }

  const breakdown = files.flatMap((f) => f.breakdown || []);
  if (breakdown.length) body.push(el("details", { class: "calc" }, el("summary", { text: "How this score was calculated" }),
    el("pre", { text: breakdown.join("\n") + "\n\n80 or more is clean, 40 to 79 is suspicious, 39 or less is compromised.\nA decisive finding makes the verdict compromised whatever the arithmetic says." })));

  body.push(el("div", { class: "result-actions" },
    el("button", { class: "btn quiet", type: "button", text: "Copy result as JSON", onclick: (e) => copy(JSON.stringify(result, null, 2), e.currentTarget, "Copy result as JSON") }),
    el("button", { class: "btn quiet", type: "button", text: "Download result", onclick: () => download(result) })));

  pane.replaceChildren(...head, el("div", { class: "result-body" }, body));
  requestAnimationFrame(() => pin.style.setProperty("left", `${Math.min(Math.max(score, 1), 99)}%`));
  $("#where").textContent = state.offline ? "" : isLocal() ? "Scanned on this computer." : `Scanned by ${scannerHost()}. Nothing is stored.`;
}

function showNotice(message, isError = false) {
  delete $("#result").dataset.verdict;
  $("#result").replaceChildren(el("p", { class: "notice" + (isError ? " error" : ""), text: message }));
}
function showError(e) {
  const aborted = e && e.name === "AbortError";
  showNotice(aborted ? "The scanner took too long to answer. Check that it is still running, then scan again."
    : e instanceof TypeError ? (HOSTED ? "The scanner could not be reached. Check your connection and press Scan again." : "The scanner could not be reached. Start it with: bash setup.sh")
    : String(e.message || e), true);
}

async function copy(text, button, label) {
  try { await navigator.clipboard.writeText(text); }
  catch { const t = el("textarea", { text }); document.body.append(t); t.select(); document.execCommand("copy"); t.remove(); }
  button.textContent = "Copied";
  setTimeout(() => { button.textContent = label; }, 1600);
}
function download(result) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }));
  el("a", { href: url, download: "sentinel-result.json" }).click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ───────────────────────────────────────────────────────── tabs, chart, wiring
function tabs(list) {
  const buttons = $$('[role="tab"]', list);
  const select = (btn) => {
    buttons.forEach((b) => {
      const on = b === btn;
      b.setAttribute("aria-selected", String(on));
      b.tabIndex = on ? 0 : -1;
      document.getElementById(b.getAttribute("aria-controls")).hidden = !on;
    });
    list.dispatchEvent(new CustomEvent("tabchange", { detail: btn.id }));
  };
  buttons.forEach((b, i) => {
    b.addEventListener("click", () => select(b));
    b.addEventListener("keydown", (e) => {
      const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!step) return;
      const next = buttons[(i + step + buttons.length) % buttons.length];
      next.focus(); select(next);
    });
  });
}

// Every square is one project; filled squares are read left to right, top to bottom. Drawn from the numbers in the markup.
function drawWaffle(box) {
  const total = +box.dataset.total, flagged = +box.dataset.flagged, cols = 31, size = 8, gap = 2.5, step = size + gap;
  const rows = Math.ceil(total / cols);
  const chart = svg("svg", { viewBox: `0 0 ${cols * step - gap} ${rows * step - gap}`, role: "img",
    "aria-label": `${total - flagged} of ${total} healthy projects pass; ${flagged} are wrongly blocked` });
  for (let i = 0; i < total; i++) {
    chart.append(svg("rect", { class: i < flagged ? "cell on" : "cell", x: (i % cols) * step, y: Math.floor(i / cols) * step, width: size, height: size, rx: 2 }));
  }
  box.replaceChildren(chart);
}
function drawDots(box) {
  const total = +box.dataset.total, filled = +box.dataset.filled;
  const dots = Array.from({ length: total }, (_, i) => el("i", { class: i < filled ? "on" : "" }));
  if (box.dataset.after) dots.push(el("span", { class: "after", text: box.dataset.after }));
  box.replaceChildren(...dots);
}

function wire() {
  $$('[role="tablist"]').forEach(tabs);
  $('#scan [role="tablist"]').addEventListener("tabchange", (e) => {
    if (e.detail === "tab-paste") { clearBundle(); setView("edit"); $("#text").focus(); }
  });
  $("#view-reviewer").addEventListener("click", () => setView("edit"));
  $("#view-agent").addEventListener("click", () => setView("reveal"));
  $("#text").addEventListener("input", () => { paintRevealCountOnly(); $$("#samples button").forEach((b) => b.setAttribute("aria-current", "false")); });
  $("#scan-btn").addEventListener("click", scan);
  $("#pick-files").addEventListener("change", (e) => takeFiles(e.target.files, false));
  $("#pick-folder").addEventListener("change", (e) => takeFiles(e.target.files, true));
  const drop = $("#drop");
  ["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => takeFiles(e.dataTransfer.files, false));
  $$(".copy").forEach((b) => b.addEventListener("click", () => copy($("code", b.parentElement).textContent, b, b.textContent)));

  $$(".waffle").forEach(drawWaffle);
  $$(".dots").forEach(drawDots);
}

async function start() {
  wire();
  $("#privacy").textContent = HOSTED ? "Waking the scanner. The first visit after a quiet spell can take a few seconds." : "Looking for the scanner.";
  $("#empty .empty-title").textContent = HOSTED ? "Waking the scanner." : "Looking for the scanner.";
  const found = await findScanner();
  if (found) state.api = found.base;
  else {
    try { state.saved = window.SENTINEL_SAVED || await getJSON("saved-results.json"); state.offline = true; }
    catch { describeOff(); return; }
    keepTrying();
  }
  describeScanner();
  try {
    await loadSamples();
    const first = state.samples.find((s) => s.file === "trapdoor_style_demo.md") || state.samples[0];
    if (first) await pickSample(first.file);                                // open with the most characteristic thing: hidden text, revealed
  } catch (e) { showError(e); }
}
function describeOff() {
  $("#privacy").textContent = HOSTED ? "The scanner did not answer. Reload the page in a few seconds." : "The scanner is not reachable. Start it with: bash setup.sh";
  showNotice(HOSTED ? "The scanner did not answer. Reload the page in a few seconds." : "The scanner could not be reached. Start it with: bash setup.sh", true);
}

start();

export { reveal, decodeRun };                                               // for tests
