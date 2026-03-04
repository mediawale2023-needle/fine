import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  BarChart2, TrendingUp, Globe, Award, RefreshCw,
  Search, ChevronRight, Target, Layers
} from "lucide-react";

const SECTORS = [
  "Agriculture",
  "Marine / Frozen Foods",
  "Pharma",
  "Special Chemicals",
  "Value-Added Agri Products",
];

function StatCard({ title, value, subtitle, icon: Icon, color = "text-[#0A192F]" }) {
  return (
    <div className="bg-white border border-slate-200 rounded-sm p-5">
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs text-slate-500 uppercase tracking-wider">{title}</p>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <p className={`text-3xl font-display font-semibold ${color}`}>{value}</p>
      {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
    </div>
  );
}

function BarRow({ label, value, max, color = "bg-[#0A192F]" }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3 py-2">
      <span className="text-sm text-slate-600 w-40 flex-shrink-0 truncate">{label}</span>
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-medium text-slate-700 w-8 text-right">{value}</span>
    </div>
  );
}

export default function MarketIntelligence() {
  const { authAxios, user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [sectorInsight, setSectorInsight] = useState(null);
  const [marketInsight, setMarketInsight] = useState(null);
  const [benchmarks, setBenchmarks] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSector, setSelectedSector] = useState("");
  const [countrySearch, setCountrySearch] = useState("");
  const [loadingSector, setLoadingSector] = useState(false);
  const [loadingMarket, setLoadingMarket] = useState(false);

  useEffect(() => {
    const loadInitial = async () => {
      try {
        const promises = [authAxios.get("/insights/overview")];
        if (user?.role === "exporter") {
          promises.push(authAxios.get("/insights/exporter/benchmarks").catch(() => ({ data: null })));
        }
        const results = await Promise.allSettled(promises);
        if (results[0].status === "fulfilled") setOverview(results[0].value.data);
        if (results[1]?.status === "fulfilled") setBenchmarks(results[1].value.data);
      } catch {
        toast.error("Failed to load market intelligence");
      } finally {
        setLoading(false);
      }
    };
    loadInitial();
  }, []);

  const loadSectorInsight = async (sector) => {
    if (!sector) return;
    setLoadingSector(true);
    try {
      const res = await authAxios.get(`/insights/sector/${encodeURIComponent(sector)}`);
      setSectorInsight(res.data);
    } catch {
      toast.error("Failed to load sector data");
    } finally {
      setLoadingSector(false);
    }
  };

  const loadMarketInsight = async () => {
    if (!countrySearch.trim()) return;
    setLoadingMarket(true);
    try {
      const res = await authAxios.get(`/insights/market/${encodeURIComponent(countrySearch.trim())}`);
      setMarketInsight(res.data);
    } catch {
      toast.error("No data for that market");
    } finally {
      setLoadingMarket(false);
    }
  };

  const maxSector = overview ? Math.max(...overview.sector_breakdown.map(s => s.opportunities), 1) : 1;
  const maxRegion = overview ? Math.max(...overview.region_breakdown.map(r => r.opportunities), 1) : 1;

  return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-8 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-2xl font-semibold text-[#0A192F]">
                Market Intelligence
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">
                Real-time insights derived from TradeNexus deal flow
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        <div className="p-8 space-y-8">
          {loading ? (
            <div className="text-center py-20 text-slate-400">Loading intelligence data...</div>
          ) : (
            <>
              {/* Platform Overview KPIs */}
              {overview && (
                <div>
                  <h2 className="font-display font-semibold text-[#0A192F] mb-4">Platform Overview</h2>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    <StatCard title="Opportunities" value={overview.total_opportunities} icon={Layers} />
                    <StatCard title="Total Deals" value={overview.total_deals} icon={Target} />
                    <StatCard title="Closed Deals" value={overview.closed_deals} icon={Award} color="text-emerald-600" />
                    <StatCard title="Exporters" value={overview.total_exporters} icon={TrendingUp} />
                    <StatCard title="Buyers" value={overview.total_buyers} icon={Globe} />
                    {user?.role === "admin" && (
                      <StatCard
                        title="Revenue (₹)"
                        value={`₹${(overview.total_revenue_inr / 100000).toFixed(1)}L`}
                        icon={BarChart2}
                        color="text-[#C5A059]"
                      />
                    )}
                  </div>
                </div>
              )}

              {/* Sector & Region Breakdown */}
              {overview && (
                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-white border border-slate-200 rounded-sm p-6">
                    <h3 className="font-display font-semibold text-[#0A192F] mb-4 flex items-center gap-2">
                      <Layers className="w-4 h-4 text-[#C5A059]" />
                      Opportunities by Sector
                    </h3>
                    {overview.sector_breakdown.map(s => (
                      <BarRow key={s.sector} label={s.sector} value={s.opportunities} max={maxSector} />
                    ))}
                  </div>
                  <div className="bg-white border border-slate-200 rounded-sm p-6">
                    <h3 className="font-display font-semibold text-[#0A192F] mb-4 flex items-center gap-2">
                      <Globe className="w-4 h-4 text-[#C5A059]" />
                      Opportunities by Region
                    </h3>
                    {overview.region_breakdown.map(r => (
                      <BarRow
                        key={r.region}
                        label={r.region}
                        value={r.opportunities}
                        max={maxRegion}
                        color="bg-[#C5A059]"
                      />
                    ))}
                    {/* Monthly trend */}
                    {overview.monthly_trend?.length > 0 && (
                      <div className="mt-6 pt-4 border-t border-slate-100">
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Monthly Trend</p>
                        <div className="flex items-end gap-1 h-16">
                          {overview.monthly_trend.map(m => {
                            const maxVal = Math.max(...overview.monthly_trend.map(x => x.opportunities), 1);
                            const h = Math.max(4, Math.round((m.opportunities / maxVal) * 60));
                            return (
                              <div key={m.month} className="flex-1 flex flex-col items-center gap-1" title={`${m.month}: ${m.opportunities} opps`}>
                                <div className="w-full bg-[#0A192F]/10 rounded-sm" style={{ height: `${h}px` }}>
                                  <div className="w-full bg-[#0A192F] rounded-sm" style={{ height: `${h}px` }} />
                                </div>
                                <span className="text-[9px] text-slate-400">{m.month.split(" ")[0]}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Sector Deep Dive */}
              <div className="bg-white border border-slate-200 rounded-sm p-6">
                <h3 className="font-display font-semibold text-[#0A192F] mb-4 flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-[#C5A059]" />
                  Sector Deep Dive
                </h3>
                <div className="flex gap-3 mb-6">
                  <Select value={selectedSector} onValueChange={v => { setSelectedSector(v); loadSectorInsight(v); }}>
                    <SelectTrigger className="w-72">
                      <SelectValue placeholder="Select a sector to analyse" />
                    </SelectTrigger>
                    <SelectContent>
                      {SECTORS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>

                {loadingSector && <p className="text-slate-400 text-sm">Loading sector data...</p>}

                {sectorInsight && !loadingSector && (
                  <div className="grid grid-cols-4 gap-4">
                    <div className="bg-slate-50 rounded-sm p-4">
                      <p className="text-xs text-slate-500">Opportunities</p>
                      <p className="text-2xl font-display font-semibold text-[#0A192F] mt-1">
                        {sectorInsight.total_opportunities}
                      </p>
                      <p className="text-xs text-slate-400">{sectorInsight.active_opportunities} active</p>
                    </div>
                    <div className="bg-slate-50 rounded-sm p-4">
                      <p className="text-xs text-slate-500">Total Deals</p>
                      <p className="text-2xl font-display font-semibold text-[#0A192F] mt-1">
                        {sectorInsight.total_deals}
                      </p>
                    </div>
                    <div className="bg-slate-50 rounded-sm p-4">
                      <p className="text-xs text-slate-500">Win Rate</p>
                      <p className={`text-2xl font-display font-semibold mt-1 ${
                        sectorInsight.win_rate >= 0.5 ? "text-emerald-600" : "text-amber-600"
                      }`}>
                        {(sectorInsight.win_rate * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-slate-50 rounded-sm p-4">
                      <p className="text-xs text-slate-500">Avg Close Time</p>
                      <p className="text-2xl font-display font-semibold text-[#0A192F] mt-1">
                        {sectorInsight.avg_time_to_close_days}d
                      </p>
                    </div>

                    {sectorInsight.top_markets?.length > 0 && (
                      <div className="col-span-2 bg-slate-50 rounded-sm p-4">
                        <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider">Top Markets</p>
                        {sectorInsight.top_markets.map(m => (
                          <BarRow
                            key={m.country}
                            label={m.country}
                            value={m.opportunities}
                            max={sectorInsight.top_markets[0]?.opportunities || 1}
                          />
                        ))}
                      </div>
                    )}

                    {sectorInsight.compliance_frequency?.length > 0 && (
                      <div className="col-span-2 bg-slate-50 rounded-sm p-4">
                        <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider">Certification Demand</p>
                        <div className="flex flex-wrap gap-2">
                          {sectorInsight.compliance_frequency.slice(0, 8).map(c => (
                            <Badge key={c.cert} className="bg-[#0A192F]/10 text-[#0A192F] gap-1">
                              {c.cert}
                              <span className="text-[10px] text-slate-400">×{c.count}</span>
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Country Intelligence */}
              <div className="bg-white border border-slate-200 rounded-sm p-6">
                <h3 className="font-display font-semibold text-[#0A192F] mb-4 flex items-center gap-2">
                  <Globe className="w-4 h-4 text-[#C5A059]" />
                  Market / Country Intelligence
                </h3>
                <div className="flex gap-3 mb-6">
                  <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="Search country (e.g. UAE, Nigeria)"
                      className="pl-9"
                      value={countrySearch}
                      onChange={e => setCountrySearch(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && loadMarketInsight()}
                      data-testid="country-search"
                    />
                  </div>
                  <Button onClick={loadMarketInsight} disabled={loadingMarket || !countrySearch.trim()}>
                    {loadingMarket ? "Searching..." : "Search"}
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>

                {marketInsight && !loadingMarket && (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-slate-50 rounded-sm p-4">
                      <p className="text-xs text-slate-500">Market</p>
                      <p className="text-xl font-display font-semibold text-[#0A192F] mt-1">{marketInsight.country}</p>
                      <Badge className="mt-1 bg-blue-100 text-blue-700">{marketInsight.region}</Badge>
                    </div>
                    <div className="bg-slate-50 rounded-sm p-4">
                      <p className="text-xs text-slate-500">Total Opportunities</p>
                      <p className="text-2xl font-display font-semibold text-[#0A192F] mt-1">
                        {marketInsight.total_opportunities}
                      </p>
                    </div>
                    <div className="bg-slate-50 rounded-sm p-4">
                      <p className="text-xs text-slate-500">Typical Certifications</p>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {marketInsight.typical_compliance.map(c => (
                          <Badge key={c} className="text-[10px] bg-[#0A192F]/10 text-[#0A192F]">{c}</Badge>
                        ))}
                      </div>
                    </div>
                    {marketInsight.top_sectors?.length > 0 && (
                      <div className="col-span-3 bg-slate-50 rounded-sm p-4">
                        <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider">Top Sectors for {marketInsight.country}</p>
                        <div className="flex gap-4">
                          {marketInsight.top_sectors.slice(0, 4).map(s => (
                            <div key={s.sector} className="flex-1 text-center p-3 bg-white border border-slate-200 rounded-sm">
                              <p className="text-2xl font-display font-semibold text-[#0A192F]">{s.count}</p>
                              <p className="text-xs text-slate-500 mt-1">{s.sector}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Exporter Benchmarks (visible to exporters) */}
              {benchmarks && (
                <div className="bg-white border border-slate-200 rounded-sm p-6">
                  <h3 className="font-display font-semibold text-[#0A192F] mb-4 flex items-center gap-2">
                    <Target className="w-4 h-4 text-[#C5A059]" />
                    Your Performance vs Platform Benchmarks
                  </h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Your Stats</p>
                      <div className="space-y-3">
                        {[
                          { label: "Total Deals", value: benchmarks.my_stats.total_deals },
                          { label: "Closed Deals", value: benchmarks.my_stats.closed_deals },
                          { label: "Win Rate", value: `${(benchmarks.my_stats.win_rate * 100).toFixed(0)}%` },
                          { label: "Interests Expressed", value: benchmarks.my_stats.interests_expressed },
                          { label: "Reliability Score", value: benchmarks.my_stats.reliability_score?.toFixed(2) },
                        ].map(item => (
                          <div key={item.label} className="flex justify-between items-center py-1.5 border-b border-slate-50">
                            <span className="text-sm text-slate-600">{item.label}</span>
                            <span className="font-semibold text-[#0A192F]">{item.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Platform Benchmarks</p>
                      <div className="space-y-3">
                        {[
                          { label: "Avg Win Rate", value: `${(benchmarks.platform_benchmarks.avg_win_rate * 100).toFixed(0)}%` },
                          { label: "Avg Deals / Exporter", value: benchmarks.platform_benchmarks.avg_deals_per_exporter },
                          { label: "Top Certifications", value: benchmarks.platform_benchmarks.top_certifications.join(", ") },
                          { label: "Top Markets", value: benchmarks.platform_benchmarks.top_markets.join(", ") },
                        ].map(item => (
                          <div key={item.label} className="flex justify-between items-center py-1.5 border-b border-slate-50">
                            <span className="text-sm text-slate-600">{item.label}</span>
                            <span className="font-semibold text-slate-700 text-right max-w-[180px] text-sm">{item.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
