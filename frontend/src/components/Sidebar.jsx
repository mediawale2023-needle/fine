import { useAuth } from "@/App";
import { useNavigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  FileText,
  PlusCircle,
  GitBranch,
  User,
  LogOut,
  Building2,
  Wallet,
  CreditCard,
  DollarSign,
  BarChart2,
  FileSearch,
  Globe,
  ClipboardList,
  TrendingUp,
} from "lucide-react";

const ADMIN_LINKS = [
  { path: "/admin", icon: LayoutDashboard, label: "Dashboard" },
  { path: "/admin/create-opportunity", icon: PlusCircle, label: "New Opportunity" },
  { path: "/admin/pipeline", icon: GitBranch, label: "Pipeline" },
  { path: "/admin/finance-requests", icon: Wallet, label: "Finance Requests" },
  { path: "/admin/revenue", icon: DollarSign, label: "Revenue" },
  { path: "/market-intelligence", icon: BarChart2, label: "Market Intel" },
  { path: "/document-intelligence", icon: FileSearch, label: "Doc Intelligence" },
];

const EXPORTER_LINKS = [
  { path: "/exporter", icon: FileText, label: "Opportunities" },
  { path: "/exporter/profile", icon: User, label: "My Profile" },
  { path: "/exporter/financing", icon: Wallet, label: "Trade Financing" },
  { path: "/exporter/subscription", icon: CreditCard, label: "Subscription" },
  { path: "/market-intelligence", icon: TrendingUp, label: "Market Intel" },
  { path: "/document-intelligence", icon: FileSearch, label: "Doc Intelligence" },
];

const BUYER_LINKS = [
  { path: "/buyer", icon: ClipboardList, label: "My RFQs" },
  { path: "/buyer/post-rfq", icon: PlusCircle, label: "Post Requirement" },
  { path: "/buyer/profile", icon: User, label: "Buyer Profile" },
  { path: "/market-intelligence", icon: Globe, label: "Market Intel" },
];

export default function Sidebar() {
  const { user, logout, authAxios } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [pendingFinanceCount, setPendingFinanceCount] = useState(0);

  const role = user?.role;

  useEffect(() => {
    if (role === "admin" && authAxios) {
      authAxios.get("/finance-requests?status=requested")
        .then(res => setPendingFinanceCount(res.data.length))
        .catch(() => {});
    }
  }, [role, authAxios]);
  const links =
    role === "admin" ? ADMIN_LINKS :
    role === "buyer" ? BUYER_LINKS :
    EXPORTER_LINKS;

  const portalLabel =
    role === "admin" ? "Admin Portal" :
    role === "buyer" ? "Buyer Portal" :
    "Exporter Portal";

  const isActive = (path) => {
    // Exact match for root dashboard routes, prefix match for others
    if (path === "/admin" || path === "/exporter" || path === "/buyer") {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className="w-64 navy-sidebar h-screen flex flex-col sticky top-0">
      {/* Logo */}
      <div className="p-6 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gold/20 rounded-sm flex items-center justify-center">
            <span className="text-gold font-display font-bold text-lg">T</span>
          </div>
          <div>
            <h1 className="font-display text-lg font-semibold text-white">TradeNexus</h1>
            <p className="text-xs text-white/60 uppercase tracking-wider">{portalLabel}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-1">
          {links.map((link) => (
            <li key={link.path}>
              <button
                onClick={() => navigate(link.path)}
                data-testid={`nav-${link.label.toLowerCase().replace(/\s+/g, "-")}`}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-sm transition-colors text-sm ${
                  isActive(link.path)
                    ? "bg-white/10 text-white"
                    : "text-white/75 hover:bg-white/5 hover:text-white"
                }`}
              >
                <link.icon className="w-4 h-4 flex-shrink-0" strokeWidth={1.5} />
                <span className="font-medium flex-1 text-left">{link.label}</span>
                {link.label === "Finance Requests" && pendingFinanceCount > 0 && (
                  <span className="bg-amber-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center flex-shrink-0">
                    {pendingFinanceCount > 9 ? "9+" : pendingFinanceCount}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-slate-700">
        <div className="flex items-center gap-3 px-4 py-3 mb-2">
          <div className="w-8 h-8 bg-slate-600 rounded-full flex items-center justify-center flex-shrink-0">
            <Building2 className="w-4 h-4 text-white/60" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.company_name}</p>
            <p className="text-xs text-white/50 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          data-testid="logout-btn"
          className="w-full flex items-center gap-3 px-4 py-2.5 text-white/75 hover:bg-white/5 hover:text-white rounded-sm transition-colors text-sm"
        >
          <LogOut className="w-4 h-4" strokeWidth={1.5} />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
