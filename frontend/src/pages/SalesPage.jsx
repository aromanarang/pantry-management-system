import { useState } from "react";
import PageShell from "../layout/PageShell";

export default function SalesPage({ refreshData }) {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!file) {
      setError("Please choose a sales summary file.");
      return;
    }

    setIsSubmitting(true);
    setMessage("");
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("report", file);

    try {
      const response = await fetch("/import-sales-summary", {
        method: "POST",
        body: formData,
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || "Unable to import sales summary");
      }

      setResult(payload);
      setMessage("Inventory updated");
      setFile(null);
      event.target.reset();
      refreshData({ preserveView: true });
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PageShell
      title="Import Daily Sales"
      description="Import a sales summary so the system can detect dishes and deduct ingredients from pantry stock."
    >
      <div className="single-column-grid">
        <div className="panel">
          <div className="panel-title-row">
            <h3>Import Sales Summary</h3>
          </div>

          <form className="stack-form" onSubmit={handleSubmit}>
            <label className="file-input">
              <span>{file ? file.name : "Choose File (.csv)"}</span>
              <input
                type="file"
                accept=".csv"
                onChange={(event) => setFile(event.target.files[0] || null)}
              />
            </label>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Uploading..." : "Upload"}
            </button>
          </form>

          {message ? <p className="form-success">{message}</p> : null}
          {error ? <p className="form-error">{error}</p> : null}

          <div className="output-panel">
            <h4>Detected Dishes</h4>
            {result?.processed_sales?.length ? (
              result.processed_sales.map((item, index) => (
                <div className="output-row" key={`${item.menu_name}-${index}`}>
                  <div>
                    <strong>{item.menu_name}</strong>
                  </div>
                  <p>{item.quantity_sold}</p>
                </div>
              ))
            ) : (
              <p className="empty-state">Imported dishes will appear here after processing.</p>
            )}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
