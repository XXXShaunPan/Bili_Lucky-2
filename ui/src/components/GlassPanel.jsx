export default function GlassPanel({
  icon,
  title,
  subtitle,
  count,
  tone = 'cyan',
  children,
}) {
  return (
    <section className={`glass-panel panel-${tone}`}>
      <header className="panel-header">
        <span className="panel-icon">{icon}</span>
        <span className="panel-heading">
          <strong>{title}</strong>
          <small>{subtitle}</small>
        </span>
        <span className="panel-count">{count}</span>
      </header>
      <div className="panel-content">{children}</div>
    </section>
  )
}
