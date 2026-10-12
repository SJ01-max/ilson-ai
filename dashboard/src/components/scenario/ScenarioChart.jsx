import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatManWon } from '../../utils/forecast.js';

const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="tooltip">
      <div className="t-title">
        {d.label} · {d.weather}
      </div>
      <div className="t-row"><span>수요</span><b>{d.demand}명</b></div>
      <div className="t-row"><span>공급 현재 → 시나리오</span><b>{d.base_supply} → {d.supply}명</b></div>
      <div className="t-row"><span>유휴 현재 → 시나리오</span><b>{d.base_idle} → {d.idle}인일</b></div>
      {d.shortage > 0 && <div className="t-row"><span>부족</span><b>{d.shortage}명</b></div>}
      <div className="t-row"><span>환산액(시나리오)</span><b>{formatManWon(d.loss_krw)}</b></div>
    </div>
  );
}

/**
 * 날짜별 유휴 비교: 현재(윤곽선) vs 시나리오(빨강 채움). 빨강=유휴·유휴 인건비 환산액, 강수일은 파랑 밴드.
 */
export default function ScenarioChart({ rows }) {
  const warnColor = css('--status-critical') || '#b93434';
  const supplyColor = css('--series-supply') || '#8a8880';
  const surfaceColor = css('--surface') || '#fcfcfb';
  const bandColor = css('--rain-band') || '#cde2fb';
  const bandAlpha = Number(css('--rain-band-alpha')) || 0.5;
  const gridColor = css('--grid') || '#e1e0d9';
  const axisColor = css('--axis') || '#c3c2b7';
  const muted = css('--text-muted') || '#898781';

  return (
    <div>
      <div className="chart-legend" aria-hidden="true">
        <span><i className="swatch" style={{ background: surfaceColor, border: `1.5px solid ${supplyColor}` }} />유휴 현재(인일)</span>
        <span><i className="swatch" style={{ background: warnColor }} />유휴 시나리오(인일)</span>
        <span><i className="swatch swatch--band" />강수일</span>
      </div>
      <div className="chart-wrap chart-wrap--short">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: -16 }} barGap={2} barCategoryGap="36%">
            <CartesianGrid vertical={false} stroke={gridColor} />
            {rows.filter((r) => r.rainy).map((r) => (
              <ReferenceArea key={r.date} x1={r.label} x2={r.label} fill={bandColor} fillOpacity={bandAlpha} strokeOpacity={0} />
            ))}
            <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: axisColor }} tick={{ fill: muted, fontSize: 12 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: muted, fontSize: 12 }} allowDecimals={false} />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: gridColor, fillOpacity: 0.4 }} />
            <Bar
              dataKey="base_idle"
              name="유휴 현재"
              fill={surfaceColor}
              stroke={supplyColor}
              strokeWidth={1.5}
              radius={[4, 4, 0, 0]}
              maxBarSize={32}
              isAnimationActive={false}
            />
            <Bar dataKey="idle" name="유휴 시나리오" fill={warnColor} radius={[4, 4, 0, 0]} maxBarSize={32} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
