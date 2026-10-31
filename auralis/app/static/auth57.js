
"use strict";

/*
 * Auralis 5.7.2
 * Authentication frontend
 *
 * Access tokens are stored in memory.
 * The refresh cookie is HttpOnly and handled server-side.
 */

function authHeader() {
  if (window.auralisAuth?.enabled) {
    return window.auralisAuth.token
      ? {
          Authorization: "Bearer " + window.auralisAuth.token,
        }
      : {};
  }

  return {
    "X-Owner-Token": typeof owner !== "undefined" ? owner : "",
  };
}

/* =========================================================
   AUTHENTICATION STATE
   ========================================================= */

const auralisAuth = {
  enabled: false,
  token: null,
  user: null,
  ready: null,

  async refresh() {
    try {
      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "same-origin",
      });

      if (!response.ok) {
        this.token = null;
        this.user = null;
        return false;
      }

      const data = await response.json();

      if (!data.access_token || !data.user) {
        this.token = null;
        this.user = null;
        return false;
      }

      this.token = data.access_token;
      this.user = data.user;

      return true;
    } catch {
      this.token = null;
      this.user = null;
      return false;
    }
  },

  async logout() {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "same-origin",
        headers: this.token
          ? { Authorization: "Bearer " + this.token }
          : {},
      });
    } catch (error) {
      console.warn("Logout request failed:", error);
    }

    this.token = null;
    this.user = null;

    localStorage.removeItem("auralis-current");

    if (typeof session !== "undefined") {
      session = null;
    }

    const authPanel = document.getElementById("account-auth");
    if (authPanel) authPanel.hidden = false;

    document.body.classList.add("auth-locked");

    const passwordField = document.getElementById(
      "account-password"
    );

    if (passwordField) passwordField.value = "";

    authMessage("");
  },

  setSession(data) {
    if (!data?.access_token || !data?.user) {
      throw new Error("Invalid authentication response.");
    }

    this.token = data.access_token;
    this.user = data.user;

    const authPanel = document.getElementById("account-auth");
    if (authPanel) authPanel.hidden = true;

    document.body.classList.remove("auth-locked");

    const emailLabel = document.getElementById(
      "account-email-label"
    );

    if (emailLabel) {
      emailLabel.textContent = this.user?.email || "Account";
    }

    window.auralisOnLogin?.();
  },
};

window.auralisAuth = auralisAuth;

/* =========================================================
   AUTH MESSAGE HANDLING
   ========================================================= */

function authMessage(message, error = false) {
  const box = document.getElementById("account-message");

  if (!box) return;

  box.textContent = String(message ?? "");
  box.classList.toggle("error", Boolean(error));
}

/*
 * Convert FastAPI / Pydantic validation errors
 * into readable messages.
 *
 * Fixes:
 * [object Object],[object Object]
 */

function authErrorText(detail) {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => authErrorText(item))
      .filter(Boolean)
      .join("; ");
  }

  if (detail && typeof detail === "object") {
    const message =
      detail.msg ||
      detail.message ||
      detail.error ||
      detail.detail;

    const readableMessage = authErrorText(message);

    if (readableMessage) {
      const location = Array.isArray(detail.loc)
        ? detail.loc.filter((part) => part !== "body").join(".")
        : "";

      return location
        ? `${location}: ${readableMessage}`
        : readableMessage;
    }
  }

  return "";
}

/* =========================================================
   AUTH API REQUEST
   ========================================================= */

async function authSubmit(path, payload) {
  let response;

  try {
    response = await fetch("/api/auth/" + path, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...(path === "password" ? authHeader() : {}),
      },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error(
      "Unable to connect to the server. Please try again."
    );
  }

  const result = await response.json().catch(() => ({
    detail: "The server returned an invalid response.",
  }));

  if (!response.ok) {
    const message =
      authErrorText(result.detail) ||
      authErrorText(result.message) ||
      "Account request failed. Please try again.";

    throw new Error(message);
  }

  return result;
}

