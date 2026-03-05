import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import OpportunityCard from "@/components/OpportunityCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Search, FileText, CheckCircle, Clock, RefreshCw, MessageSquare, Wallet, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

const SECTORS = ["Agriculture", "Marine / Frozen Foods", "Pharma", "Special Chemicals", "Value-Added Agri Products"];

export default function ExporterDashboard() {
  const { authAxios, user } = useAuth();
  const navigate = useNavigate();
  const [opportunities, setOpportunities] = useState([]);
  const [myInterests, setMyInterests] = useState([]);
  const [myDeals, setMyDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [hasProfile, setHasProfile] = useState(false);
  const [financeRequests, setFinanceRequests] = useState([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [oppRes, interestsRes, dealsRes, financeRes] = await Promise.all([
        authAxios.get("/opportunities?status=Active"),
        authAxios.get("/my-interests"),
        authAxios.get("/deals"),
        authAxios.get("/finance-requests").catch(() => ({ data: [] }))
      ]);
      setOpportunities(oppRes.data);
      setMyInterests(interestsRes.data);
      setMyDeals(dealsRes.data);
      setFinanceRequests(financeRes.data);

      // Check if profile exists
      try {
        await authAxios.get("/exporter-profiles/me");
        setHasProfile(true);
      } catch (e) {
        setHasProfile(false);
      }
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
    return matchesSearch && matchesSector;
  });

  const interestedIds = new Set(myInterests.map((i) => i.opportunity_id));

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-3xl font-bold text-slate-900 tracking-tight">
                Trade Opportunities
              </h1>
              <p className="mt-1 text-slate-500">Browse and express interest in trade opportunities</p>
            </div>
            <Button
              variant="outline"
              onClick={fetchData}
              data-testid="refresh-btn"
              className="border-slate-200"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </header>

        <div className="p-8">
          {/* Profile Alert */}
          {!hasProfile && (
            <div className="premium-card p-4 rounded-sm mb-6 border-l-4 border-l-gold bg-amber-50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Complete Your Profile</p>
                  <p className="text-sm text-slate-600">Create your exporter profile to express interest in opportunities</p>
                </div>
                <Button
                  onClick={() => navigate("/exporter/profile")}
                  data-testid="create-profile-btn"
                  className="bg-navy hover:bg-charcoal text-white"
                >
                  Create Profile
                </Button>
              </div>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 mb-8">
            <div className="premium-card p-6 rounded-sm">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-50 rounded-sm flex items-center justify-center">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{opportunities.length}</p>
                  <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Available</p>
                </div>
              </div>
            </div>
            <div className="premium-card p-6 rounded-sm">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-emerald-50 rounded-sm flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{myInterests.length}</p>
                  <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Interests</p>
                </div>
              </div>
            </div>
            <div className="premium-card p-6 rounded-sm">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-purple-50 rounded-sm flex items-center justify-center">
                  <Clock className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{myDeals.length}</p>
                  <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Active Deals</p>
                </div>
              </div>
            </div>
          </div>

          {/* NBFC / Trade Financing Banner */}
          <div className="premium-card p-6 rounded-sm mb-6 border-l-4 border-l-[#0A192F] bg-gradient-to-r from-slate-50 to-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#0A192F]/10 rounded-sm flex items-center justify-center">
                  <Wallet className="w-6 h-6 text-[#0A192F]" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">NBFC Trade Financing</h3>
                  <p className="text-sm text-slate-500">
                    {financeRequests.length === 0
                      ? "Get working capital for your trade deals — request financing from NBFCs"
                      : `${financeRequests.length} financing request${financeRequests.length > 1 ? "s" : ""} · ${financeRequests.filter(r => r.financing_status === "nbfc_offer_received").length} offer${financeRequests.filter(r => r.financing_status === "nbfc_offer_received").length !== 1 ? "s" : ""} received`}
                  </p>
                </div>
              </div>
              <Button
                onClick={() => navigate("/exporter/financing")}
                className="bg-[#0A192F] hover:bg-[#1E293B] text-white flex items-center gap-2"
                data-testid="go-to-financing-btn"
              >
                {financeRequests.length === 0 ? "Request Financing" : "Manage Financing"}
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
            {financeRequests.filter(r => r.financing_status === "nbfc_offer_received").length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-200">
                <p className="text-xs text-emerald-700 font-medium">
                  You have pending NBFC offers waiting for your acceptance. Go to Trade Financing to review and accept.
                </p>
              </div>
            )}
          </div>

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
                <SelectTrigger className="w-56 bg-white" data-testid="sector-filter">
                  <SelectValue placeholder="All Sectors" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sectors</SelectItem>
                  {SECTORS.map((s) => (
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
              <p className="text-slate-500">No opportunities available</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="opportunities-grid">
              {filteredOpportunities.map((opp) => (
                <div key={opp.id} className="relative">
                  {interestedIds.has(opp.id) && (
                    <Badge className="absolute -top-2 -right-2 z-10 bg-emerald-500 text-white">
                      Interested
                    </Badge>
                  )}
                  <OpportunityCard opportunity={opp} />
                </div>
              ))}
            </div>
          )}

          {/* My Deals Section */}
          {myDeals.length > 0 && (
            <div className="mt-12">
              <h2 className="font-display text-xl font-semibold text-slate-900 mb-6">My Active Deals</h2>
              <div className="premium-card rounded-sm overflow-hidden">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Product</th>
                      <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Stage</th>
                      <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Updated</th>
                      <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {myDeals.map((deal) => (
                      <tr key={deal.id} className="border-b border-slate-100 last:border-0">
                        <td className="px-6 py-4 font-medium text-slate-900">{deal.opportunity_product}</td>
                        <td className="px-6 py-4">
                          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                            {deal.stage}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 text-slate-500 text-sm">
                          {new Date(deal.updated_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4">
                          <button
                            onClick={() => navigate(`/deals/${deal.id}/room`)}
                            className="flex items-center gap-1.5 text-xs text-[#0A192F] hover:text-[#C5A059] font-medium transition-colors"
                            data-testid={`deal-room-btn-${deal.id}`}
                          >
                            <MessageSquare className="w-3.5 h-3.5" />
                            Deal Room
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
