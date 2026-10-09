import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
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
      <div className="t-row"><span>공급</span><b>{d.supply}명</b></div>
      <div className="t-row"><span>유휴</span><b>{d.idle}인일</b></div>
      <div className="t-row"><span>손실</span><b>{formatManWon(d.loss_krw)}</b></div>
    </div>
  );
}

/**
 * 요일별 수요 vs 공급 막대 차트. 강수일은 배경 밴드로 강조.
 * rows: toRows(forecast) 결과
 */
export default function DemandSupplyChart({ rows }) {
  const demandColor = css('--series-demand') || '#1f766b';
  const supplyColor = css('--series-supply') || '#8a8880';
  const surfaceColor = css('--surface') || '#fcfcfb';
  const bandColor = css('--rain-band') || '#cde2fb';
  const bandAlpha = Number(css('--rain-band-alpha')) || 0.5;
  const rainAccent = css('--rain-accent') || '#1d62b8';
  const warnColor = css('--status-critical') || '#b93434';
  const gridColor = css('--grid') || '#e1e0d9';
  const axisColor = css('--axis') || '#c3c2b7';
  const muted = css('--text-muted') || '#898781';

  const rainLabel = ({ viewBox }) => (
    <text
      x={viewBox.x + viewBox.width / 2}
      y={viewBox.y + 14}
      textAnchor="middle"
      fill={rainAccent}
      fontSize={11}
      fontWeight={600}
    >
      강수
    </text>
  );

  return (
    <div>
      <div className="chart-legend" aria-hidden="true">
        <span><i className="swatch" style={{ background: demandColor }} />수요(명)</span>
        <span><i className="swatch" style={{ background: surfaceColor, border: `1.5px solid ${supplyColor}` }} />공급(명)</span>
        <span><i className="swatch swatch--band" />강수일</span>
        <span className="legend-idle">막대 위 숫자 = 유휴(인일)</span>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 24, right: 8, bottom: 0, left: -16 }} barGap={1} barCategoryGap="36%">
            <CartesianGrid vertical={false} stroke={gridColor} />
            {rows.filter((r) => r.rainy).map((r) => (
              <ReferenceArea
                key={r.date}
                x1={r.label}
                x2={r.label}
                fill={bandColor}
                fillOpacity={bandAlpha}
                strokeOpacity={0}
                ifOverflow="visible"
                label={rainLabel}
              />
            ))}
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={{ stroke: axisColor }}
              tick={{ fill: muted, fontSize: 12 }}
              tickFormatter={(label, i) => (rows[i]?.rainy ? `${label} (비)` : label)}
            />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: muted, fontSize: 12 }} allowDecimals={false} />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: gridColor, fillOpacity: 0.4 }} />
            <Bar dataKey="demand" name="수요" fill={demandColor} radius={[4, 4, 0, 0]} maxBarSize={36} isAnimationActive={false} />
            <Bar
              dataKey="supply"
              name="공급"
              fill={surfaceColor}
              stroke={supplyColor}
              strokeWidth={1.5}
              radius={[4, 4, 0, 0]}
              maxBarSize={36}
              isAnimationActive={false}
            >
              <LabelList
                dataKey="idle"
                position="top"
                formatter={(v) => (v > 0 ? v : '')}
                style={{ fill: warnColor, fontSize: 11, fontWeight: 700 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
