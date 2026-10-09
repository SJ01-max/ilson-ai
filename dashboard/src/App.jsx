import { useEffect, useState } from 'react';
import Tabs from './components/Tabs.jsx';
import ForecastPage from './pages/ForecastPage.jsx';
import AssignmentBoardPage from './pages/AssignmentBoardPage.jsx';
import ScenarioPage from './pages/ScenarioPage.jsx';

const TABS = [
  { id: 'forecast', label: '유휴 예보' },
  { id: 'board', label: '배정 보드', badge: '준비 중' },
  { id: 'scenario', label: '시나리오 비교', badge: '준비 중' },
];

export default function App() {
  const [tab, setTab] = useState('forecast');
  const [dark, setDark] = useState(false);
  const [mcpOpen, setMcpOpen] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  }, [dark]);

  const today = new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  });

  return (
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
        </div>
      </header>

      <Tabs tabs={TABS} value={tab} onChange={setTab} />

      {tab === 'forecast' && <ForecastPage />}
      {tab === 'board' && <AssignmentBoardPage />}
      {tab === 'scenario' && <ScenarioPage />}
    </div>
  );
}
