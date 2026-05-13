import { OPTOUT_KEY, SESSION_KEY } from "./constants";

export const isOptedOut = () => {
  try {
    return localStorage.getItem(OPTOUT_KEY) === "1";
  } catch (e) {
    return false;
  }
};

export const optOut = () => {
  try {
    localStorage.setItem(OPTOUT_KEY, "1");
  } catch (e) {}
};

export const optIn = () => {
  try {
    localStorage.removeItem(OPTOUT_KEY);
  } catch (e) {}
};

export const getOrCreateSessionId = () => {
  try {
    let sid = sessionStorage.getItem(SESSION_KEY);
    if (!sid) {
      sid = crypto.randomUUID();
      sessionStorage.setItem(SESSION_KEY, sid);
    }
    return sid;
  } catch (e) {
    return "fallback-session-" + Date.now();
  }
};

export const sendBatch = async (endpoint, payload) => {
  if (!endpoint) return;
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      console.warn("Analytics ingest failed", response.status);
    }
  } catch (e) {
    console.warn("Analytics ingest error", e);
  }
};

export const flushBeacon = (endpoint, payload) => {
  if (!endpoint) return;
  try {
    if (navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify(payload)], { type: "text/plain" });
      navigator.sendBeacon(endpoint, blob);
    } else {
      sendBatch(endpoint, payload);
    }
  } catch (e) {
    sendBatch(endpoint, payload);
  }
};
