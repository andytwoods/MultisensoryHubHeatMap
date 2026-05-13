import { isOptedOut, optOut, optIn, getOrCreateSessionId } from "../tracker";

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  // Mock crypto.randomUUID
  Object.defineProperty(global, 'crypto', {
    value: {
      randomUUID: () => 'test-uuid-' + Math.random()
    }
  });
});

test("not opted out by default", () => {
  expect(isOptedOut()).toBe(false);
});

test("optOut sets key", () => {
  optOut();
  expect(isOptedOut()).toBe(true);
});

test("optIn clears key", () => {
  optOut();
  optIn();
  expect(isOptedOut()).toBe(false);
});

test("getOrCreateSessionId returns stable ID within session", () => {
  const id1 = getOrCreateSessionId();
  const id2 = getOrCreateSessionId();
  expect(id1).toBe(id2);
  expect(id1.length).toBeGreaterThan(8);
});

test("getOrCreateSessionId creates new ID in new session", () => {
  const id1 = getOrCreateSessionId();
  sessionStorage.clear();
  const id2 = getOrCreateSessionId();
  expect(id1).not.toBe(id2);
});
