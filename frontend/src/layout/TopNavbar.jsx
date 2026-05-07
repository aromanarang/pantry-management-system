import StoreTwoToneIcon from "@mui/icons-material/StoreTwoTone";

export default function TopNavbar() {
  return (
    <header className="topbar">
      <div className="topbar-brand">
        <div className="topbar-icon">
          <StoreTwoToneIcon fontSize="medium" />
        </div>
        <div>
          <p className="topbar-caption">Restaurant Inventory Management Platform</p>
          <h2>RestroStock</h2>
        </div>
      </div>
    </header>
  );
}
