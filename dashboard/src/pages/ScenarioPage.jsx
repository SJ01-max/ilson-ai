import { useEffect, useMemo, useState } from 'react';
import { getForecast } from '../api/forecast.js';
import { estimateScenario } from '../utils/scenario.js';
import { formatManWon, isRainy, shortDate, toMan, weekdayOf } from '../utils/forecast.js';
import ScenarioChart from '../components/scenario/ScenarioChart.jsx';

const WORKERS_MIN = 5;
const WORKERS_MAX = 40;

/**
 * 화면 3: 시나리오 비교 — 슬라이더(입국 인원·투입 시기) + 결과 영역.
 * 결과 수치는 현재 utils/scenario.js 의 임시 추정이다. 성재의 compare_scenario 엔진이
 * 올라오면 estimateScenario() 호출 자리를 API 호출로 바꾼다 (화면 레이아웃은 그대로).
 */
export default function ScenarioPage() {
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState(null);
  const [workers, setWorkers] = useState(20);
  const [startIdx, setStartIdx] = useState(0);

  useEffect(() => {
    let alive = true;
    getForecast()
      .then((data) => alive && setForecast(data))
      .catch((e) => alive && setError(e));
    return () => {
      alive = false;
    };
  }, []);

  const days = forecast?.days ?? [];
  const start = days[Math.min(startIdx, Math.max(days.length - 1, 0))]?.date;
  const baseSupply = days[0]?.supply ?? 20;

  const est = useMemo(() => (forecast && start ? estimateScenario(forecast, { workers, start }) : null), [forecast, workers, start]);

  if (error) return <div className="card state error">예보를 불러오지 못했습니다: {String(error.message ?? error)}</div>;
  if (!forecast || !est) return <div className="card state">예보 불러오는 중…</div>;

  const rows = est.days.map((d) => ({
    ...d,
    weekday: weekdayOf(d.date),
    label: `${weekdayOf(d.date)} ${shortDate(d.date)}`,
    rainy: isRainy(d.weather),
  }));
  const dIdle = est.total.idle - est.base_total.idle;
  const dLoss = est.total.loss_krw - est.base_total.loss_krw;
  const sign = (n) => (n > 0 ? `+${n}` : `${n}`);

  return (
    <div className="stack">
      <section className="card" aria-label="시나리오 조건">
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
              <span>현재 {baseSupply}명</span>
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
        <p className="note" role="note">
          계산 엔진(compare_scenario) 연결 대기 중 — 아래 수치는 화면 확인용 임시 추정(공급 − 수요)입니다.
        </p>
      </section>

      <section className="card hero">
        <h2>결과 요약 · 현재 vs 시나리오</h2>
        <div className="summary summary--3">
          <section className="stat">
            <div className="label">주간 유휴 인일</div>
            <div className="value value--warn">
              {est.total.idle}
              <small>인일</small>
            </div>
            <div className="hint">
              현재 {est.base_total.idle}인일 · {sign(dIdle)}
            </div>
          </section>
          <section className="stat">
            <div className="label">주간 손실액</div>
            <div className="value value--warn">{formatManWon(est.total.loss_krw)}</div>
            <div className="hint">
              현재 {formatManWon(est.base_total.loss_krw)} · {dLoss > 0 ? '+' : dLoss < 0 ? '−' : ''}
              {formatManWon(Math.abs(dLoss))}
            </div>
          </section>
          <section className={est.total.shortage > 0 ? 'stat' : 'stat stat--neutral'}>
            <div className="label">인력 부족 (수요 &gt; 공급)</div>
            <div className={est.total.shortage > 0 ? 'value value--warn' : 'value'}>
              {est.total.shortage}
              <small>인일</small>
            </div>
            <div className="hint">투입 전·소수 인원일 때 발생</div>
          </section>
        </div>
        <div className="headline">
          <div className="eyebrow">시나리오 문장</div>
          <p className="text">
            <span>
              {workers}명이 {shortDate(start)}({weekdayOf(start)})부터 투입되면
            </span>
            <span className="arrow" aria-hidden="true">
              →
            </span>
            <span className="part--loss">유휴 {est.total.idle}인일</span>
            <span className="arrow" aria-hidden="true">
              →
            </span>
            <span className="part--loss">손실 {formatManWon(est.total.loss_krw)}</span>
          </p>
          <div className="meta">
            현재 기준(공급 {baseSupply}명 고정) 대비 유휴 {sign(dIdle)}인일
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
                <th>손실액(만 원)</th>
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
                  <td className={r.shortage > 0 ? 'num-warn' : undefined}>{r.shortage}</td>
                  <td className={r.loss_krw > 0 ? 'num-warn' : undefined}>{toMan(r.loss_krw)}</td>
                </tr>
              ))}
              <tr className="total">
                <td>주간 합계</td>
                <td className="left" />
                <td>{rows.reduce((s, r) => s + r.demand, 0)}</td>
                <td />
                <td className="num-warn">
                  {est.base_total.idle} → {est.total.idle}
                </td>
                <td className="num-warn">{est.total.shortage}</td>
                <td className="num-warn">{toMan(est.total.loss_krw)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
