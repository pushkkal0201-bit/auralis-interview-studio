"use strict";
(() => {
  const $ = id => document.getElementById(id);
  let features = [], selected = null, filter = "all", bearer = null, authRequired = false;

  function node(tag, value, className) {
    const e = document.createElement(tag);
    if (value !== undefined) e.textContent = value;
    if (className) e.className = className;
    return e;
  }

  async function authorized(path, options = {}) {
    const headers = {
      ...(options.headers || {}),
      ...(authRequired
        ? (bearer ? { Authorization: "Bearer " + bearer } : {})
        : { "X-Owner-Token": localStorage.getItem("auralis-owner") || "" }),
    };
    if (options.body) headers["Content-Type"] = "application/json";
    const call = () => fetch(path, {
      ...options, credentials: "same-origin", headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    let r = await call();
    if (r.status === 401 && authRequired) {
      const refresh = await fetch("/api/auth/refresh", { method: "POST", credentials: "same-origin" });
      if (refresh.ok) {
        const d = await refresh.json();
        bearer = d.access_token;
        headers.Authorization = "Bearer " + bearer;
        r = await call();
      }
    }
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      const detail = typeof data.detail === "string" ? data.detail : "The request could not be completed.";
      throw new Error(detail);
    }
    return data;
  }

  function render() {
    const list = $("skills");
    list.replaceChildren();
    const visible = features.filter(f => filter === "all" || f.group === filter);
    $("count").textContent = visible.length + " of " + features.length;
    for (const f of visible) {
      const button = node("button", undefined, "skill-button" + (selected?.id === f.id ? " active" : ""));
      button.type = "button";
      button.append(node("strong", f.title));
      button.append(node("small", f.integration.replaceAll("-", " ").toUpperCase() + " · " + f.group.toUpperCase()));
      button.onclick = () => choose(f);
      list.append(button);
    }
    if (!visible.length) list.append(node("p", "No skills in this category."));
  }

  function choose(feature) {
    selected = feature;
    $("selected-title").textContent = feature.title;
    $("selected-kind").textContent = feature.integration.replaceAll("-", " ").toUpperCase();
    $("selected-description").textContent = feature.description;
    $("native-link").hidden = !feature.native_view;
    if (feature.native_view) {
      $("native-link").firstElementChild.textContent = "Related Auralis workspace: " + feature.native_view.replaceAll("-", " ");
    }
    $("result").hidden = true;
    $("message").textContent = "";
    render();
  }

  async function init() {
    try {
      const config = await fetch("/api/public-config").then(r => {
        if (!r.ok) throw new Error("Auralis is unavailable.");
        return r.json();
      });
      authRequired = Boolean(config.authentication_required);
      const response = await authorized("/api/cracked/features");
      features = response.features;
      if (!Array.isArray(features) || !features.length) throw new Error("Skill catalog is empty.");
      choose(features[0]);
    } catch (err) {
      $("message").textContent = err.message +
        (authRequired ? " Sign in from the Auralis homepage, then reopen Career Skills." :
          " Open the Auralis homepage once to initialize the local workspace.");
      $("count").textContent = "Unavailable";
    }
  }

  $("filters").addEventListener("click", event => {
    const target = event.target.closest("button[data-group]");
    if (!target) return;
    filter = target.dataset.group;
    for (const b of $("filters").querySelectorAll("button")) {
      b.classList.toggle("selected", b === target);
    }
    render();
  });

  $("coach-form").addEventListener("submit", async event => {
    event.preventDefault();
    if (!selected) return;
    const submit = $("submit");
    submit.disabled = true;
    $("message").textContent = "Generating guided feedback…";
    $("result").hidden = true;
    try {
      const result = await authorized("/api/cracked/coach", {
        method: "POST",
        body: {
          skill: selected.id, context: $("context").value,
          company: $("company").value,
          ai_model: $("model").value,
          consent: $("consent").checked
        }
      });
      $("answer").textContent = result.response;
      $("next-steps").replaceChildren(...(result.suggestions || []).map(s => node("li", s)));
      $("limitations").replaceChildren(...(result.limitations || []).map(s => node("li", s)));
      $("limitations").append(node("li",
        "No code was executed, no external sources were checked, and no files were changed by this guided session."));
      $("message").textContent = "";
      $("result").hidden = false;
    } catch (err) {
      $("message").textContent = err.message;
    } finally {
      submit.disabled = false;
    }
  });

  init();
})();
