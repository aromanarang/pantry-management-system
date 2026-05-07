import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "../config/navigation";

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <nav className="side-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
            to={item.to}
          >
            <item.icon />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
