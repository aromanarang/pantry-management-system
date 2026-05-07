import { Bar, Line } from "react-chartjs-2";
import { chartOptions } from "../config/chartConfig";
import InventoryHealthPanel from "../components/InventoryHealthPanel";
import SummaryCard from "../components/SummaryCard";
import PageShell from "../layout/PageShell";

export default function DashboardPage({ summary, pantry, reportInsights }) {
  const topIngredients = reportInsights?.top_ingredients || [];
  const monthlyTotals = reportInsights?.monthly_totals || [];

  const barData = {
    labels: topIngredients.map((item) => item.ingredient_name),
    datasets: [
      {
        data: topIngredients.map((item) => Number(item.total_consumption)),
        backgroundColor: topIngredients.map((_, index) =>
          ["#c8642b", "#da8c2c", "#e2aa24", "#35836c", "#4ea18a", "#88c4a6"][index % 6]
        ),
        borderRadius: 10,
      },
    ],
  };

  const lineData = {
    labels: monthlyTotals.map((item) => item.usage_month),
    datasets: [
      {
        data: monthlyTotals.map((item) => Number(item.total_consumption)),
        borderColor: "#1d705f",
        backgroundColor: "rgba(29, 112, 95, 0.18)",
        fill: true,
        tension: 0.32,
      },
    ],
  };

  return (
    <PageShell title="Dashboard">
      <div className="summary-grid summary-grid-three">
        <SummaryCard
          label="Total Ingredients"
          value={summary?.inventory?.total_ingredients || 0}
        />
        <SummaryCard
          label="Low Stock Items"
          value={summary?.inventory?.low_stock_count || 0}
        />
        <SummaryCard
          label="Today's Sales (Dishes)"
          value={summary?.sales_today?.sales_today || 0}
        />
      </div>

      <div className="dashboard-spotlight">
        <div className="hero-panel">
          <h3>Track pantry movement, detect stock risk, and view consumption trends from one place.</h3>
        </div>
        <InventoryHealthPanel pantry={pantry} />
      </div>

      <div className="chart-grid-two">
        <div className="panel chart-panel">
          <div className="panel-title-row">
            <h3>Top 20 Ingredients</h3>
          </div>
          <div className="chart-canvas">
            {topIngredients.length ? (
              <Bar data={barData} options={chartOptions} />
            ) : (
              <p className="empty-state">No report data available yet.</p>
            )}
          </div>
        </div>

        <div className="panel chart-panel">
          <div className="panel-title-row">
            <h3>Monthly Consumption</h3>
          </div>
          <div className="chart-canvas">
            {monthlyTotals.length ? (
              <Line data={lineData} options={chartOptions} />
            ) : (
              <p className="empty-state">Monthly consumption will appear after sales are recorded.</p>
            )}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
