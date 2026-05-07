import { formatNumber, getStatusTone } from "../utils/formatters";

export default function InventoryTable({ items, search, filter }) {
  return (
    <div className="panel table-panel">
      <div className="table-heading">
        <div>
          <h3>Inventory Table</h3>
          <p>
            {filter === "high-usage"
              ? "Ingredients sorted from high usage to low usage."
              : "Live ingredient availability with threshold status."}
          </p>
        </div>
        <div className="table-meta">
          <span>{items.length} results</span>
          {search ? <span>Search: {search}</span> : null}
        </div>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Ingredient</th>
              <th>Available</th>
              <th>Threshold</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.length ? (
              items.map((item) => {
                const tone = getStatusTone(item.quantity, item.threshold);

                return (
                  <tr key={item.ingredient_id}>
                    <td>{item.ingredient_name}</td>
                    <td>
                      {formatNumber(item.quantity)} {item.unit}
                    </td>
                    <td>
                      {formatNumber(item.threshold)} {item.unit}
                    </td>
                    <td>
                      <span className={`status-pill ${tone}`}>
                        {tone === "healthy"
                          ? "In stock"
                          : tone === "warning"
                            ? "Near threshold"
                            : "Low stock"}
                      </span>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan="4" className="no-results">
                  No results
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
