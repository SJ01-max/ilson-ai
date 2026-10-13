import { useEffect, useState } from 'react';
import { MODE_CHANGE_EVENT, getMode, setMode } from '../api/client.js';

// 시연 중 "강수 주간" 전환 — 멘토 피드백.
// 메모리 전용이라 새로고침 시 꺼짐(실데이터가 기본). 켜짐이 명확히 보이게 스타일링.
export default function ModeToggle() {
  const [demo, setDemo] = useState(() => getMode() === 'demo');

  useEffect(() => {
    const handler = (e) => setDemo(e.detail?.mode === 'demo');
    window.addEventListener(MODE_CHANGE_EVENT, handler);
    return () => window.removeEventListener(MODE_CHANGE_EVENT, handler);
  }, []);

  function toggle() {
    setMode(demo ? null : 'demo');
  }

  return (
    <button
      type="button"
      className={demo ? 'mode-toggle mode-toggle--on' : 'mode-toggle'}
      aria-pressed={demo}
      onClick={toggle}
      title="데모 모드: 강수 2일 포함 주간(54인일)으로 전환합니다"
    >
      <span className="mode-toggle-dot" aria-hidden="true" />
      시연: 강수 주간
    </button>
  );
}
