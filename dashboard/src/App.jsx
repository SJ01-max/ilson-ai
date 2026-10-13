import { useEffect, useState } from 'react';
import Tabs from './components/Tabs.jsx';
import ForecastPage from './pages/ForecastPage.jsx';
import AssignmentBoardPage from './pages/AssignmentBoardPage.jsx';
import ScenarioPage from './pages/ScenarioPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import ChatWidget from './components/chat/ChatWidget.jsx';
import ForecastBasis from './components/forecast/ForecastBasis.jsx';
import ModeToggle from './components/ModeToggle.jsx';
import { logout } from './api/auth.js';
import { getDisplayName, getToken, UNAUTHORIZED_EVENT } from './api/client.js';

const TABS = [
  { id: 'forecast', label: '유휴 예보', title: '이번 주 인력 현황', kicker: '주간 운영' },
  { id: 'board', label: '배정 보드', title: '농가별 배정 현황', kicker: '일별 배정' },
  { id: 'scenario', label: '시나리오 비교', title: '인력 투입 계획 비교', kicker: '운영 계획' },
];

export default function App() {
  const [tab, setTab] = useState('forecast');
  const [dark, setDark] = useState(false);
  const [mcpOpen, setMcpOpen] = useState(false);
  const [session, setSession] = useState(() =>
    getToken() ? { token: getToken(), display_name: getDisplayName() } : null,
  );

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  }, [dark]);

  // 서버 재시작 등으로 토큰이 무효가 되면(401) 로그인 화면으로
  useEffect(() => {
    const onUnauthorized = () => setSession(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } finally {
      setSession(null);
      setTab('forecast');
    }
  }

  if (!session) return <LoginPage onLogin={setSession} />;

  const today = new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  });

  return (
    <>
      <div className="app">
        <header className="app-header">
          <div className="brand">
            <h1>일손배정<span className="brand-ai">AI</span></h1>
            <span className="sub">양주시 공공형<br />계절근로 운영</span>
          </div>
          <div className="header-side">
            <span className="header-meta">
              {today}
            </span>
            <ForecastBasis />
            <ModeToggle />
            <div className="mcp">
              <button
                type="button"
                className="icon-btn"
                aria-expanded={mcpOpen}
                aria-label="MCP 연동 안내"
                onClick={() => setMcpOpen((v) => !v)}
              >
                연동 안내
              </button>
              {mcpOpen && (
                <div className="mcp-tip" role="status">
                  이 시스템은 Claude와 MCP로 연결됩니다. Claude에서
                  &ldquo;다음 주 유휴 어때?&rdquo;라고 물어보세요.
                </div>
              )}
            </div>
            <button
              type="button"
              className="text-btn"
              aria-pressed={dark}
              onClick={() => setDark((v) => !v)}
            >
              {dark ? '라이트' : '다크'}
            </button>
            <span className="user-chip" title="로그인 계정">
              {session.display_name || '담당자'}
            </span>
            <button type="button" className="text-btn" onClick={handleLogout}>
              로그아웃
            </button>
          </div>
        </header>

        <Tabs tabs={TABS} value={tab} onChange={setTab} />
        <section className="page-heading"><div><p className="section-kicker">{TABS.find((item) => item.id === tab).kicker}</p><h2>{TABS.find((item) => item.id === tab).title}</h2></div><p className="page-heading-note">백석농협 · 공공형 계절근로</p></section>

        <ChatWidget />

        {tab === 'forecast' && <ForecastPage />}
        {tab === 'board' && <AssignmentBoardPage />}
        {tab === 'scenario' && <ScenarioPage />}
        <footer className="app-footer"><span>일손배정 AI</span><span>양주시 공공형 계절근로 운영</span></footer>
      </div>


    </>
  );
}