/* =========================================================
   FORM VALIDATION
   ========================================================= */

function validateAuthForm(form, requirePassword = true) {
  const emailField = document.getElementById("account-email");
  const passwordField = document.getElementById(
    "account-password"
  );

  if (!emailField?.value.trim()) {
    authMessage("Please enter your email address.", true);
    emailField?.focus();
    return false;
  }

  if (requirePassword && !passwordField?.value) {
    authMessage("Please enter your password.", true);
    passwordField?.focus();
    return false;
  }

  if (form && !form.reportValidity()) {
    return false;
  }

  return true;
}

/* =========================================================
   BOOT AUTHENTICATION
   ========================================================= */

async function bootAuth() {
  let config;

  try {
    const response = await fetch("/api/public-config");

    if (!response.ok) {
      throw new Error("Configuration unavailable");
    }

    config = await response.json();
  } catch (error) {
    console.error("Authentication initialization:", error);
    return;
  }

  if (!config.authentication_required) {
    return;
  }

  const privacyCopy = document.querySelector(
    ".privacy-panel p"
  );

  if (privacyCopy) {
    privacyCopy.textContent =
      "Your interview records, uploaded CV details, " +
      "assessments and learning history are stored " +
      "with your verified account in the hosted database. " +
      "You can delete Auralis data here. " +
      "Removing your Supabase sign-in identity is a " +
      "separate support request.";
  }

  const deleteButton = document.getElementById("delete-all");

  if (deleteButton) {
    deleteButton.textContent = "Delete my Auralis records";
  }

  const accountRemoval = document.getElementById(
    "account-removal"
  );

  if (accountRemoval) {
    accountRemoval.hidden = false;
  }

  auralisAuth.enabled = true;

  const authPanel = document.getElementById("account-auth");

  if (authPanel) {
    authPanel.hidden = false;
  }

  document.body.classList.add("auth-locked");

  const menu = document.getElementById("account-controls");

  if (menu) {
    menu.hidden = false;
  }

  /* Password recovery */

  const params = new URLSearchParams(
    location.hash.substring(1)
  );

  if (
    params.get("type") === "recovery" &&
    params.get("access_token")
  ) {
    auralisAuth.token = params.get("access_token");

    history.replaceState(
      null,
      "",
      location.pathname + location.search
    );

    const resetForm = document.getElementById(
      "account-password-reset"
    );

    const credentialsForm = document.getElementById(
      "account-credentials"
    );

    if (resetForm) resetForm.hidden = false;
    if (credentialsForm) credentialsForm.hidden = true;

    authMessage("Choose a new password for your account.");

    return;
  }

  /* Restore authenticated session */

  if (await auralisAuth.refresh()) {
    auralisAuth.setSession({
      access_token: auralisAuth.token,
      user: auralisAuth.user,
    });
  }
}

auralisAuth.ready = bootAuth();

