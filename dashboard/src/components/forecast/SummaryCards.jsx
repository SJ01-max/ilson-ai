import { formatManWon } from '../../utils/forecast.js';

export default function SummaryCards({ forecast, headline }) {
  const { idle, loss_krw } = forecast.week_total;
  const days = forecast.days.length;
  return (
    <div className="summary">
      <section className="stat">
        <div className="label">주간 유휴 인일 합계</div>
        <div className="value value--warn">
          {idle.toLocaleString('ko-KR')}
          <small>인일</small>
        </div>
        <div className="hint">
          {days}일 기준 · 강수일 유휴 {headline.idle}인일
        </div>
      </section>
      <section className="stat">
        <div className="label">주간 손실액 합계</div>
        <div className="value value--warn">{formatManWon(loss_krw)}</div>
        <div className="hint">강수일 손실 {formatManWon(headline.lossKrw)}</div>
      </section>
    </div>
  );
}
