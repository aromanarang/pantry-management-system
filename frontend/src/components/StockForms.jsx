import { useState } from "react";
import { formatNumber } from "../utils/formatters";

export function GroceryUploadPanel({ onComplete }) {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!file) {
      setError("Please choose a grocery bill image.");
      return;
    }

    setIsSubmitting(true);
    setMessage("");
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("bill", file);

    try {
      const response = await fetch("/upload-bill", {
        method: "POST",
        body: formData,
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || "Unable to upload bill");
      }

      setResult(payload);
      setMessage("Inventory updated");
      setFile(null);
      event.target.reset();
      onComplete({ preserveView: true });
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="panel split-panel">
      <div className="panel-title-row">
        <h3>Upload Grocery Bill</h3>
      </div>

      <form className="stack-form" onSubmit={handleSubmit}>
        <label className="file-input">
          <span>{file ? file.name : "Choose File (.jpg, .jpeg or .png)"}</span>
          <input
            type="file"
            accept=".jpg,.jpeg,.png,image/png,image/jpeg"
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
        <h4>Extracted Items</h4>
        {result?.processed_items?.length ? (
          result.processed_items.map((item, index) => (
            <div className="output-row" key={`${item.matched_name}-${index}`}>
              <div>
                <strong>{item.matched_name}</strong>
              </div>
              <p>
                {formatNumber(item.quantity_added)} {item.stored_unit}
              </p>
            </div>
          ))
        ) : (
          <p className="empty-state">Uploaded items will appear here after processing.</p>
        )}
      </div>
    </div>
  );
}

export function ManualStockPanel({ onComplete }) {
  const [form, setForm] = useState({
    ingredient_name: "",
    quantity: "",
    unit: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage("");
    setError("");

    try {
      const response = await fetch("/add-stock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || "Unable to add stock");
      }

      setMessage("Inventory updated");
      setForm({ ingredient_name: "", quantity: "", unit: "" });
      onComplete({ preserveView: true });
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="panel split-panel">
      <div className="panel-title-row">
        <h3>Add Stock Manually</h3>
      </div>
      <form className="stack-form" onSubmit={handleSubmit}>
        <input
          name="ingredient_name"
          placeholder="Ingredient name"
          value={form.ingredient_name}
          onChange={(event) =>
            setForm((current) => ({ ...current, ingredient_name: event.target.value }))
          }
        />
        <input
          name="quantity"
          type="number"
          min="0"
          step="0.01"
          placeholder="Quantity"
          value={form.quantity}
          onChange={(event) =>
            setForm((current) => ({ ...current, quantity: event.target.value }))
          }
        />
        <input
          name="unit"
          placeholder="Unit"
          value={form.unit}
          onChange={(event) =>
            setForm((current) => ({ ...current, unit: event.target.value }))
          }
        />
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : "Add Stock"}
        </button>
      </form>

      {message ? <p className="form-success">{message}</p> : null}
      {error ? <p className="form-error">{error}</p> : null}
    </div>
  );
}
