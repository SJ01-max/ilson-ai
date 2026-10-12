/**
 * 시나리오 비교 API (성재 → 정환)
 * GET /scenario?workers=&start= (Bearer) — engine/scenario.py 의 compare 결과.
 * 응답 형식: docs/interface.md §5 (base·scenario·diff — unmet 포함).
 */
import { apiFetch } from './client.js';

/**
 * @param {number} workers 5~50
 * @param {string|null} [start] YYYY-MM-DD 또는 null (주 전체 적용)
 * @returns {Promise<{
 *   base:     { workers: number, start: string|null, idle: number, unmet: number, loss_krw: number, utilization: number },
 *   scenario: { workers: number, start: string|null, idle: number, unmet: number, loss_krw: number, utilization: number },
 *   diff:     { idle: number, unmet: number, loss_krw: number }
 * }>}
 */
export function getScenario(workers, start) {
  const params = new URLSearchParams({ workers: String(workers) });
  if (start) params.set('start', start);
  return apiFetch(`/scenario?${params.toString()}`);
}
