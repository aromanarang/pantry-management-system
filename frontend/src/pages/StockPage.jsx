import { GroceryUploadPanel, ManualStockPanel } from "../components/StockForms";
import PageShell from "../layout/PageShell";

export default function StockPage({ refreshData }) {
  return (
    <PageShell
      title="Add New Stock"
      description="Upload grocery bills or add ingredient quantities manually to update pantry inventory."
    >
      <div className="two-column-grid">
        <GroceryUploadPanel onComplete={refreshData} />
        <ManualStockPanel onComplete={refreshData} />
      </div>
    </PageShell>
  );
}
