import { toMan } from '../../utils/forecast.js';

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
                <span className={r.rainy ? 'weather-chip weather-chip--rain' : 'weather-chip'}>
                  {r.weather}
                </span>
              </td>
              <td>{r.demand}</td>
              <td>{r.supply}</td>
              <td className={r.idle > 0 ? 'num-warn' : undefined}>{r.idle}</td>
              <td className={r.loss_krw > 0 ? 'num-warn' : undefined}>{toMan(r.loss_krw)}</td>
            </tr>
          ))}
          {total && (
            <tr className="total">
              <td>주간 합계</td>
              <td className="left" />
              <td>{rows.reduce((s, r) => s + r.demand, 0)}</td>
              <td>{rows.reduce((s, r) => s + r.supply, 0)}</td>
              <td className="num-warn">{total.idle}</td>
              <td className="num-warn">{toMan(total.loss_krw)}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
