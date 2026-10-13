import { useEffect, useMemo, useRef, useState } from 'react';
import { getForecast } from '../api/forecast.js';
import { getScenario } from '../api/scenario.js';
import { formatManWon, isRainy, shortDate, toMan, weekdayOf } from '../utils/forecast.js';
import ScenarioChart from '../components/scenario/ScenarioChart.jsx';

const WORKERS_MIN = 5;
const WORKERS_MAX = 50;
const BASE_WORKERS = 20;
const WAGE_KRW = 100_000;
const DEBOUNCE_MS = 300;

/**
 * 화면 3: 시나리오 비교 — 슬라이더(입국 인원·투입 시기) → GET /scenario → 요약·차트·표.
 * 주간 집계(idle/unmet/loss_krw/utilization)는 엔진 응답을 그대로 쓰고,
 * 일별 차트는 엔진과 동일한 공급 규칙(start 기준)으로 재구성한다 — 이중 계산이 아니라 동일 규칙 전개.
 */
export default function ScenarioPage() {
  const [forecast, setForecast] = useState(null);
  const [forecastError, setForecastError] = useState(null);
  const [workers, setWorkers] = useState(BASE_WORKERS);
  const [startIdx, setStartIdx] = useState(0);
  const [result, setResult] = useState(null);
  const [scenarioError, setScenarioError] = useState(null);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    let alive = true;
    getForecast()
      .then((data) => alive && setForecast(data))
      .catch((e) => alive && setForecastError(e));
    return () => {
      alive = false;
    };
  }, []);

  const days = forecast?.days ?? [];
  const start = days[Math.min(startIdx, Math.max(days.length - 1, 0))]?.date;

  useEffect(() => {
    if (!forecast || !start) return undefined;
    if (timerRef.current) clearTimeout(timerRef.current);
    setLoading(true);
    timerRef.current = setTimeout(() => {
      let alive = true;
      getScenario(workers, start)
        .then((data) => {
          if (!alive) return;
          setResult(data);
          setScenarioError(null);
        })
        .catch((e) => alive && setScenarioError(e))
        .finally(() => alive && setLoading(false));
      return () => {
        alive = false;
      };
    }, DEBOUNCE_MS);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [forecast, workers, start]);

  const rows = useMemo(() => {
    if (!forecast || !start) return [];
    return days.map((d) => {
      const supply = d.date >= start ? workers : BASE_WORKERS;
      const idle = Math.max(supply - d.demand, 0);
      const shortage = Math.max(d.demand - supply, 0);
      return {
        date: d.date,
        weather: d.weather,
        weekday: weekdayOf(d.date),
        label: `${weekdayOf(d.date)} ${shortDate(d.date)}`,
        rainy: isRainy(d.weather),
        demand: d.demand,
        base_supply: BASE_WORKERS,
        base_idle: d.idle,
        supply,
        idle,
        shortage,
        loss_krw: idle * WAGE_KRW,
      };
    });
  }, [forecast, workers, start, days]);

  if (forecastError) {
    return (
      <div className="card state error">예보를 불러오지 못했습니다: {String(forecastError.message ?? forecastError)}</div>
    );
  }
  if (!forecast) return <div className="card state">예보 불러오는 중…</div>;

  if (scenarioError && !result) {
    return (
      <div className="card state error">시나리오를 불러오지 못했습니다: {String(scenarioError.message ?? scenarioError)}</div>
    );
  }
  if (!result) return <div className="card state">시나리오 계산 중…</div>;

  const { base, scenario, diff } = result;
  const sign = (n) => (n > 0 ? `+${n}` : `${n}`);

  return (
    <div className="stack scenario-layout">
      <section className="card scenario-controls" aria-label="시나리오 조건">
        <h2>조건 설정</h2>
        <div className="sliders">
          <label className="slider">
            <div className="slider-head">
              <span>입국 인원</span>
              <b>{workers}명</b>
            </div>
            <input
              type="range"
              min={WORKERS_MIN}
              max={WORKERS_MAX}
              step={1}
              value={workers}
              onChange={(e) => setWorkers(Number(e.target.value))}
              aria-valuetext={`${workers}명`}
            />
            <div className="slider-scale">
              <span>{WORKERS_MIN}명</span>
              <span>현재 {BASE_WORKERS}명</span>
              <span>{WORKERS_MAX}명</span>
            </div>
          </label>
          <label className="slider">
            <div className="slider-head">
              <span>투입 시작일</span>
              <b>
                {shortDate(start)} ({weekdayOf(start)})
              </b>
            </div>
            <input
              type="range"
              min={0}
              max={Math.max(days.length - 1, 0)}
              step={1}
              value={Math.min(startIdx, days.length - 1)}
              onChange={(e) => setStartIdx(Number(e.target.value))}
              aria-valuetext={`${start} 투입 시작`}
            />
            <div className="slider-scale">
              <span>{shortDate(days[0].date)}</span>
              <span>예보 기간 내</span>
              <span>{shortDate(days.at(-1).date)}</span>
            </div>
          </label>
        </div>
      </section>

      <section className={loading ? 'card hero scenario-results is-loading' : 'card hero scenario-results'} aria-busy={loading}>
        <h2>결과 요약 · 현재 계획과 변경안</h2>
        <div className="summary summary--4">
          <section className="stat">
            <div className="label">주간 유휴 인일</div>
            <div className="value value--warn">
              {scenario.idle}
              <small>인일</small>
            </div>
            <div className="hint">
              현재 {base.idle}인일 · {sign(diff.idle)}
            </div>
          </section>
          <section className="stat">
            <div className="label">주간 유휴 인건비 환산액(예상)</div>
            <div className="value value--warn">{formatManWon(scenario.loss_krw)}</div>
            <div className="hint">
              현재 {formatManWon(base.loss_krw)} · {diff.loss_krw > 0 ? '+' : diff.loss_krw < 0 ? '−' : ''}
              {formatManWon(Math.abs(diff.loss_krw))}
            </div>
          </section>
          <section className={scenario.unmet > 0 ? 'stat stat--unmet' : 'stat stat--neutral'}>
            <div className="label">수요 미충족(인일)</div>
            <div className={scenario.unmet > 0 ? 'value value--unmet' : 'value'}>
              {scenario.unmet}
              <small>인일</small>
            </div>
            <div className="hint">
              현재 {base.unmet}인일 · {sign(diff.unmet)}
            </div>
          </section>
          <section className="stat stat--neutral">
            <div className="label">가동률</div>
            <div className="value">
              {Math.round(scenario.utilization * 100)}
              <small>%</small>
            </div>
            <div className="hint">
              현재 {Math.round(base.utilization * 100)}% · 수요 미충족도 함께 확인하세요
            </div>
          </section>
        </div>
        <div className="headline">
          <div className="eyebrow">변경안 요약</div>
          <p className="text">
            <span>
              {workers}명이 {shortDate(start)}({weekdayOf(start)})부터 투입되면
            </span>
            <span className="arrow" aria-hidden="true">
              →
            </span>
            <span className="part--loss">유휴 {scenario.idle}인일</span>
            <span className="arrow" aria-hidden="true">
              →
            </span>
            <span className="part--loss">환산액 {formatManWon(scenario.loss_krw)}</span>
            {scenario.unmet > 0 && (
              <>
                <span className="arrow" aria-hidden="true">
                  →
                </span>
                <span className="part--unmet">수요 미충족 {scenario.unmet}인일</span>
              </>
            )}
          </p>
          <div className="meta">
            현재 기준(공급 {BASE_WORKERS}명 고정) 대비 유휴 {sign(diff.idle)}인일 · 미충족 {sign(diff.unmet)}인일
          </div>
        </div>
      </section>

      <section className="card">
        <h2>일별 유휴 비교</h2>
        <ScenarioChart rows={rows} />
      </section>

      <section className="card">
        <h2>상세 내역</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>날짜</th>
                <th className="left">날씨</th>
                <th>수요(명)</th>
                <th>공급 현재→시나리오</th>
                <th>유휴 현재→시나리오</th>
                <th>부족(명)</th>
                <th>환산액(만 원)</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.date} className={r.rainy ? 'rainy' : undefined}>
                  <td>
                    {r.date} ({r.weekday})
                  </td>
                  <td className="left">
                    <span className={r.rainy ? 'weather-chip weather-chip--rain' : 'weather-chip'}>{r.weather}</span>
                  </td>
                  <td>{r.demand}</td>
                  <td>
                    {r.base_supply} → {r.supply}
                  </td>
                  <td className={r.idle > 0 ? 'num-warn' : undefined}>
                    {r.base_idle} → {r.idle}
                  </td>
                  <td className={r.shortage > 0 ? 'num-unmet' : undefined}>{r.shortage}</td>
                  <td className={r.loss_krw > 0 ? 'num-warn' : undefined}>{toMan(r.loss_krw)}</td>
                </tr>
              ))}
              <tr className="total">
                <td>주간 합계</td>
                <td className="left" />
                <td>{rows.reduce((s, r) => s + r.demand, 0)}</td>
                <td />
                <td className="num-warn">
                  {base.idle} → {scenario.idle}
                </td>
                <td className={scenario.unmet > 0 ? 'num-unmet' : undefined}>{scenario.unmet}</td>
                <td className="num-warn">{toMan(scenario.loss_krw)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
