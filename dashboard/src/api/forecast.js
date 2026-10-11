/**
 * 유휴 예보 API (새영 → 정환)
 * GET /forecast (Bearer) — 서버는 data/idle_forecast.json을 그대로 돌려준다.
 * 응답 형식: docs/interface.md §3
 */
import { apiFetch } from './client.js';

/**
 * @returns {Promise<{
 *   week_start: string,
 *   days: Array<{ date: string, weather: string, demand: number, supply: number, idle: number, loss_krw: number }>,
 *   week_total: { idle: number, loss_krw: number }
 * }>}
 */
export function getForecast() {
  return apiFetch('/forecast');
}
