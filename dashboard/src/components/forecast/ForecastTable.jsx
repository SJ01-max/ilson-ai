import { toMan } from '../../utils/forecast.js';

const WEATHER_ICON = { 비: '🌧️', 맑음: '☀️', 흐림: '☁️', 눈: '❄️', 소나기: '🌦️' };

export default function ForecastTable({ rows, total }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>날짜</th>
            <th className="left">날씨</th>
            <th>수요(명)</th>
            <th>공급(명)</th>
            <th>유휴(인일)</th>
            <th>손실액(만 원)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.date} className={r.rainy ? 'rainy' : undefined}>
              <td>
                {r.date} ({r.weekday})
              </td>
              <td className="left">
                <span className="weather-chip">
                  <span aria-hidden="true">{WEATHER_ICON[r.weather] ?? '🌡️'}</span>
                  {r.weather}
                </span>
              </td>
              <td>{r.demand}</td>
              <td>{r.supply}</td>
              <td className={r.idle > 0 ? 'idle-pos' : undefined}>{r.idle}</td>
              <td>{toMan(r.loss_krw)}</td>
            </tr>
          ))}
          {total && (
            <tr className="total">
              <td>주간 합계</td>
              <td className="left" />
              <td>{rows.reduce((s, r) => s + r.demand, 0)}</td>
              <td>{rows.reduce((s, r) => s + r.supply, 0)}</td>
              <td>{total.idle}</td>
              <td>{toMan(total.loss_krw)}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
