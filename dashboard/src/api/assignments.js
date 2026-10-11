/**
 * 배정 API (성재 → 정환)
 * GET /assignments?date=YYYY-MM-DD (Bearer) — engine/assigner.py 의 CP-SAT 배정 결과.
 * 응답 형식: docs/interface.md §2
 */
import { apiFetch } from './client.js';

/**
 * @param {string} date YYYY-MM-DD
 * @returns {Promise<{
 *   date: string,
 *   assignments: Array<{ worker_id: string, worker_name: string, farm_id: string, farm_name: string, task: string, score: number, reason: string }>,
 *   unassigned_workers: string[],
 *   unmet_requests: Array<{ farm_id: string, shortage: number }>
 * }>}
 */
export function getAssignments(date) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date ?? '')) {
    return Promise.reject(new Error('날짜는 YYYY-MM-DD 형식이어야 합니다.'));
  }
  return apiFetch(`/assignments?date=${encodeURIComponent(date)}`);
}
