import {
  useCallback,
  useEffect,
  useRef,
  type DependencyList,
  type RefObject,
} from 'react';

const DEFAULT_BOTTOM_THRESHOLD_PX = 96;
const DEFAULT_BOTTOM_THRESHOLD_VIEWPORT_RATIO = 0.6;
const DEFAULT_MAX_BOTTOM_THRESHOLD_PX = 420;

interface StickyChatScrollOptions {
  readonly bottomThresholdPx?: number;
}

interface StickyChatScrollController<T extends HTMLElement> {
  readonly scrollRef: RefObject<T>;
  readonly onScroll: () => void;
  readonly scrollToBottom: () => void;
}

const isNearBottom = (el: HTMLElement, bottomThresholdPx: number): boolean => {
  const distance = Number(el.scrollHeight || 0) - Number(el.scrollTop || 0) - Number(el.clientHeight || 0);
  const adaptiveThreshold = Math.max(
    bottomThresholdPx,
    Math.min(
      DEFAULT_MAX_BOTTOM_THRESHOLD_PX,
      Number(el.clientHeight || 0) * DEFAULT_BOTTOM_THRESHOLD_VIEWPORT_RATIO,
    ),
  );
  return distance <= adaptiveThreshold;
};

export const useStickyChatScroll = <T extends HTMLElement>(
  deps: DependencyList,
  options: StickyChatScrollOptions = {},
): StickyChatScrollController<T> => {
  const scrollRef = useRef<T>(null);
  const pinnedToBottomRef = useRef<boolean>(true);
  const frameRef = useRef<number | null>(null);
  const fallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bottomThresholdPx = options.bottomThresholdPx ?? DEFAULT_BOTTOM_THRESHOLD_PX;

  const cancelPendingScroll = useCallback(() => {
    if (frameRef.current !== null && typeof window.cancelAnimationFrame === 'function') {
      window.cancelAnimationFrame(frameRef.current);
    }
    frameRef.current = null;
    if (fallbackTimerRef.current !== null) {
      clearTimeout(fallbackTimerRef.current);
      fallbackTimerRef.current = null;
    }
  }, []);

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    pinnedToBottomRef.current = isNearBottom(el, bottomThresholdPx);
  }, [bottomThresholdPx]);

  const requestScrollToBottom = useCallback(() => {
    if (frameRef.current !== null || fallbackTimerRef.current !== null) return;
    const run = () => {
      frameRef.current = null;
      if (fallbackTimerRef.current !== null) {
        clearTimeout(fallbackTimerRef.current);
        fallbackTimerRef.current = null;
      }
      if (!pinnedToBottomRef.current) return;
      const el = scrollRef.current;
      if (!el) return;
      el.scrollTop = el.scrollHeight;
    };
    if (typeof window.requestAnimationFrame === 'function') {
      frameRef.current = window.requestAnimationFrame(run);
      return;
    }
    fallbackTimerRef.current = setTimeout(run, 16);
  }, []);

  const scrollToBottom = useCallback(() => {
    pinnedToBottomRef.current = true;
    requestScrollToBottom();
  }, [requestScrollToBottom]);

  useEffect(() => {
    if (pinnedToBottomRef.current) requestScrollToBottom();
  }, deps);

  useEffect(() => cancelPendingScroll, [cancelPendingScroll]);

  return {
    scrollRef,
    onScroll,
    scrollToBottom,
  };
};
