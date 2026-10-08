export default function Placeholder({ title, due, items = [] }) {
  return (
    <section className="card placeholder">
      <h2>{title}</h2>
      <p>준비 중입니다. {due && `${due} 구현 예정`}</p>
      {items.length > 0 && (
        <ul>
          {items.map((it) => (
            <li key={it}>{it}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
