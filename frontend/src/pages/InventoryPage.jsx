import { useMemo, useState } from "react";
import SearchTwoToneIcon from "@mui/icons-material/SearchTwoTone";
import InventoryTable from "../components/InventoryTable";
import PageShell from "../layout/PageShell";

export default function InventoryPage({ pantry, lowStock, reportInsights }) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const usageRank = useMemo(() => {
    const rankedItems = reportInsights?.top_ingredients || [];
    return new Map(
      rankedItems.map((item, index) => [item.ingredient_name.toLowerCase(), index])
    );
  }, [reportInsights]);

  const filteredItems = useMemo(() => {
    const needle = search.trim().toLowerCase();
    let nextItems = [...pantry];

    if (needle) {
      nextItems = nextItems.filter((item) =>
        item.ingredient_name.toLowerCase().includes(needle)
      );
    }

    if (filter === "low-stock") {
      nextItems = nextItems.filter((item) => item.quantity < item.threshold);
    }

    if (filter === "in-stock") {
      nextItems = nextItems.filter((item) => item.quantity > item.threshold * 1.25);
    }

    if (filter === "near-threshold") {
      nextItems = nextItems.filter(
        (item) => item.quantity >= item.threshold && item.quantity <= item.threshold * 1.25
      );
    }

    if (filter === "high-usage") {
      nextItems.sort((left, right) => {
        const leftRank = usageRank.get(left.ingredient_name.toLowerCase());
        const rightRank = usageRank.get(right.ingredient_name.toLowerCase());

        if (leftRank !== undefined && rightRank !== undefined) {
          return leftRank - rightRank;
        }
        if (leftRank !== undefined) {
          return -1;
        }
        if (rightRank !== undefined) {
          return 1;
        }

        return left.ingredient_name.localeCompare(right.ingredient_name);
      });
    }

    return nextItems;
  }, [filter, pantry, search, usageRank]);

  return (
    <PageShell
      title="Inventory"
      description="Search ingredients, review threshold risk, and inspect inventory status."
    >
      <div className="panel inventory-controls">
        <label className="search-input">
          <SearchTwoToneIcon />
          <input
            type="search"
            placeholder="Search Ingredient"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <div className="filter-bar">
          <button
            type="button"
            className={filter === "all" ? "filter-chip active" : "filter-chip"}
            onClick={() => setFilter("all")}
          >
            All
          </button>
          <button
            type="button"
            className={filter === "low-stock" ? "filter-chip active" : "filter-chip"}
            onClick={() => setFilter("low-stock")}
          >
            Low Stock
          </button>
          <button
            type="button"
            className={filter === "in-stock" ? "filter-chip active" : "filter-chip"}
            onClick={() => setFilter("in-stock")}
          >
            In Stock
          </button>
          <button
            type="button"
            className={filter === "near-threshold" ? "filter-chip active" : "filter-chip"}
            onClick={() => setFilter("near-threshold")}
          >
            Near Threshold
          </button>
          <button
            type="button"
            className={filter === "high-usage" ? "filter-chip active" : "filter-chip"}
            onClick={() => setFilter("high-usage")}
          >
            High Usage
          </button>
        </div>
      </div>

      <InventoryTable items={filteredItems} search={search} filter={filter} />

      {!search && filter === "low-stock" && lowStock.length === 0 ? (
        <p className="helper-note">No ingredients are currently below threshold.</p>
      ) : null}
    </PageShell>
  );
}
