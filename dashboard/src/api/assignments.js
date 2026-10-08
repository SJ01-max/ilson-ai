/**
 * 배정 API (성재 → 정환)
 * 응답 형식: docs/interface.md §2
 *
 * 10/12 통합 시 이 파일의 함수 본문만 fetch()로 교체한다.
 * 화면 컴포넌트는 이 함수만 호출하고, mock JSON을 직접 import하지 않는다.
 *
 * 교체 예시:
 *   const res = await fetch(`${import.meta.env.VITE_API_BASE}/assignments?date=${date}`);
 *   if (!res.ok) throw new Error(`assignments ${res.status}`);
 *   return res.json();
 */
import mock from '../mock/assignments.json';

/**
 * @param {string} date YYYY-MM-DD
 * @returns {Promise<{
 *   date: string,
 *   assignments: Array<{ worker_id: string, worker_name: string, farm_id: string, farm_name: string, task: string, score: number, reason: string }>,
 *   unassigned_workers: string[],
 *   unmet_requests: Array<{ farm_id: string, shortage: number }>
 * }>}
 */
export async function getAssignments(date) {
  await new Promise((r) => setTimeout(r, 150));
  // Mock은 단일 날짜만 담고 있으므로 요청 날짜를 그대로 반영해서 돌려준다.
  return { ...structuredClone(mock), date: date ?? mock.date };
}
