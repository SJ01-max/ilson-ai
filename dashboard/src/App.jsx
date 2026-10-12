import { useEffect, useState } from 'react';
import Tabs from './components/Tabs.jsx';
import ForecastPage from './pages/ForecastPage.jsx';
import AssignmentBoardPage from './pages/AssignmentBoardPage.jsx';
import ScenarioPage from './pages/ScenarioPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import ChatWidget from './components/chat/ChatWidget.jsx';
import { logout } from './api/auth.js';
import { getDisplayName, getToken, UNAUTHORIZED_EVENT } from './api/client.js';

const TABS = [
  { id: 'forecast', label: '유휴 예보' },
  { id: 'board', label: '배정 보드' },
  { id: 'scenario', label: '시나리오 비교' },
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
            <h1>일손배정 AI</h1>
            <span className="sub">양주시 공공형 계절근로 유휴 예보·배정 플랫폼</span>
          </div>
          <div className="header-side">
            <span className="header-meta">
              {today} · 데이터 기준: 기상청 단기예보
            </span>
            <div className="mcp">
              <button
                type="button"
                className="icon-btn"
                aria-expanded={mcpOpen}
                aria-label="MCP 연동 안내"
                onClick={() => setMcpOpen((v) => !v)}
              >
                i
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

        {tab === 'forecast' && <ForecastPage />}
        {tab === 'board' && <AssignmentBoardPage />}
        {tab === 'scenario' && <ScenarioPage />}
      </div>

      {/* 탭 콘텐츠 바깥(.app 바깥) 최상위에 배치 — position:fixed 가 어떤 조상 스타일에도 영향받지 않게 */}
      <ChatWidget />
    </>
  );
}
