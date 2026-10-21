import { useCallback, useEffect, useMemo, useRef } from 'react';

/**
 * Trailing-edge debounce for event handlers that trigger work you don't want to
 * run on every keystroke (network calls, expensive side effects).
 *
 * The returned function is stable across renders, and so are `flush`/`cancel`,
 * so handlers can be handed to memoized children without breaking React.memo.
 *
 *   const { debounced: save, flush: flushSave } = useDebouncedCallback(saveFn, 800);
 *   onChange={e => save(e.target.value)}   // fires 800ms after the last change
 *   onBlur={flushSave}                     // fires immediately if a call is pending
 *
 * Note: never use this to defer the value that a controlled <input> renders —
 * that makes typing lag. Debounce the side effect instead.
 */
export function useDebouncedCallback(callback, delay) {
  const callbackRef = useRef(callback);
  const timerRef    = useRef(null);
  const argsRef     = useRef([]);

  // Keep the latest callback without restarting any pending timer.
  useEffect(() => { callbackRef.current = callback; }, [callback]);

  const cancel = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    argsRef.current = [];
  }, []);

  const flush = useCallback(() => {
    if (!timerRef.current) return;
    clearTimeout(timerRef.current);
    timerRef.current = null;
    const args = argsRef.current;
    argsRef.current = [];
    callbackRef.current(...args);
  }, []);

  const debounced = useCallback((...args) => {
    argsRef.current = args;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      timerRef.current = null;
      const pending = argsRef.current;
      argsRef.current = [];
      callbackRef.current(...pending);
    }, delay);
  }, [delay]);

  // Drop any pending call on unmount so it can't fire against a dead component
  // (or re-issue a request the user already navigated away from).
  useEffect(() => cancel, [cancel]);

  return useMemo(() => ({ debounced, flush, cancel }), [debounced, flush, cancel]);
}

export default useDebouncedCallback;
