import { useEffect, useState } from 'react';
import { getAssignments } from '../api/assignments.js';
import { groupByFarm, summarize, toIsoDate, upcomingDates } from '../utils/assignments.js';
import { shortDate, weekdayOf } from '../utils/forecast.js';
import BoardSummary from '../components/board/BoardSummary.jsx';
import FarmCard from '../components/board/FarmCard.jsx';

/**
 * 화면 2: 배정 보드 — 날짜 선택 → getAssignments(date) → 요약 → 농가별 카드 → 미배정/부족
 */
export default function AssignmentBoardPage() {
  const [date, setDate] = useState(() => toIsoDate());
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    getAssignments(date)
      .then((data) => alive && setResult(data))
      .catch((e) => alive && setError(e))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [date]);

  const quick = upcomingDates(7);
  const farms = result ? groupByFarm(result) : [];

  return (
    <div className="stack">
      <section className="card date-bar" aria-label="배정 날짜 선택">
        <label className="date-field">
          <span>배정 날짜</span>
          <input type="date" value={date} onChange={(e) => e.target.value && setDate(e.target.value)} />
        </label>
        <div className="chips" role="group" aria-label="빠른 선택">
          {quick.map((d, i) => (
            <button key={d} type="button" className="chip-btn" aria-pressed={d === date} onClick={() => setDate(d)}>
              {i === 0 ? '오늘' : `${shortDate(d)} (${weekdayOf(d)})`}
            </button>
          ))}
        </div>
      </section>

      {error && (
        <div className="card state error">배정 결과를 불러오지 못했습니다: {String(error.message ?? error)}</div>
      )}
      {!error && !result && <div className="card state">배정 결과 불러오는 중…</div>}

      {result && !error && (
        <div className={loading ? 'stack is-loading' : 'stack'} aria-busy={loading}>
          <section className="card hero">
            <h2>배정 요약</h2>
            <BoardSummary date={result.date} summary={summarize(result)} />
          </section>

          <section className="card">
            <h2>농가별 배정</h2>
            {farms.length === 0 ? (
              <p className="empty">이 날짜에 등록된 농가 요청이 없습니다. 다른 날짜를 선택하세요.</p>
            ) : (
              <div className="farm-grid">
                {farms.map((farm) => (
                  <FarmCard key={farm.farm_id} farm={farm} />
                ))}
              </div>
            )}
          </section>

          <section className="card">
            <h2>미배정 근로자 · 인력 부족</h2>
            <div className="leftovers">
              <div>
                <div className="leftovers-label">
                  미배정 근로자 <b className="num-warn">{result.unassigned_workers.length}명</b>
                </div>
                {result.unassigned_workers.length === 0 ? (
                  <p className="empty">전원 배정되었습니다.</p>
                ) : (
                  <ul className="id-chips">
                    {result.unassigned_workers.map((id) => (
                      <li key={id} className="chip chip--idle">
                        {id}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <div className="leftovers-label">
                  인력 부족 요청 <b className="num-warn">{result.unmet_requests.length}건</b>
                </div>
                {result.unmet_requests.length === 0 ? (
                  <p className="empty">모든 요청을 충족했습니다.</p>
                ) : (
                  <ul className="id-chips">
                    {result.unmet_requests.map((u, i) => (
                      <li key={`${u.farm_id}-${i}`} className="chip chip--warn">
                        {u.farm_id} · {u.shortage}명 부족
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
