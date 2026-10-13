import { formatManWon } from '../../utils/forecast.js';

export default function SummaryCards({ forecast, headline }) {
  const { idle, loss_krw } = forecast.week_total;
  const days = forecast.days.length;
  const supply = forecast.days.reduce((sum, day) => sum + day.supply, 0);
  const used = forecast.days.reduce((sum, day) => sum + Math.min(day.supply, day.demand), 0);
  const utilization = supply ? Math.round(used / supply * 100) : 0;
  return (
    <div className="summary summary--3">
      <section className="stat">
        <div className="label">유휴 인건비 환산액(예상)</div>
        <div className="value">{formatManWon(loss_krw)}</div>
        <div className="hint">일당 10만 원 기준 · 강수일 {formatManWon(headline.lossKrw)}</div>
      </section>
      <section className="stat">
        <div className="label">예상 유휴</div>
        <div className="value">{idle.toLocaleString('ko-KR')}<small>인일</small></div>
        <div className="hint">{days}일 합계 · 강수일 유휴 {headline.idle}인일</div>
      </section>
      <section className="stat stat--neutral">
        <div className="label">예상 가동률</div>
        <div className="value">{utilization}<small>%</small></div>
        <div className="hint">예상 투입 {used} / 공급 {supply}인일</div>
        <div className="utilization-track" aria-hidden="true"><span style={{ width: `${utilization}%` }} /></div>
      </section>
    </div>
  );
}
