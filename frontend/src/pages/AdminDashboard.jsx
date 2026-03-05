import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import OpportunityCard from "@/components/OpportunityCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Search, Plus, FileText, Users, TrendingUp, GitBranch, RefreshCw, ShoppingBag, Building2, Wallet, AlertCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { SECTORS, REGIONS } from "@/data/tradeData";

const STATUSES = ["Active", "Draft", "Matched", "Closed"];

export default function AdminDashboard() {
  const { authAxios } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("opportunities");
  const [opportunities, setOpportunities] = useState([]);
  const [buyers, setBuyers] = useState([]);
  const [exporters, setExporters] = useState([]);
  const [stats, setStats] = useState(null);
  const [pendingFinanceRequests, setPendingFinanceRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usersLoading, setUsersLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [regionFilter, setRegionFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [userSearch, setUserSearch] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [oppRes, statsRes, financeRes] = await Promise.all([
        authAxios.get("/opportunities"),
        authAxios.get("/stats"),
        authAxios.get("/finance-requests?status=requested").catch(() => ({ data: [] }))
      ]);
      setOpportunities(oppRes.data);
      setStats(statsRes.data);
      setPendingFinanceRequests(financeRes.data);
    } catch (e) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    setUsersLoading(true);
    try {
      const [buyersRes, exportersRes] = await Promise.all([
        authAxios.get("/admin/users/buyers"),
        authAxios.get("/admin/users/exporters"),
      ]);
      setBuyers(buyersRes.data);
      setExporters(exportersRes.data);
    } catch (e) {
      toast.error("Failed to load users");
    } finally {
      setUsersLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    fetchUsers();
  }, []);

  const filteredOpportunities = opportunities.filter((opp) => {
    const matchesSearch = opp.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          opp.source_country.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSector = sectorFilter === "all" || opp.sector === sectorFilter;
    const matchesRegion = regionFilter === "all" || opp.region === regionFilter;
    const matchesStatus = statusFilter === "all" || opp.status === statusFilter;
    return matchesSearch && matchesSector && matchesRegion && matchesStatus;
  });

  const filteredBuyers = buyers.filter(b =>
    b.company_name?.toLowerCase().includes(userSearch.toLowerCase()) ||
    b.email?.toLowerCase().includes(userSearch.toLowerCase()) ||
    b.profile?.country?.toLowerCase().includes(userSearch.toLowerCase())
  );

  const filteredExporters = exporters.filter(e =>
    e.company_name?.toLowerCase().includes(userSearch.toLowerCase()) ||
    e.email?.toLowerCase().includes(userSearch.toLowerCase()) ||
    e.profile?.sectors?.some(s => s.toLowerCase().includes(userSearch.toLowerCase()))
  );

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-3xl font-bold text-slate-900 tracking-tight">
                Command Center
              </h1>
              <p className="mt-1 text-slate-500">Trade opportunity management dashboard</p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={() => { fetchData(); fetchUsers(); }}
                data-testid="refresh-btn"
                className="border-slate-200"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button
                onClick={() => navigate("/admin/create-opportunity")}
                data-testid="new-opportunity-btn"
                className="bg-navy hover:bg-charcoal text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Opportunity
              </Button>
            </div>
          </div>
        </header>

        <div className="p-8">
          {/* NBFC Finance Requests Alert */}
          {pendingFinanceRequests.length > 0 && (
            <div className="premium-card p-4 rounded-sm mb-6 border-l-4 border-l-amber-500 bg-amber-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-slate-900">
                      {pendingFinanceRequests.length} New NBFC Financing Request{pendingFinanceRequests.length > 1 ? "s" : ""} Pending
                    </p>
                    <p className="text-sm text-slate-600">
                      Exporters are waiting for their financing requests to be reviewed and submitted to NBFCs.
                    </p>
                  </div>
                </div>
                <Button
                  onClick={() => navigate("/admin/finance-requests")}
                  className="bg-amber-600 hover:bg-amber-700 text-white flex items-center gap-2 flex-shrink-0"
                >
                  <Wallet className="w-4 h-4" />
                  Review Requests
                </Button>
              </div>
            </div>
          )}

          {/* Stats Grid */}
          {stats && (
            <div className="grid grid-cols-5 gap-4 mb-8">
              <div className="premium-card p-5 rounded-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-50 rounded-sm flex items-center justify-center">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-xl font-bold text-slate-900">{stats.total_opportunities}</p>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Total Opps</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-5 rounded-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-emerald-50 rounded-sm flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-xl font-bold text-slate-900">{stats.active_opportunities}</p>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Active</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-5 rounded-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-50 rounded-sm flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-xl font-bold text-slate-900">{stats.total_exporters}</p>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Exporters</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-5 rounded-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-teal-50 rounded-sm flex items-center justify-center">
                    <ShoppingBag className="w-5 h-5 text-teal-600" />
                  </div>
                  <div>
                    <p className="text-xl font-bold text-slate-900">{buyers.length}</p>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Buyers</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-5 rounded-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-amber-50 rounded-sm flex items-center justify-center">
                    <GitBranch className="w-5 h-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-xl font-bold text-slate-900">{stats.total_deals}</p>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Active Deals</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex gap-1 mb-6 border-b border-slate-200">
            {[
              { key: "opportunities", label: "Opportunities", icon: FileText },
              { key: "exporters", label: `Exporters (${exporters.length})`, icon: Building2 },
              { key: "buyers", label: `Buyers (${buyers.length})`, icon: ShoppingBag },
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === key
                    ? "border-navy text-navy"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Opportunities Tab */}
          {activeTab === "opportunities" && (
            <>
              <div className="premium-card p-4 rounded-sm mb-6">
                <div className="flex items-center gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="Search opportunities..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      data-testid="search-input"
                      className="pl-10 bg-slate-50 border-slate-200"
                    />
                  </div>
                  <Select value={sectorFilter} onValueChange={setSectorFilter}>
                    <SelectTrigger className="w-52 bg-white" data-testid="sector-filter">
                      <SelectValue placeholder="All Sectors" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Sectors</SelectItem>
                      {SECTORS.map((s) => (
                        <SelectItem key={s} value={s}>{s}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={regionFilter} onValueChange={setRegionFilter}>
                    <SelectTrigger className="w-40 bg-white" data-testid="region-filter">
                      <SelectValue placeholder="All Regions" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Regions</SelectItem>
                      {REGIONS.map((r) => (
                        <SelectItem key={r} value={r}>{r}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-36 bg-white" data-testid="status-filter">
                      <SelectValue placeholder="All Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      {STATUSES.map((s) => (
                        <SelectItem key={s} value={s}>{s}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {loading ? (
                <div className="text-center py-12 text-slate-500">Loading opportunities...</div>
              ) : filteredOpportunities.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500">No opportunities found</p>
                  <Button
                    onClick={() => navigate("/admin/create-opportunity")}
                    className="mt-4 bg-navy hover:bg-charcoal text-white"
                  >
                    Create First Opportunity
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="opportunities-grid">
                  {filteredOpportunities.map((opp) => (
                    <OpportunityCard key={opp.id} opportunity={opp} showScores />
                  ))}
                </div>
              )}
            </>
          )}

          {/* Exporters Tab */}
          {activeTab === "exporters" && (
            <>
              <div className="premium-card p-4 rounded-sm mb-6">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="Search exporters by name, email, or sector..."
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    className="pl-10 bg-slate-50 border-slate-200"
                  />
                </div>
              </div>
              {usersLoading ? (
                <div className="text-center py-12 text-slate-500">Loading exporters...</div>
              ) : filteredExporters.length === 0 ? (
                <div className="text-center py-12">
                  <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500">No exporters found</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredExporters.map((exp) => (
                    <div key={exp.id} className="premium-card p-5 rounded-sm">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-purple-100 rounded-sm flex items-center justify-center text-purple-700 font-bold text-sm">
                            {exp.company_name?.charAt(0) || "E"}
                          </div>
                          <div>
                            <p className="font-semibold text-slate-900">{exp.company_name}</p>
                            <p className="text-sm text-slate-500">{exp.email}</p>
                          </div>
                        </div>
                        <Badge className={exp.profile ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}>
                          {exp.profile ? "Profile Complete" : "Profile Pending"}
                        </Badge>
                      </div>
                      {exp.profile && (
                        <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Sectors</span>
                            <div className="flex flex-wrap gap-1">
                              {exp.profile.sectors?.map(s => (
                                <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                              ))}
                            </div>
                          </div>
                          <div>
                            <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Products</span>
                            <p className="text-slate-700 truncate">{exp.profile.products?.join(", ") || "—"}</p>
                          </div>
                          <div>
                            <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Capacity</span>
                            <p className="text-slate-700">{exp.profile.capacity || "—"}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Buyers Tab */}
          {activeTab === "buyers" && (
            <>
              <div className="premium-card p-4 rounded-sm mb-6">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="Search buyers by name, email, or country..."
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    className="pl-10 bg-slate-50 border-slate-200"
                  />
                </div>
              </div>
              {usersLoading ? (
                <div className="text-center py-12 text-slate-500">Loading buyers...</div>
              ) : filteredBuyers.length === 0 ? (
                <div className="text-center py-12">
                  <ShoppingBag className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500">No buyers found</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredBuyers.map((buyer) => (
                    <div key={buyer.id} className="premium-card p-5 rounded-sm">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-teal-100 rounded-sm flex items-center justify-center text-teal-700 font-bold text-sm">
                            {buyer.company_name?.charAt(0) || "B"}
                          </div>
                          <div>
                            <p className="font-semibold text-slate-900">{buyer.company_name}</p>
                            <p className="text-sm text-slate-500">{buyer.email}</p>
                          </div>
                        </div>
                        <Badge className={buyer.profile ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}>
                          {buyer.profile ? "Profile Complete" : "Profile Pending"}
                        </Badge>
                      </div>
                      {buyer.profile && (
                        <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Country</span>
                            <p className="text-slate-700">{buyer.profile.country || "—"}</p>
                          </div>
                          <div>
                            <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Industry</span>
                            <p className="text-slate-700">{buyer.profile.industry || "—"}</p>
                          </div>
                          <div>
                            <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Preferred Sectors</span>
                            <div className="flex flex-wrap gap-1">
                              {buyer.profile.preferred_sectors?.map(s => (
                                <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