/* =========================================================
   AUTHENTICATION EVENT HANDLERS
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById(
    "account-credentials"
  );

  if (!form) {
    console.error("Auralis authentication form not found.");
    return;
  }

  /* -------------------------
     SIGN IN
     ------------------------- */

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    authMessage("");

    if (!validateAuthForm(form)) return;

    const submit = document.getElementById("account-login");

    if (submit?.disabled) return;
    if (submit) submit.disabled = true;

    try {
      const data = await authSubmit("login", {
        email: document
          .getElementById("account-email")
          .value.trim(),
        password: document.getElementById(
          "account-password"
        ).value,
      });

      auralisAuth.setSession(data);
    } catch (error) {
      authMessage(
        error.message || "Sign in failed.",
        true
      );
    } finally {
      if (submit) submit.disabled = false;
    }
  });

  /* -------------------------
     CREATE ACCOUNT
     ------------------------- */

  const registerButton = document.getElementById(
    "account-register"
  );

  registerButton?.addEventListener("click", async (event) => {
    event.preventDefault();
    authMessage("");

    if (!validateAuthForm(form)) return;

    if (registerButton.disabled) return;
    registerButton.disabled = true;

    try {
      const data = await authSubmit("signup", {
        email: document
          .getElementById("account-email")
          .value.trim(),
        password: document.getElementById(
          "account-password"
        ).value,
      });

      if (data.verification_required) {
        authMessage(
          data.message ||
            "Account created. Check your email to verify it."
        );
      } else {
        auralisAuth.setSession(data);
      }
    } catch (error) {
      authMessage(
        error.message || "Account creation failed.",
        true
      );
    } finally {
      registerButton.disabled = false;
    }
  });

  /* -------------------------
     FORGOT PASSWORD
     ------------------------- */

  const forgotButton = document.getElementById(
    "account-forgot"
  );

  forgotButton?.addEventListener("click", async (event) => {
    event.preventDefault();
    authMessage("");

    if (!validateAuthForm(null, false)) return;

    if (forgotButton.disabled) return;
    forgotButton.disabled = true;

    try {
      const data = await authSubmit("recover", {
        email: document
          .getElementById("account-email")
          .value.trim(),
      });

      authMessage(
        data.message ||
          "If the account exists, recovery instructions will be sent."
      );
    } catch (error) {
      authMessage(
        error.message || "Password recovery failed.",
        true
      );
    } finally {
      forgotButton.disabled = false;
    }
  });

  /* -------------------------
     RESET PASSWORD
     ------------------------- */

  const resetForm = document.getElementById(
    "account-password-reset"
  );

  resetForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    authMessage("");

    if (!resetForm.reportValidity()) return;

    const submit = resetForm.querySelector(
      'button[type="submit"]'
    );

    if (submit?.disabled) return;
    if (submit) submit.disabled = true;

    try {
      await authSubmit("password", {
        password: document.getElementById(
          "account-new-password"
        ).value,
      });

      await auralisAuth.logout();

      resetForm.hidden = true;
      form.hidden = false;

      authMessage(
        "Password updated. Sign in with your new password."
      );
    } catch (error) {
      authMessage(
        error.message || "Password update failed.",
        true
      );
    } finally {
      if (submit) submit.disabled = false;
    }
  });

  /* -------------------------
     DELETE ACCOUNT
     ------------------------- */

  const removalForm = document.getElementById(
    "account-removal-form"
  );

  removalForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const feedback = document.getElementById(
      "account-removal-message"
    );

    const submit = removalForm.querySelector(
      'button[type="submit"]'
    );

    if (!removalForm.reportValidity()) return;

    if (
      !confirm(
        "Permanently close this account and delete " +
          "the saved Auralis data?"
      )
    ) {
      return;
    }

    if (submit?.disabled) return;
    if (submit) submit.disabled = true;

    try {
      const response = await fetch(
        "/api/auth/delete-account",
        {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            ...authHeader(),
          },
          body: JSON.stringify({
            password: document.getElementById(
              "account-remove-password"
            ).value,
            confirmation: document.getElementById(
              "account-remove-confirmation"
            ).value,
          }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          authErrorText(data.detail) ||
            "Account deletion could not be completed."
        );
      }

      await auralisAuth.logout();

      if (feedback) {
        feedback.textContent =
          "Your account and Auralis records were removed.";
      }

      removalForm.reset();
    } catch (error) {
      if (feedback) {
        feedback.textContent =
          error.message || "Account deletion failed.";
      }
    } finally {
      if (submit) submit.disabled = false;
    }
  });

  /* -------------------------
     LOGOUT
     ------------------------- */

  const logoutButton = document.getElementById(
    "account-logout"
  );

  if (logoutButton) {
    logoutButton.onclick = () => auralisAuth.logout();
  }
});
