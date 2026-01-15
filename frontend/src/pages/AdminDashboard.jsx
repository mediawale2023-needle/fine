import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import OpportunityCard from "@/components/OpportunityCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Search, Plus, FileText, Users, TrendingUp, GitBranch, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";

const SECTORS = ["Agriculture", "Marine / Frozen Foods", "Pharma", "Special Chemicals", "Value-Added Agri Products"];
const REGIONS = ["Africa", "Middle East", "Europe"];
const STATUSES = ["Active", "Draft", "Matched", "Closed"];

export default function AdminDashboard() {
  const { authAxios } = useAuth();
  const navigate = useNavigate();
  const [opportunities, setOpportunities] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [regionFilter, setRegionFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [oppRes, statsRes] = await Promise.all([
        authAxios.get("/opportunities"),
        authAxios.get("/stats")
      ]);
      setOpportunities(oppRes.data);
      setStats(statsRes.data);
    } catch (e) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredOpportunities = opportunities.filter((opp) => {
    const matchesSearch = opp.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          opp.source_country.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSector = sectorFilter === "all" || opp.sector === sectorFilter;
    const matchesRegion = regionFilter === "all" || opp.region === regionFilter;
    const matchesStatus = statusFilter === "all" || opp.status === statusFilter;
    return matchesSearch && matchesSector && matchesRegion && matchesStatus;
  });

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
                onClick={fetchData}
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
          {/* Stats Grid */}
          {stats && (
            <div className="grid grid-cols-4 gap-6 mb-8">
              <div className="premium-card p-6 rounded-sm">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-50 rounded-sm flex items-center justify-center">
                    <FileText className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.total_opportunities}</p>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Total Opportunities</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-6 rounded-sm">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-emerald-50 rounded-sm flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.active_opportunities}</p>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Active</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-6 rounded-sm">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-purple-50 rounded-sm flex items-center justify-center">
                    <Users className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.total_exporters}</p>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Exporters</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-6 rounded-sm">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-amber-50 rounded-sm flex items-center justify-center">
                    <GitBranch className="w-6 h-6 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.total_deals}</p>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Active Deals</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Filters */}
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
                <SelectTrigger className="w-48 bg-white" data-testid="sector-filter">
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

          {/* Opportunities Grid */}
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
        </div>
      </main>
    </div>
  );
}
