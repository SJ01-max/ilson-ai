import { useEffect, useRef, useState } from 'react';
import { postChat } from '../../api/chat.js';
import { ApiError } from '../../api/client.js';

const SUGGESTIONS = ['이번 주 유휴 이유는?', '내일 배정 알려줘', '15명으로 줄이면?'];

// 탭 콘텐츠와 별도로 유지하여 화면을 바꿔도 대화가 이어진다.
export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (open && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [open, messages, busy, error]);

  async function send(question) {
    const text = question.trim();
    if (!text || busy) return;
    const next = [...messages, { role: 'user', content: text }];
    setMessages(next);
    setInput('');
    setOpen(true);
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
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="chat-inline" aria-labelledby="chat-inline-title">
      <header className="chat-head">
        <h2 id="chat-inline-title">일손 도우미</h2>
        {messages.length > 0 && <button type="button" className="chat-toggle" aria-expanded={open} aria-controls="chat-conversation" onClick={() => setOpen((value) => !value)}>{open ? '대화 접기' : '이전 대화 보기'}</button>}
      </header>
      <form className="chat-form" onSubmit={(event) => { event.preventDefault(); send(input); }}>
        <input type="text" value={input} onChange={(event) => setInput(event.target.value)} placeholder="예보나 배정에 대해 물어보세요." aria-label="일손 도우미 질문" autoComplete="off" disabled={busy} />
        <button type="submit" disabled={busy || !input.trim()}>{busy ? '답변 중…' : '질문 보내기'}</button>
      </form>
      <div className="chat-suggestions" role="group" aria-label="추천 질문">
        {SUGGESTIONS.map((question) => <button type="button" key={question} disabled={busy} onClick={() => send(question)}>{question}</button>)}
      </div>
      <div id="chat-conversation" className="chat-conversation" hidden={!open}>
        <div className="chat-log" ref={scrollRef} role="log" aria-label="일손 도우미 대화" aria-live="polite" aria-relevant="additions text">
          {messages.map((message, index) => <div key={index} className={`chat-turn chat-turn--${message.role}`}><span className="chat-speaker">{message.role === 'user' ? '담당자' : '일손 도우미'}</span><p className="chat-message">{message.content}</p></div>)}
          {busy && <div className="chat-turn chat-turn--assistant"><span className="chat-speaker">일손 도우미</span><p className="chat-message chat-loading" role="status">예보와 배정 데이터를 확인하고 있습니다…</p></div>}
          {error && <p className="chat-error" role="alert">{error}</p>}
        </div>
      </div>
    </section>
  );
}
