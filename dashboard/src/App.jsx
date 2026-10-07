import { useState } from 'react';
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

  return (
    <div className="app">
      <header className="app-header">
        <h1>일손배정 AI</h1>
        <span className="sub">양주시 공공형 계절근로 유휴 예보·배정 플랫폼</span>
      </header>

      <Tabs tabs={TABS} value={tab} onChange={setTab} />

      {tab === 'forecast' && <ForecastPage />}
      {tab === 'board' && <AssignmentBoardPage />}
      {tab === 'scenario' && <ScenarioPage />}
    </div>
  );
}
