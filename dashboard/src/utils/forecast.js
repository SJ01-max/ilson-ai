/**
 * 유휴 예보 데이터 가공 유틸 (순수 함수 — UI 의존 없음)
 */

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토'];

/** 'YYYY-MM-DD' → 로컬 Date (타임존 밀림 방지) */
export function parseDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
}

/** 'YYYY-MM-DD' → '월' */
export function weekdayOf(iso) {
  return WEEKDAYS[parseDate(iso).getDay()];
}

/** 'YYYY-MM-DD' → '10/12' */
export function shortDate(iso) {
  const d = parseDate(iso);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

/** 강수일 판정 — 날씨 문자열 기준 (비, 소나기, 눈, 비/눈 등) */
export function isRainy(weather = '') {
  return /비|소나기|눈/.test(weather);
}

/** 원 → '180만 원' / '0원' / '1억 2,000만 원' */
export function formatManWon(krw) {
  if (!krw) return '0원';
  const man = Math.round(krw / 10000);
  if (man >= 10000) {
    const eok = Math.floor(man / 10000);
    const rest = man % 10000;
    return rest ? `${eok}억 ${rest.toLocaleString('ko-KR')}만 원` : `${eok}억 원`;
  }
  return `${man.toLocaleString('ko-KR')}만 원`;
}

/** 원 → '180' (표 셀용, 단위는 헤더에 표기) */
export function toMan(krw) {
  return Math.round((krw ?? 0) / 10000).toLocaleString('ko-KR');
}

/** 해당 날짜가 속한 주의 월요일 (로컬) */
function mondayOf(date) {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diff = (d.getDay() + 6) % 7; // 월=0 … 일=6
  d.setDate(d.getDate() - diff);
  return d;
}

/** week_start 기준으로 '이번 주' / '다음 주' / '10/12 주' 라벨 */
export function weekLabel(weekStartIso, now = new Date()) {
  const thisMon = mondayOf(now);
  const targetMon = mondayOf(parseDate(weekStartIso));
  const diffWeeks = Math.round((targetMon - thisMon) / (7 * 24 * 3600 * 1000));
  if (diffWeeks === 0) return '이번 주';
  if (diffWeeks === 1) return '다음 주';
  if (diffWeeks === -1) return '지난주';
  return `${shortDate(weekStartIso)} 주`;
}

/**
 * 상단 핵심 문구 생성
 * 예) "다음 주 월·화 강수 → 유휴 18인일 → 손실 180만 원"
 * 강수일이 없으면 "다음 주 강수 없음 → 유휴 N인일 → 손실 …" 형태.
 *
 * @returns {{ text: string, parts: string[], rainDays: Array, idle: number, lossKrw: number }}
 */
export function buildHeadline(forecast, now = new Date()) {
  const rainDays = (forecast?.days ?? []).filter((d) => isRainy(d.weather));
  const idle = rainDays.reduce((s, d) => s + (d.idle ?? 0), 0);
  const lossKrw = rainDays.reduce((s, d) => s + (d.loss_krw ?? 0), 0);
  const week = weekLabel(forecast?.week_start ?? forecast?.days?.[0]?.date, now);

  const parts = rainDays.length
    ? [
        `${week} ${rainDays.map((d) => weekdayOf(d.date)).join('·')} 강수`,
        `유휴 ${idle}인일`,
        `손실 ${formatManWon(lossKrw)}`,
      ]
    : [
        `${week} 강수 없음`,
        `유휴 ${forecast?.week_total?.idle ?? 0}인일`,
        `손실 ${formatManWon(forecast?.week_total?.loss_krw ?? 0)}`,
      ];

  return { text: parts.join(' → '), parts, rainDays, idle, lossKrw };
}

/** 차트·표용 행 데이터 (라벨 미리 계산) */
export function toRows(forecast) {
  return (forecast?.days ?? []).map((d) => ({
    ...d,
    weekday: weekdayOf(d.date),
    label: `${weekdayOf(d.date)} ${shortDate(d.date)}`,
    rainy: isRainy(d.weather),
  }));
}
