import { shortDate, weekdayOf } from '../../utils/forecast.js';

/**
 * 배정 요약 — 결론 먼저. 배정 인원은 중립, 미배정(유휴)·부족은 빨강(유휴 인건비 환산액 의미).
 */
export default function BoardSummary({ date, summary }) {
  const { assigned, unassigned, shortage, farms } = summary;
  const noWork = assigned === 0 && shortage === 0;
  return (
    <>
      <div className="summary summary--3">
        <section className="stat stat--neutral">
          <div className="label">추천 배정</div>
          <div className="value">
            {assigned}
            <small>명</small>
          </div>
          <div className="hint">농가 {farms}곳</div>
        </section>
        <section className={unassigned > 0 ? 'stat' : 'stat stat--neutral'}>
          <div className="label">미배정 근로자</div>
          <div className={unassigned > 0 ? 'value value--warn' : 'value'}>
            {unassigned}
            <small>명</small>
          </div>
          <div className="hint">이날 일감이 없는 인원 = 유휴</div>
        </section>
        <section className={shortage > 0 ? 'stat' : 'stat stat--neutral'}>
          <div className="label">인력 부족</div>
          <div className={shortage > 0 ? 'value value--warn' : 'value'}>
            {shortage}
            <small>명</small>
          </div>
          <div className="hint">농가 요청 대비 못 채운 인원</div>
        </section>
      </div>
      <div className="headline">
        <div className="eyebrow">
          배정 결과 · {shortDate(date)} ({weekdayOf(date)})
        </div>
        <p className="text">
          {noWork ? (
            <span>이 날짜에는 농가 요청이 없습니다. 전원 미배정(유휴)입니다.</span>
          ) : (
            <>
              <span>
                농가 {farms}곳에 {assigned}명 배정
              </span>
              {unassigned > 0 && (
                <>
                  <span className="arrow" aria-hidden="true">
                    →
                  </span>
                  <span className="part--loss">미배정 {unassigned}명</span>
                </>
              )}
              {shortage > 0 && (
                <>
                  <span className="arrow" aria-hidden="true">
                    →
                  </span>
                  <span className="part--loss">부족 {shortage}명</span>
                </>
              )}
            </>
          )}
        </p>
        <div className="meta">점수는 작목 경험·경력·한국어·재입국·운전·거주 읍면 가중치의 합계입니다.</div>
      </div>
    </>
  );
}
