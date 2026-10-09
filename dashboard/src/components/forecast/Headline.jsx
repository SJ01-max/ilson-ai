import { shortDate } from '../../utils/forecast.js';

/**
 * 상단 핵심 문구
 * 예) 다음 주 월·화 강수 → 유휴 18인일 → 손실 180만 원
 */
export default function Headline({ headline, forecast }) {
  const last = forecast.days.at(-1)?.date;
  return (
    <section className="headline">
      <div className="eyebrow">주간 유휴 예보 · {shortDate(forecast.week_start)}{last && ` ~ ${shortDate(last)}`}</div>
      <p className="text" aria-label={headline.text}>
        {headline.parts.map((p, i) => (
          <span key={p}>
            {i > 0 && <span className="arrow" aria-hidden="true">→ </span>}
            <span className={i >= 1 ? 'part--loss' : undefined}>{p}</span>
          </span>
        ))}
      </p>
      <div className="meta">
        {headline.rainDays.length
          ? `강수일 ${headline.rainDays.length}일 기준 · 손실액은 유휴 인일 × 일당 기준 추정치`
          : '이번 예보 기간에는 강수가 없습니다.'}
      </div>
    </section>
  );
}
