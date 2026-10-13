import { useEffect, useState } from 'react';
import { getForecast } from '../api/forecast.js';
import { buildHeadline, formatManWon, isRainy, shortDate, toRows } from '../utils/forecast.js';
import { MODE_CHANGE_EVENT } from '../api/client.js';
import SummaryCards from '../components/forecast/SummaryCards.jsx';
import DemandSupplyChart from '../components/forecast/DemandSupplyChart.jsx';
import ForecastTable from '../components/forecast/ForecastTable.jsx';

export default function ForecastPage() {
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [view, setView] = useState('table');
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let alive = true;
    setForecast(null);
    getForecast()
      .then((data) => alive && setForecast(data))
      .catch((e) => alive && setError(e));
    return () => { alive = false; };
  }, [reloadKey]);

  useEffect(() => {
    const handler = () => setReloadKey((k) => k + 1);
    window.addEventListener(MODE_CHANGE_EVENT, handler);
    return () => window.removeEventListener(MODE_CHANGE_EVENT, handler);
  }, []);

  if (error) return <div className="card state error">예보를 불러오지 못했습니다: {String(error.message ?? error)}</div>;
  if (!forecast) return <div className="card state">예보 불러오는 중…</div>;

  const headline = buildHeadline(forecast);
  const rows = toRows(forecast);
  const selected = rows.find((row) => row.date === selectedDate) ?? rows[0];

  return (
    <div className="stack forecast-page">
      <section className="card hero">
        <div className="section-heading"><h2>주간 요약</h2><span>{shortDate(forecast.week_start)} — {rows.length ? shortDate(rows.at(-1).date) : shortDate(forecast.week_start)}</span></div>
        <SummaryCards forecast={forecast} headline={headline} />
      </section>
      <div className="forecast-workspace">
        <section className="card forecast-main">
          <div className="section-heading">
            <h2>날짜별 현황</h2>
            <div className="view-switch" role="group" aria-label="예보 보기 방식">
              <button type="button" aria-pressed={view === 'table'} onClick={() => setView('table')}>표</button>
              <button type="button" aria-pressed={view === 'chart'} onClick={() => setView('chart')}>그래프</button>
            </div>
          </div>
          {view === 'table' ? <ForecastTable rows={rows} total={forecast.week_total} selectedDate={selected?.date} onSelect={setSelectedDate} /> : <>
            <DemandSupplyChart rows={rows} />
            <div className="chips chart-date-picker" role="group" aria-label="상세 날짜 선택">
              {rows.map((row) => <button className="chip-btn" type="button" key={row.date} aria-pressed={row.date === selected?.date} onClick={() => setSelectedDate(row.date)}>{shortDate(row.date)} ({row.weekday})</button>)}
            </div>
          </>}
          <p className="table-note">일별 인원은 명, 주간 합계는 인일입니다. 날짜를 선택하면 상세 내용을 확인할 수 있습니다.</p>
        </section>
        {selected && <aside className="forecast-detail" aria-label="선택한 날짜 상세" aria-live="polite">
          <p className="section-kicker">선택한 날짜</p>
          <h2>{shortDate(selected.date)} <span>{selected.weekday}요일</span></h2>
          <p className="detail-finding">{selected.idle > 0 ? <>일손 <strong>{selected.idle}명</strong>이 남습니다.</> : '예상 유휴 인원이 없습니다.'}</p>
          <p className="detail-description">{isRainy(selected.weather) ? '강수 예보가 있는 날입니다. 작업 가능 여부를 확인하세요.' : '강수 예보가 없습니다. 예상 수요와 공급을 확인하세요.'}</p>
          <dl className="detail-list"><div><dt>날씨</dt><dd>{selected.weather}</dd></div><div><dt>공급 인원</dt><dd>{selected.supply}명</dd></div><div><dt>예상 수요</dt><dd>{selected.demand}명</dd></div><div><dt>유휴 인건비 환산액</dt><dd>{formatManWon(selected.loss_krw)}</dd></div></dl>
          <details className="detail-disclosure"><summary>산정 근거</summary><p>공급 {selected.supply}명과 예상 수요 {selected.demand}명의 차이를 유휴 인원으로 계산합니다. 유휴 인건비 환산액은 유휴 인원 × 일당 가정 10만 원입니다.</p></details>
          <details className="detail-disclosure"><summary>예보를 읽는 방법</summary><p>수요는 기상과 작목 통계를 바탕으로 한 추정치입니다. 실제 접수된 농가 요청과 구분해서 검토하세요.</p></details>
        </aside>}
      </div>
      <p className="forecast-context">{headline.text}</p>
    </div>
  );
}
