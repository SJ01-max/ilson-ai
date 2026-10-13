import { useEffect, useState } from 'react';
import { getForecast } from '../../api/forecast.js';
import { shortDate } from '../../utils/forecast.js';
import { MODE_CHANGE_EVENT } from '../../api/client.js';

// data/idle_forecast.json 의 generated_at·source 를 읽어 상단 기준 라벨을 렌더.
// 메타 없으면 week_start 기반 폴백 — 기존 JSON에도 지장 없게.
function formatGeneratedAt(iso) {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if (!m) return null;
  return `${Number(m[2])}/${Number(m[3])} ${Number(m[4])}시`;
}

export default function ForecastBasis() {
  const [forecast, setForecast] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let alive = true;
    getForecast()
      .then((data) => alive && setForecast(data))
      .catch(() => {
        /* 실패해도 헤더는 조용히 비움 — 예보 자체 오류는 하위 페이지가 안내 */
      });
    return () => {
      alive = false;
    };
  }, [reloadKey]);

  useEffect(() => {
    const handler = () => setReloadKey((k) => k + 1);
    window.addEventListener(MODE_CHANGE_EVENT, handler);
    return () => window.removeEventListener(MODE_CHANGE_EVENT, handler);
  }, []);

  if (!forecast) return null;

  if (forecast.source === 'demo') {
    return <span className="forecast-basis forecast-basis--demo">시연 데이터</span>;
  }

  const label = forecast.generated_at
    ? `예보 생성: ${formatGeneratedAt(forecast.generated_at)} · 기상청 단기예보`
    : `예보 기준: ${shortDate(forecast.week_start)}`;
  return <span className="forecast-basis">{label}</span>;
}
