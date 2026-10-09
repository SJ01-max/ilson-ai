import { useEffect, useState } from 'react';
import { getForecast } from '../api/forecast.js';
import { buildHeadline, toRows } from '../utils/forecast.js';
import Headline from '../components/forecast/Headline.jsx';
import SummaryCards from '../components/forecast/SummaryCards.jsx';
import DemandSupplyChart from '../components/forecast/DemandSupplyChart.jsx';
import ForecastTable from '../components/forecast/ForecastTable.jsx';

export default function ForecastPage() {
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    getForecast()
      .then((data) => alive && setForecast(data))
      .catch((e) => alive && setError(e));
    return () => {
      alive = false;
    };
  }, []);

  if (error) return <div className="card state error">예보를 불러오지 못했습니다: {String(error.message ?? error)}</div>;
  if (!forecast) return <div className="card state">예보 불러오는 중…</div>;

  const headline = buildHeadline(forecast);
  const rows = toRows(forecast);

  return (
    <div className="stack">
      <section className="card hero">
        <h2>주간 요약</h2>
        <SummaryCards forecast={forecast} headline={headline} />
        <Headline headline={headline} forecast={forecast} />
      </section>
      <section className="card">
        <h2>일별 추이</h2>
        <DemandSupplyChart rows={rows} />
      </section>
      <section className="card">
        <h2>상세 내역</h2>
        <ForecastTable rows={rows} total={forecast.week_total} />
      </section>
    </div>
  );
}
