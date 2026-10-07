/**
 * 유휴 예보 API (새영 → 정환)
 * 응답 형식: docs/interface.md §3
 *
 * 10/12 통합 시 이 파일의 함수 본문만 fetch()로 교체한다.
 * 화면 컴포넌트는 이 함수만 호출하고, mock JSON을 직접 import하지 않는다.
 *
 * 교체 예시:
 *   const res = await fetch(`${import.meta.env.VITE_API_BASE}/forecast`);
 *   if (!res.ok) throw new Error(`forecast ${res.status}`);
 *   return res.json();
 */
import mock from '../mock/forecast.json';

/**
 * @returns {Promise<{
 *   week_start: string,
 *   days: Array<{ date: string, weather: string, demand: number, supply: number, idle: number, loss_krw: number }>,
 *   week_total: { idle: number, loss_krw: number }
 * }>}
 */
export async function getForecast() {
  // 실제 네트워크처럼 비동기로 동작하도록 한 틱 지연
  await new Promise((r) => setTimeout(r, 150));
  return structuredClone(mock);
}
