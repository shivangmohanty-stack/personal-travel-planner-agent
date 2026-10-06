/* No browser storage, no HTML injection, no raw model text. */
"use strict";
const el = id => document.getElementById(id);
let csrf = "";
let messages = [];
let busy = false;
let expiryTimer;
let absoluteExpiry = 0;
const rupees = n => "₹" + Number(n).toLocaleString("en-IN");

function node(tag, text, className) {
  const item = document.createElement(tag);
  if (text !== undefined) item.textContent = text;
  if (className) item.className = className;
  return item;
}
function status(text) { el("status").textContent = text; }
function signedOut() {
  clearTimeout(expiryTimer); absoluteExpiry = 0;
  csrf = ""; messages = []; el("messages").replaceChildren();
  el("message").value = ""; el("password").value = "";
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
  const response = await fetch(path, options);
  const result = await response.json();
  if (path !== "/api/login" && requestCsrf !== csrf) throw new Error("Your session changed. Reload before continuing.");
  if (!response.ok) {
    if (response.status === 401 && path !== "/api/login") signedOut();
    throw new Error(result.detail || "The request failed. Try again.");
  }
  return result;
}
function planNode(plan) {
  const wrap = node("div", undefined, "plan");
  wrap.append(node("p", plan.source, "source"), node("h3", `${plan.trip.days} days in ${plan.trip.destination}`));
  wrap.append(node("p", `${plan.trip.travelers} adult(s) · ${rupees(plan.trip.budget)} total budget · ${plan.trip.interests.join(", ")}`));
  for (const day of plan.itinerary) {
    wrap.append(node("h4", "Day " + day.day));
    for (const activity of day.activities) {
      const row = node("div", `${activity.time} — ${activity.place}`, "activity");
      row.append(node("span", activity.area, "area")); wrap.append(row);
    }
  }
  wrap.append(node("h4", "Estimated budget"));
  const table = node("table"), head = node("tr");
  for (const title of ["Category", "Calculation", "Amount"]) head.append(node("th", title));
  table.append(head);
  for (const item of plan.budget.items) {
    const row = node("tr");
    row.append(node("td", item.category), node("td", `${item.quantity} × ${rupees(item.unit_cost)}`), node("td", rupees(item.amount)));
    table.append(row);
  }
  wrap.append(table, node("p", `Total: ${rupees(plan.budget.total)} · Remaining: ${rupees(plan.budget.remaining)}`, "total"));
  wrap.append(node("h4", "Assumptions & travel tips"));
  const list = node("ul");
  for (const text of [...plan.assumptions, ...plan.tips]) list.append(node("li", text));
  wrap.append(list); return wrap;
}
function render(result) {
  messages = result.messages;
  el("messages").replaceChildren();
  if (!messages.length) el("messages").append(node("p", "Your itinerary will appear here. Use the form to get started.", "empty"));
  for (const message of messages) {
    const bubble = node("div", undefined, "bubble " + message.role);
    if (message.plan) bubble.append(planNode(message.plan)); else bubble.textContent = message.text;
    el("messages").append(bubble);
  }
  if (result.trip) {
    for (const id of ["destination", "days", "travelers", "budget", "stay"]) el(id).value = result.trip[id];
    for (const box of el("interests").querySelectorAll("input")) box.checked = result.trip.interests.includes(box.value);
  }
  el("messages").scrollTop = el("messages").scrollHeight;
}
async function enter() {
  const info = await api("/api/me"); csrf = info.csrf;
  absoluteExpiry = Date.now() + info.expires_in * 1000;
  el("destination").replaceChildren(...info.destinations.map(city => {const option = node("option", city); option.value = city; return option;}));
  el("interests").replaceChildren(...info.interests.map(interest => {
    const label = node("label"), box = node("input"); box.type = "checkbox"; box.value = interest;
    box.checked = ["history", "food"].includes(interest); label.append(box, node("span", interest)); return label;
  }));
  el("mode").textContent = info.demo ? "Offline practice · catalog planner · no Gemini requests" : "Google ADK + Gemini · validated trip details only";
  el("privacy").textContent = info.demo
    ? "Offline practice mode. No trip details are sent to Gemini. Chats are temporary and cleared on sign-out, session expiry, or server restart."
    : "Your chat stays in this app's memory until you clear it, sign out, or your session expires. Validated trip details are sent to Google Gemini to arrange activities. Avoid personal or secret information.";
  render(await api("/api/history")); el("login-panel").hidden = true; el("workspace").hidden = false;
}
async function run(task) {
  if (busy) return;
  busy = true; status("Working…");
  const buttons = document.querySelectorAll("button[type=submit]");
  buttons.forEach(button => button.disabled = true);
  try { await task(); status(""); } catch (error) { status(error.message || "Connection failed. Check that the server is running."); }
  finally { busy = false; buttons.forEach(button => button.disabled = false); }
}
el("login-form").addEventListener("submit", event => {
  event.preventDefault(); run(async () => {
    try {await api("/api/login", {username: el("username").value.trim(), password: el("password").value});}
    finally {el("password").value = "";}
    await enter();
  });
});
el("trip-form").addEventListener("submit", event => {
  event.preventDefault(); run(async () => {
    const interests = [...el("interests").querySelectorAll("input:checked")].map(box => box.value);
    if (!interests.length) throw new Error("Choose at least one interest.");
    render(await api("/api/plan", {destination: el("destination").value, days: Number(el("days").value),
      budget: Number(el("budget").value), travelers: Number(el("travelers").value), stay: el("stay").value, interests}));
  });
});
el("chat-form").addEventListener("submit", event => {
  event.preventDefault(); run(async () => {const text = el("message").value; el("message").value = ""; render(await api("/api/chat", {message:text}));});
});
el("clear").addEventListener("click", () => run(async () => {await api("/api/clear", {}); el("trip-form").reset(); render(await api("/api/history"));}));
el("logout").addEventListener("click", async () => {
  try {await api("/api/logout", {}); signedOut(); status("Signed out. This session's chat was cleared.");}
  catch (error) {status(error.message);}
});
el("export").addEventListener("click", () => {
  if (!messages.length) {status("Create a plan before saving your chat."); return;}
  const content = messages.map(message => {
    if (!message.plan) return `${message.role.toUpperCase()}: ${message.text}`;
    const p = message.plan;
    return `ASSISTANT (${p.source})\n${p.trip.destination}, ${p.trip.days} days, ${p.trip.travelers} adult(s)\n` +
      p.itinerary.map(d => `Day ${d.day}\n` + d.activities.map(a => `${a.time}: ${a.place} (${a.area})`).join("\n")).join("\n\n") +
      "\n\nEstimated budget\n" + p.budget.items.map(i => `${i.category}: ${i.quantity} x ${rupees(i.unit_cost)} = ${rupees(i.amount)}`).join("\n") +
      `\nTotal: ${rupees(p.budget.total)}\nRemaining: ${rupees(p.budget.remaining)}\n` + [...p.assumptions, ...p.tips].join("\n");
  }).join("\n\n");
  const url = URL.createObjectURL(new Blob([content], {type:"text/plain;charset=utf-8"}));
  const link = node("a"); link.href = url; link.download = "travel_conversation.txt"; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000); status("Chat saved to your downloads. Keep exported files private.");
});
enter().catch(() => signedOut());
