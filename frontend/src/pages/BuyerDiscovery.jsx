import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  Search,
  Sparkles,
  Loader2,
  Globe,
  Building2,
  Mail,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  Trash2,
  Linkedin,
} from "lucide-react";

const STATUS_BADGE = {
  enriched: { label: "Enriched", cls: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  partial: { label: "Partial", cls: "bg-amber-50 text-amber-700 border-amber-200" },
  pending: { label: "Discovery only", cls: "bg-slate-50 text-slate-600 border-slate-200" },
  failed: { label: "Failed", cls: "bg-rose-50 text-rose-700 border-rose-200" },
};

export default function BuyerDiscovery() {
  const { authAxios } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [hsCode, setHsCode] = useState(searchParams.get("hs_code") || "");
  const [country, setCountry] = useState(searchParams.get("country") || "");
  const [productName, setProductName] = useState(searchParams.get("product") || "");

  const [discovering, setDiscovering] = useState(false);
  const [loading, setLoading] = useState(false);
  const [buyers, setBuyers] = useState([]);

  const fetchExisting = async (filters = {}) => {
    setLoading(true);
    try {
      const params = {};
      if (filters.hs_code) params.hs_code = filters.hs_code;
      if (filters.country) params.country = filters.country;
      const res = await authAxios.get("/buyers", { params });
      setBuyers(res.data);
    } catch (e) {
      toast.error("Failed to load buyers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const filters = {};
    if (searchParams.get("hs_code")) filters.hs_code = searchParams.get("hs_code");
    if (searchParams.get("country")) filters.country = searchParams.get("country");
    fetchExisting(filters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runDiscovery = async () => {
    if (!hsCode.trim()) {
      toast.error("HS Code is required");
      return;
    }
    setDiscovering(true);
    try {
      const res = await authAxios.post("/buyers/discover", {
        hs_code: hsCode.trim(),
        country: country.trim() || null,
        product_name: productName.trim() || null,
        max_results: 10,
      });
      const found = res.data || [];
      if (found.length === 0) {
        toast.warning("No buyers found for this query — try adding a product name or country");
      } else {
        toast.success(`Discovered ${found.length} buyers`);
      }
      setSearchParams({
        hs_code: hsCode.trim(),
        ...(country.trim() ? { country: country.trim() } : {}),
        ...(productName.trim() ? { product: productName.trim() } : {}),
      });
      // Refresh list filtered by the same HS code so admin sees full set incl. prior runs
      await fetchExisting({ hs_code: hsCode.trim(), country: country.trim() });
    } catch (e) {
      toast.error(e.response?.data?.detail || "Discovery failed");
    } finally {
      setDiscovering(false);
    }
  };

  const toggleVerified = async (buyer) => {
    try {
      const res = await authAxios.put(`/buyers/${buyer.id}/verify`, {
        verified: !buyer.verified,
      });
      setBuyers((prev) => prev.map((b) => (b.id === buyer.id ? res.data : b)));
    } catch (e) {
      toast.error("Failed to update");
    }
  };

  const deleteBuyer = async (buyer) => {
    if (!window.confirm(`Remove ${buyer.company_name}?`)) return;
    try {
      await authAxios.delete(`/buyers/${buyer.id}`);
      setBuyers((prev) => prev.filter((b) => b.id !== buyer.id));
      toast.success("Removed");
    } catch (e) {
      toast.error("Failed to delete");
    }
  };

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-3xl font-bold text-slate-900 tracking-tight">
                Buyer Discovery
              </h1>
              <p className="mt-1 text-slate-500">
                Search-grounded agent — finds real importers per HS code with source evidence
              </p>
            </div>
          </div>
        </header>

        <div className="p-8">
          {/* Search Card */}
          <div className="premium-card p-6 rounded-sm mb-6">
            <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">
              Discover Buyers
            </h2>
            <div className="grid grid-cols-12 gap-4 items-end">
              <div className="col-span-3">
                <Label className="text-xs uppercase tracking-wider text-slate-500">HS Code *</Label>
                <Input
                  value={hsCode}
                  onChange={(e) => setHsCode(e.target.value)}
                  placeholder="e.g., 1006.30"
                  data-testid="hs-code-input"
                  className="mt-1.5 font-mono"
                />
              </div>
              <div className="col-span-4">
                <Label className="text-xs uppercase tracking-wider text-slate-500">Product (optional)</Label>
                <Input
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="e.g., Premium Basmati Rice"
                  data-testid="product-input"
                  className="mt-1.5"
                />
              </div>
              <div className="col-span-3">
                <Label className="text-xs uppercase tracking-wider text-slate-500">Country (optional)</Label>
                <Input
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="e.g., Nigeria"
                  data-testid="country-input"
                  className="mt-1.5"
                />
              </div>
              <div className="col-span-2">
                <Button
                  onClick={runDiscovery}
                  disabled={discovering}
                  data-testid="discover-btn"
                  className="w-full bg-gold hover:bg-amber-600 text-white"
                >
                  {discovering ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Run Agent
                    </>
                  )}
                </Button>
              </div>
            </div>
            <p className="mt-4 text-xs text-slate-400">
              Pipeline: Tavily web search → GPT extraction → Apollo enrichment → Hunter email fallback.
              Apollo/Hunter steps skip silently if their API keys are not configured.
            </p>
          </div>

          {/* Results */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium">
              {buyers.length} {buyers.length === 1 ? "Buyer" : "Buyers"}
              {searchParams.get("hs_code") ? ` for HS ${searchParams.get("hs_code")}` : ""}
            </h2>
            {searchParams.get("hs_code") && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchParams({});
                  fetchExisting();
                }}
                className="border-slate-200"
              >
                Show all
              </Button>
            )}
          </div>

          {loading ? (
            <div className="text-center py-12 text-slate-500">Loading buyers...</div>
          ) : buyers.length === 0 ? (
            <div className="premium-card p-12 rounded-sm text-center">
              <Search className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No buyers yet</p>
              <p className="text-slate-400 text-sm mt-1">
                Enter an HS code above and click "Run Agent" to discover importers
              </p>
            </div>
          ) : (
            <div className="space-y-4" data-testid="buyers-list">
              {buyers.map((b) => {
                const status = STATUS_BADGE[b.enrichment_status] || STATUS_BADGE.pending;
                return (
                  <div key={b.id} className="premium-card p-6 rounded-sm">
                    <div className="flex items-start justify-between gap-6">
                      {/* Left: company core */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 flex-wrap">
                          <Building2 className="w-5 h-5 text-slate-400 flex-shrink-0" />
                          <h3 className="text-lg font-semibold text-slate-900 truncate">
                            {b.company_name}
                          </h3>
                          <Badge variant="outline" className={status.cls}>
                            {status.label}
                          </Badge>
                          {b.verified && (
                            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                              <ShieldCheck className="w-3 h-3 mr-1" /> Verified
                            </Badge>
                          )}
                          <Badge variant="outline" className="bg-slate-50 font-mono">
                            HS {b.hs_code}
                          </Badge>
                        </div>

                        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-xs uppercase tracking-wider text-slate-400">Country</p>
                            <p className="text-slate-900 font-medium">{b.country || "—"}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-slate-400">Industry</p>
                            <p className="text-slate-900 font-medium truncate">{b.industry || "—"}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-slate-400">Headcount</p>
                            <p className="text-slate-900 font-medium">{b.headcount || "—"}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-slate-400">HQ City</p>
                            <p className="text-slate-900 font-medium truncate">{b.hq_city || "—"}</p>
                          </div>
                        </div>

                        {b.domain && (
                          <a
                            href={`https://${b.domain.replace(/^https?:\/\//, "")}`}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-3 inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
                          >
                            <Globe className="w-3.5 h-3.5" /> {b.domain}
                          </a>
                        )}

                        {/* Evidence */}
                        {b.evidence_url && (
                          <div className="mt-4 p-3 bg-slate-50 rounded-sm border border-slate-100">
                            <div className="flex items-center gap-2 mb-1">
                              <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                              <a
                                href={b.evidence_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-xs text-blue-600 hover:underline truncate"
                              >
                                {b.evidence_url}
                              </a>
                            </div>
                            {b.evidence_snippet && (
                              <p className="text-sm text-slate-600 italic">"{b.evidence_snippet}"</p>
                            )}
                          </div>
                        )}

                        {/* Contacts */}
                        {b.contacts && b.contacts.length > 0 && (
                          <div className="mt-4">
                            <p className="text-xs uppercase tracking-wider text-slate-400 mb-2">
                              Procurement Contacts ({b.contacts.length})
                            </p>
                            <div className="space-y-2">
                              {b.contacts.map((c, i) => (
                                <div
                                  key={i}
                                  className="flex items-center justify-between gap-3 p-2 bg-white border border-slate-100 rounded-sm"
                                >
                                  <div className="flex items-center gap-3 min-w-0">
                                    <div className="w-7 h-7 bg-navy/5 rounded-full flex items-center justify-center text-navy text-xs font-medium flex-shrink-0">
                                      {(c.name || "?").slice(0, 1).toUpperCase()}
                                    </div>
                                    <div className="min-w-0">
                                      <p className="text-sm font-medium text-slate-900 truncate">
                                        {c.name || "Unknown"}
                                      </p>
                                      <p className="text-xs text-slate-500 truncate">
                                        {c.title || "—"}
                                      </p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2 flex-shrink-0">
                                    {c.email && (
                                      <a
                                        href={`mailto:${c.email}`}
                                        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
                                      >
                                        <Mail className="w-3 h-3" /> {c.email}
                                      </a>
                                    )}
                                    {c.linkedin_url && (
                                      <a
                                        href={c.linkedin_url}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-slate-400 hover:text-blue-600"
                                      >
                                        <Linkedin className="w-3.5 h-3.5" />
                                      </a>
                                    )}
                                    <Badge variant="outline" className="bg-slate-50 text-[10px] uppercase">
                                      {c.source}
                                    </Badge>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Right: actions */}
                      <div className="flex flex-col gap-2 flex-shrink-0">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleVerified(b)}
                          className="border-slate-200"
                        >
                          {b.verified ? (
                            <>
                              <ShieldAlert className="w-3.5 h-3.5 mr-1.5" /> Unverify
                            </>
                          ) : (
                            <>
                              <ShieldCheck className="w-3.5 h-3.5 mr-1.5" /> Verify
                            </>
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deleteBuyer(b)}
                          className="border-rose-200 text-rose-600 hover:bg-rose-50"
                        >
                          <Trash2 className="w-3.5 h-3.5 mr-1.5" /> Remove
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
