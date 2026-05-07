import DashboardTwoToneIcon from "@mui/icons-material/DashboardTwoTone";
import AddBoxTwoToneIcon from "@mui/icons-material/AddBoxTwoTone";
import Inventory2TwoToneIcon from "@mui/icons-material/Inventory2TwoTone";
import PointOfSaleTwoToneIcon from "@mui/icons-material/PointOfSaleTwoTone";

export const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: DashboardTwoToneIcon },
  { to: "/inventory", label: "Inventory", icon: Inventory2TwoToneIcon },
  { to: "/stock", label: "Add New Stock", icon: AddBoxTwoToneIcon },
  { to: "/sales", label: "Record Daily Sales", icon: PointOfSaleTwoToneIcon },
];
