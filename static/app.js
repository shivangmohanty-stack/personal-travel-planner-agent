/* Model text is displayed safely; no innerHTML or persistent browser storage. */
"use strict";
const el = id => document.getElementById(id);
let csrf = "", messages = [], busy = false, expiryTimer, absoluteExpiry = 0;
function status(text) { el("status").textContent = text; }
function node(tag, text, className) {
  const item = document.createElement(tag);
  if (text !== undefined) item.textContent = text;
  if (className) item.className = className;
  return item;
}
function signedOut() {
  clearTimeout(expiryTimer); absoluteExpiry = 0; csrf = ""; messages = [];
  el("messages").replaceChildren(); el("message").value = ""; el("password").value = "";
  el("trip-form").reset(); el("workspace").hidden = true; el("login-panel").hidden = false;
}
async function api(path, data) {
  const requestCsrf = csrf;
  if (absoluteExpiry) {
    clearTimeout(expiryTimer);
    expiryTimer = setTimeout(() => {signedOut(); status("Your private session expired. Please sign in again.");},
      Math.max(0, Math.min(900000, absoluteExpiry - Date.now())));
  }
  const options = {credentials: "same-origin", cache: "no-store"};
  if (data !== undefined) {
    options.method = "POST";
    options.headers = {"Content-Type": "application/json", "X-CSRF-Token": csrf};
    options.body = JSON.stringify(data);
  }
  const response = await fetch(path, options), result = await response.json();
  if (path !== "/api/login" && requestCsrf !== csrf) throw new Error("Your session changed. Reload before continuing.");
  if (!response.ok) {
    if (response.status === 401 && path !== "/api/login") signedOut();
    throw new Error(result.detail || "The request failed. Try again.");
  }
  return result;
}
function appendText(parent, text) {
  // A small text-only formatter. Never parse model-supplied HTML or links.
  for (const line of text.split("\n")) {
    const heading = /^(#{1,4})\s+(.+)$/.exec(line);
    const text = (heading ? heading[2] : line).replace(/\*\*(.*?)\*\*/g, "$1");
    parent.append(node(heading ? "h4" : "div", text));
  }
}
function render(result) {
  messages = result.messages; el("messages").replaceChildren();
  if (!messages.length) el("messages").append(node("p", "Where would you like to go? Describe your trip here or use the optional form.", "empty"));
  for (const message of messages) {
    const bubble = node("div", undefined, "bubble " + message.role);
    appendText(bubble, message.text); el("messages").append(bubble);
  }
  el("messages").scrollTop = el("messages").scrollHeight;
}
async function enter() {
  const info = await api("/api/me"); csrf = info.csrf;
  absoluteExpiry = Date.now() + info.expires_in * 1000;
  el("mode").textContent = "Google ADK + Gemini · " + info.model;
  render(await api("/api/history")); el("login-panel").hidden = true; el("workspace").hidden = false;
}
async function run(task) {
  if (busy) return;
  busy = true; status("Checking your request and preparing a thoughtful travel response…");
  const buttons = document.querySelectorAll("button[type=submit]"); buttons.forEach(b => b.disabled = true);
  try {await task(); status("");} catch (error) {status(error.message || "Connection failed. Check that the server is running.");}
  finally {busy = false; buttons.forEach(b => b.disabled = false);}
}
el("login-form").addEventListener("submit", event => {
  event.preventDefault(); run(async () => {
    try {await api("/api/login", {username:el("username").value.trim(), password:el("password").value});}
    finally {el("password").value = "";}
    await enter();
  });
});
el("trip-form").addEventListener("submit", event => {
  event.preventDefault(); run(async () => {
    render(await api("/api/plan", {
      destination:el("destination").value, days:Number(el("days").value), travelers:Number(el("travelers").value),
      budget:el("budget").value ? Number(el("budget").value) : null, currency:el("currency").value.toUpperCase(),
      interests:el("interests").value, accommodation:el("accommodation").value, notes:el("notes").value,
    }));
  });
});
el("chat-form").addEventListener("submit", event => {
  event.preventDefault(); run(async () => {
    const text = el("message").value;
    const result = await api("/api/chat", {message:text}); el("message").value = ""; render(result);
  });
});
el("clear").addEventListener("click", () => run(async () => {
  await api("/api/clear", {}); el("trip-form").reset(); render(await api("/api/history"));
}));
el("logout").addEventListener("click", async () => {
  try {await api("/api/logout", {}); signedOut(); status("Signed out. This session's chat was cleared.");}
  catch (error) {status(error.message);}
});
el("export").addEventListener("click", () => {
  if (!messages.length) {status("Create a conversation before saving your chat."); return;}
  const content = "Live Google ADK + Gemini travel conversation\n\n" + messages.map(m => `${m.role.toUpperCase()}: ${m.text}`).join("\n\n");
  const url = URL.createObjectURL(new Blob([content], {type:"text/plain;charset=utf-8"}));
  const link = node("a"); link.href = url; link.download = "travel_conversation.txt"; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000); status("Chat saved to your downloads. Keep exported files private.");
});
enter().catch(() => signedOut());
