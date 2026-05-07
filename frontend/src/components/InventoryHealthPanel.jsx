import { useMemo } from "react";

export default function InventoryHealthPanel({ pantry }) {
  const health = useMemo(() => {
    const total = pantry.length || 1;
    const healthy = pantry.filter((item) => item.quantity > item.threshold * 1.25).length;
    const warning = pantry.filter(
      (item) => item.quantity >= item.threshold && item.quantity <= item.threshold * 1.25
    ).length;
    const critical = pantry.filter((item) => item.quantity < item.threshold).length;

    return {
      healthy: Math.round((healthy / total) * 100),
      warning: Math.round((warning / total) * 100),
      critical: Math.round((critical / total) * 100),
    };
  }, [pantry]);

  return (
    <div className="panel inventory-health-panel">
      <div className="panel-title-row">
        <h3>Inventory Health</h3>
      </div>
      <div className="health-list">
        <div className="health-row healthy">
          <span>Healthy</span>
          <strong>{health.healthy}%</strong>
        </div>
        <div className="health-row warning">
          <span>Warning</span>
          <strong>{health.warning}%</strong>
        </div>
        <div className="health-row critical">
          <span>Critical</span>
          <strong>{health.critical}%</strong>
        </div>
      </div>
    </div>
  );
}
