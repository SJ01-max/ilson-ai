/**
 * 시나리오 비교 — 화면 확인용 임시 추정 (순수 함수)
 *
 * ⚠️ 확정 계산은 engine/mcp_server.py 의 compare_scenario(성재 담당, 새영 공식 대기)가 맡는다.
 *    엔진이 올라오면 이 함수 호출부(pages/ScenarioPage.jsx)를 API 호출로 바꾼다.
 *
 * 가정(임시): 입국 인원 workers 가 start 날짜부터 투입된다 → 그날 이후 supply = workers,
 *            그 전에는 supply = 0. idle = max(supply − demand, 0), shortage = max(demand − supply, 0),
 *            loss = idle × 일당(100,000원). 수요(demand)·날씨는 예보 그대로 사용.
 */

export const DAILY_WAGE_KRW = 100_000;

/**
 * @param {object} forecast docs/interface.md §3
 * @param {{ workers: number, start: string }} scenario
 */
export function estimateScenario(forecast, { workers, start }) {
  const days = (forecast?.days ?? []).map((d) => {
    const supply = d.date >= start ? workers : 0;
    const idle = Math.max(supply - d.demand, 0);
    const shortage = Math.max(d.demand - supply, 0);
    return {
      date: d.date,
      weather: d.weather,
      demand: d.demand,
      base_supply: d.supply,
      base_idle: d.idle,
      base_loss_krw: d.loss_krw,
      supply,
      idle,
      shortage,
      loss_krw: idle * DAILY_WAGE_KRW,
    };
  });
  const sum = (key) => days.reduce((s, d) => s + (d[key] ?? 0), 0);
  return {
    days,
    base_total: { idle: forecast?.week_total?.idle ?? sum('base_idle'), loss_krw: forecast?.week_total?.loss_krw ?? sum('base_loss_krw') },
    total: { idle: sum('idle'), loss_krw: sum('loss_krw'), shortage: sum('shortage') },
  };
}
