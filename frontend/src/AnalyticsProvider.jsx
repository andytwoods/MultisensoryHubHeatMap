import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { getOrCreateSessionId, isOptedOut, sendBatch, flushBeacon, optOut, optIn } from './tracker';
import { HEARTBEAT_MS } from './constants';

const AnalyticsContext = createContext(null);

export const useAnalytics = () => useContext(AnalyticsContext);

export const AnalyticsProvider = ({ endpoint, children, disabled = false }) => {
  const [optedOut, setOptedOut] = useState(false);
  const queue = useRef([]);
  const sequence = useRef(0);
  const sessionId = useRef(null);
  const heartbeatTimer = useRef(null);

  useEffect(() => {
    setOptedOut(isOptedOut());
  }, []);

  const trackEvent = (type, data = {}) => {
    if (disabled || optedOut) return;
    
    queue.current.push({
      event_type: type,
      event_sequence: sequence.current++,
      timestamp_client: new Date().toISOString(),
      ...data
    });
  };

  const flush = (isUnload = false) => {
    if (queue.current.length === 0 || !endpoint) return;

    const payload = {
      session_id: sessionId.current,
      page_path: window.location.pathname,
      referrer_domain: document.referrer ? new URL(document.referrer).hostname : "",
      events: [...queue.current]
    };

    queue.current = [];

    if (isUnload) {
      flushBeacon(endpoint, payload);
    } else {
      sendBatch(endpoint, payload);
    }
  };

  useEffect(() => {
    if (disabled || optedOut) return;

    sessionId.current = getOrCreateSessionId();
    trackEvent("session_start");

    heartbeatTimer.current = setInterval(() => flush(), HEARTBEAT_MS);

    // IntersectionObserver for dwell-time tracking
    const visibleBlocks = new Map(); // blockId -> { startTime, ratio }
    
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const blockId = entry.target.getAttribute("data-block-id");
        if (!blockId) return;

        if (entry.isIntersecting && entry.intersectionRatio > 0.1) {
          if (!visibleBlocks.has(blockId)) {
            visibleBlocks.set(blockId, { 
              startTime: Date.now(), 
              ratio: entry.intersectionRatio,
              topic: entry.target.getAttribute("data-topic"),
              concept: entry.target.getAttribute("data-concept")
            });
            trackEvent("concept_enter_view", { 
              block_id: blockId,
              topic: entry.target.getAttribute("data-topic"),
              intersection_ratio: entry.intersectionRatio
            });
          }
        } else {
          if (visibleBlocks.has(blockId)) {
            const data = visibleBlocks.get(blockId);
            const duration = (Date.now() - data.startTime) / 1000;
            trackEvent("concept_exit_view", {
              block_id: blockId,
              seconds_visible: duration,
              intersection_ratio: entry.intersectionRatio
            });
            visibleBlocks.delete(blockId);
          }
        }
      });
    }, { threshold: [0, 0.1, 0.5, 0.9] });

    // Helper to find and observe blocks
    const observeBlocks = () => {
      document.querySelectorAll("[data-block-id]").forEach(el => obs.observe(el));
    };
    
    // Initial observation
    observeBlocks();
    
    // Re-observe on changes (simple poll for now, could use MutationObserver)
    const observeInterval = setInterval(observeBlocks, 3000);

    // Heartbeat for visible blocks
    const visibleHeartbeat = setInterval(() => {
      visibleBlocks.forEach((data, blockId) => {
        trackEvent("concept_visible_heartbeat", {
          block_id: blockId,
          topic: data.topic,
          concept: data.concept,
          intersection_ratio: data.ratio,
          seconds_visible: (Date.now() - data.startTime) / 1000
        });
      });
    }, HEARTBEAT_MS);

    const handleVisibility = () => {
      if (document.visibilityState === "hidden") {
        trackEvent("page_hidden");
        flush();
      } else {
        trackEvent("session_resume", { resume_reason: "visibility" });
      }
    };

    const handleClick = (e) => {
      const anchor = e.target.closest('a');
      if (!anchor || !anchor.href) return;

      const url = new URL(anchor.href);
      const isExternal = url.hostname !== window.location.hostname;
      const isDownload = /\.(pdf|docx|xlsx|pptx|zip)$/i.test(url.pathname);

      if (isDownload) {
        trackEvent("download_clicked", { target_path: url.pathname });
      } else if (isExternal) {
        trackEvent("external_link_clicked", { target_domain: url.hostname });
      } else {
        trackEvent("internal_link_clicked", { target_path: url.pathname });
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);
    document.addEventListener("click", handleClick);

    return () => {
      clearInterval(heartbeatTimer.current);
      clearInterval(observeInterval);
      clearInterval(visibleHeartbeat);
      obs.disconnect();
      document.removeEventListener("visibilitychange", handleVisibility);
      document.removeEventListener("click", handleClick);
      flush(true);
    };
  }, [disabled, optedOut, endpoint]);

  const value = {
    trackEvent,
    optOut: () => { optOut(); setOptedOut(true); },
    optIn: () => { optIn(); setOptedOut(false); },
    isOptedOut: () => optedOut
  };

  return (
    <AnalyticsContext.Provider value={value}>
      {children}
    </AnalyticsContext.Provider>
  );
};

export default AnalyticsProvider;
