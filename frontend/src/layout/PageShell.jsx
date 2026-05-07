export default function PageShell({ title, description, children }) {
  return (
    <section className="page-shell">
      <div className="page-header">
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {children}
    </section>
  );
}
