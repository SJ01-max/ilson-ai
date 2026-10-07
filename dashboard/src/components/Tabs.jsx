export default function Tabs({ tabs, value, onChange }) {
  return (
    <nav className="tabs" role="tablist" aria-label="화면 전환">
      {tabs.map((t) => (
        <button
          key={t.id}
          type="button"
          role="tab"
          className="tab"
          aria-selected={value === t.id}
          onClick={() => onChange(t.id)}
        >
          {t.label}
          {t.badge && <span className="badge">{t.badge}</span>}
        </button>
      ))}
    </nav>
  );
}
