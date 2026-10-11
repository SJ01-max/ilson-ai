/**
 * 배정 결과(docs/interface.md §2) 가공 유틸 — 순수 함수, UI 의존 없음
 */

/**
 * 농가별로 묶는다. 배정이 없고 부족만 있는 농가도 카드로 나오도록 unmet_requests를 합친다.
 * @returns {Array<{ farm_id, farm_name, tasks: string[], workers: Array, shortage: number }>}
 */
export function groupByFarm(result) {
  const map = new Map();
  for (const a of result?.assignments ?? []) {
    if (!map.has(a.farm_id)) {
      map.set(a.farm_id, { farm_id: a.farm_id, farm_name: a.farm_name, tasks: [], workers: [], shortage: 0 });
    }
    const g = map.get(a.farm_id);
    if (!g.tasks.includes(a.task)) g.tasks.push(a.task);
    g.workers.push(a);
  }
  for (const u of result?.unmet_requests ?? []) {
    if (!map.has(u.farm_id)) {
      map.set(u.farm_id, { farm_id: u.farm_id, farm_name: u.farm_id, tasks: [], workers: [], shortage: 0 });
    }
    map.get(u.farm_id).shortage += u.shortage ?? 0;
  }
  const groups = [...map.values()];
  for (const g of groups) g.workers.sort((a, b) => b.score - a.score);
  return groups.sort((a, b) => a.farm_id.localeCompare(b.farm_id));
}

/** 요약 수치 */
export function summarize(result) {
  const assigned = result?.assignments?.length ?? 0;
  const unassigned = result?.unassigned_workers?.length ?? 0;
  const shortage = (result?.unmet_requests ?? []).reduce((s, u) => s + (u.shortage ?? 0), 0);
  const farms = new Set((result?.assignments ?? []).map((a) => a.farm_id)).size;
  return { assigned, unassigned, shortage, farms, total: assigned + unassigned };
}

/** 'YYYY-MM-DD' 로컬 날짜 문자열 (타임존 밀림 방지) */
export function toIsoDate(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** 오늘부터 n일치 'YYYY-MM-DD' 배열 (날짜 빠른 선택용) */
export function upcomingDates(n = 7, from = new Date()) {
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(from.getFullYear(), from.getMonth(), from.getDate() + i);
    return toIsoDate(d);
  });
}
