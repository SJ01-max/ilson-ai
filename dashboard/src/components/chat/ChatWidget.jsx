import { useEffect, useRef, useState } from 'react';
import { postChat } from '../../api/chat.js';
import { ApiError } from '../../api/client.js';

/**
 * 우하단 플로팅 채팅 위젯 — /chat 호출. 대화는 메모리에만 보관, 새로고침 시 초기화.
 * 외부 라이브러리 없이 React 상태만 사용.
 */
export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [open, messages, busy]);

  useEffect(() => {
    if (open && inputRef.current) inputRef.current.focus();
  }, [open]);

  async function send(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    const next = [...messages, { role: 'user', content: text }];
    setMessages(next);
    setInput('');
    setBusy(true);
    setError(null);
    try {
      const data = await postChat(next);
      setMessages([...next, { role: 'assistant', content: data.reply || '(응답 없음)' }]);
    } catch (err) {
      const msg = err instanceof ApiError && err.status === 503
        ? 'AI 질의 기능이 설정되지 않았습니다'
        : `오류: ${err.message ?? String(err)}`;
      setError(msg);
      setMessages(next);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {!open && (
        <button
          type="button"
          className="chat-fab"
          aria-label="AI 질의 채팅 열기"
          onClick={() => setOpen(true)}
        >
          일손 도우미
        </button>
      )}
      {open && (
        <section className="chat-panel" role="dialog" aria-label="AI 질의 채팅">
          <header className="chat-head">
            <div className="chat-title">
              <b>일손 도우미</b>
              <span>· 예보와 배정에 대해 질문하세요</span>
            </div>
            <button type="button" className="chat-close" aria-label="닫기" onClick={() => setOpen(false)}>
              ✕
            </button>
          </header>
          <div className="chat-log" ref={scrollRef} aria-live="polite">
            {messages.length === 0 && !error && (
              <div className="chat-empty">
                예) "다음 주 유휴 어때?" / "10/14 배정 알려줘" / "입국 30명이면?"
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={m.role === 'user' ? 'bubble bubble--user' : 'bubble bubble--bot'}>
                {m.content}
              </div>
            ))}
            {busy && <div className="bubble bubble--bot bubble--loading">응답 생성 중…</div>}
            {error && <div className="chat-error" role="alert">{error}</div>}
          </div>
          <form className="chat-form" onSubmit={send}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="질문을 입력하세요"
              aria-label="질문 입력"
              disabled={busy}
            />
            <button type="submit" disabled={busy || !input.trim()}>
              전송
            </button>
          </form>
        </section>
      )}
    </>
  );
}
