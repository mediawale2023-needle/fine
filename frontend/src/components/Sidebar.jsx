import { useAuth } from "@/App";
import { useNavigate, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, 
  FileText, 
  PlusCircle, 
  GitBranch, 
  User, 
  LogOut,
  Building2,
  Wallet,
  ShieldCheck,
  CreditCard,
  DollarSign
} from "lucide-react";

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isAdmin = user?.role === "admin";

  const adminLinks = [
    { path: "/admin", icon: LayoutDashboard, label: "Dashboard" },
    { path: "/admin/create-opportunity", icon: PlusCircle, label: "New Opportunity" },
    { path: "/admin/pipeline", icon: GitBranch, label: "Pipeline" },
    { path: "/admin/finance-requests", icon: Wallet, label: "Finance Requests" },
    { path: "/admin/revenue", icon: DollarSign, label: "Revenue" },
  ];

  const exporterLinks = [
    { path: "/exporter", icon: FileText, label: "Opportunities" },
    { path: "/exporter/financing", icon: Wallet, label: "Trade Financing" },
    { path: "/exporter/subscription", icon: CreditCard, label: "Subscription" },
    { path: "/exporter/profile", icon: User, label: "My Profile" },
  ];

  const links = isAdmin ? adminLinks : exporterLinks;

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
            <p className="text-xs text-slate-400 uppercase tracking-wider">
              {isAdmin ? "Admin Portal" : "Exporter Portal"}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {links.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <li key={link.path}>
                <button
                  onClick={() => navigate(link.path)}
                  data-testid={`nav-${link.label.toLowerCase().replace(' ', '-')}`}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-sm transition-colors ${
                    isActive 
                      ? "bg-white/10 text-white" 
                      : "text-slate-300 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <link.icon className="w-5 h-5" strokeWidth={1.5} />
                  <span className="font-medium">{link.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-slate-700">
        <div className="flex items-center gap-3 px-4 py-3 mb-2">
          <div className="w-8 h-8 bg-slate-600 rounded-full flex items-center justify-center">
            <Building2 className="w-4 h-4 text-slate-300" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.company_name}</p>
            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          data-testid="logout-btn"
          className="w-full flex items-center gap-3 px-4 py-3 text-slate-300 hover:bg-white/5 hover:text-white rounded-sm transition-colors"
        >
          <LogOut className="w-5 h-5" strokeWidth={1.5} />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
