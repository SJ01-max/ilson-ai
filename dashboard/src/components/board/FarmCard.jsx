/**
 * 농가별 배정 카드 — 이름·점수·사유 문장 노출. 부족 인원은 빨강 칩.
 */
export default function FarmCard({ farm }) {
  const { farm_id, farm_name, tasks, workers, shortage } = farm;
  return (
    <article className="farm-card" aria-labelledby={`farm-${farm_id}`}>
      <header className="farm-head">
        <div>
          <h3 id={`farm-${farm_id}`}>{farm_name}</h3>
          <div className="farm-meta">
            {farm_id}
            {tasks.length > 0 && ` · ${tasks.join('·')}`}
          </div>
        </div>
        <div className="farm-count">
          <span className="count">{workers.length}명</span>
          {shortage > 0 && <span className="chip chip--warn">{shortage}명 부족</span>}
        </div>
      </header>
      {workers.length === 0 ? (
        <p className="farm-empty">배정된 근로자가 없습니다.</p>
      ) : (
        <ul className="worker-list">
          {workers.map((w) => (
            <li key={w.worker_id} className="worker">
              <div className="worker-main">
                <span className="worker-name">{w.worker_name}</span>
                <span className="worker-id">{w.worker_id}</span>
                <span
                  className="score"
                  aria-label={`배정 적합도 가중점수 ${w.score}점`}
                  title="배정 적합도 가중점수 (작목·경력·한국어·재입국·운전·읍면)"
                >
                  {w.score}
                  <small>점</small>
                </span>
              </div>
              <p className="worker-reason">{w.reason}</p>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
