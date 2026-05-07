import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Sidebar from "./layout/Sidebar";
import TopNavbar from "./layout/TopNavbar";
import DashboardPage from "./pages/DashboardPage";
import InventoryPage from "./pages/InventoryPage";
import StockPage from "./pages/StockPage";
import SalesPage from "./pages/SalesPage";

export default function App() {
  const [pantry, setPantry] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [summary, setSummary] = useState(null);
  const [reportInsights, setReportInsights] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  async function fetchAppData(options = {}) {
    const { preserveView = false } = options;

    setLoadError("");

    if (!preserveView) {
      setIsLoading(true);
    }

    try {
      const responses = await Promise.all([
        fetch("/pantry"),
        fetch("/low-stock"),
        fetch("/dashboard-summary"),
        fetch("/report-insights"),
      ]);

      const payloads = await Promise.all(responses.map((response) => response.json()));
      setPantry(payloads[0]);
      setLowStock(payloads[1]);
      setSummary(payloads[2]);
      setReportInsights(payloads[3]);
    } catch (error) {
      setLoadError("Unable to load application data. Please check the backend connection.");
    } finally {
      if (!preserveView) {
        setIsLoading(false);
      }
    }
  }

  useEffect(() => {
    fetchAppData();
  }, []);

  return (
    <div className="layout-shell">
      <Sidebar />

      <main className="main-shell">
        <TopNavbar />

        {loadError ? <div className="banner error">{loadError}</div> : null}

        {isLoading ? (
          <div className="banner">Loading RestroStock...</div>
        ) : (
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/dashboard"
              element={
                <DashboardPage
                  summary={summary}
                  pantry={pantry}
                  reportInsights={reportInsights}
                />
              }
            />
            <Route
              path="/inventory"
              element={
                <InventoryPage
                  pantry={pantry}
                  lowStock={lowStock}
                  reportInsights={reportInsights}
                />
              }
            />
            <Route path="/stock" element={<StockPage refreshData={fetchAppData} />} />
            <Route path="/sales" element={<SalesPage refreshData={fetchAppData} />} />
          </Routes>
        )}
      </main>
    </div>
  );
}
