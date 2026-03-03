import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { DollarSign, RefreshCw, TrendingUp, CreditCard, Wallet, Percent } from "lucide-react";

export default function AdminRevenue() {
  const { authAxios } = useAuth();
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState("all");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [recordsRes, summaryRes] = await Promise.all([
        authAxios.get(typeFilter !== "all" ? `/revenue?revenue_type=${typeFilter}` : "/revenue"),
        authAxios.get("/revenue/summary")
      ]);
      setRecords(recordsRes.data);
      setSummary(summaryRes.data);
    } catch (e) {
      toast.error("Failed to load revenue data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [typeFilter]);

  const getTypeIcon = (type) => {
    switch (type) {
      case "subscription": return CreditCard;
      case "deal": return TrendingUp;
      case "financing": return Wallet;
      default: return DollarSign;
    }
  };

  const getTypeBadge = (type) => {
    const styles = {
      subscription: "bg-purple-50 text-purple-700 border-purple-200",
      deal: "bg-blue-50 text-blue-700 border-blue-200",
      financing: "bg-emerald-50 text-emerald-700 border-emerald-200"
    };
    return styles[type] || "bg-slate-50 text-slate-700";
  };

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-3xl font-bold text-slate-900 tracking-tight">
                Revenue Dashboard
              </h1>
              <p className="mt-1 text-slate-500">Track platform revenue across all streams</p>
            </div>
            <Button variant="outline" onClick={fetchData} className="border-slate-200">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </header>

        <div className="p-8">
          {/* Summary Cards */}
          {summary && (
            <div className="grid grid-cols-4 gap-6 mb-8">
              <div className="premium-card p-6 rounded-sm border-l-4 border-l-navy">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-navy/10 rounded-sm flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-navy" />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Total Revenue</p>
                    <p className="text-2xl font-bold text-slate-900">₹{summary.total_revenue?.toLocaleString()}</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-6 rounded-sm">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-purple-50 rounded-sm flex items-center justify-center">
                    <CreditCard className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Subscriptions</p>
                    <p className="text-2xl font-bold text-slate-900">₹{summary.subscription_revenue?.toLocaleString()}</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-6 rounded-sm">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-50 rounded-sm flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Deal Commission</p>
                    <p className="text-2xl font-bold text-slate-900">₹{summary.deal_commission_revenue?.toLocaleString()}</p>
                  </div>
                </div>
              </div>
              <div className="premium-card p-6 rounded-sm">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-emerald-50 rounded-sm flex items-center justify-center">
                    <Wallet className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Financing Commission</p>
                    <p className="text-2xl font-bold text-slate-900">₹{summary.financing_commission_revenue?.toLocaleString()}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Filter */}
          <div className="premium-card p-4 rounded-sm mb-6">
            <div className="flex items-center gap-4">
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-48 bg-white">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="subscription">Subscriptions</SelectItem>
                  <SelectItem value="deal">Deal Commissions</SelectItem>
                  <SelectItem value="financing">Financing Commissions</SelectItem>
                </SelectContent>
              </Select>
              <span className="text-sm text-slate-500">{records.length} records</span>
            </div>
          </div>

          {/* Revenue Records */}
          {loading ? (
            <div className="text-center py-12 text-slate-500">Loading...</div>
          ) : records.length === 0 ? (
            <div className="text-center py-12">
              <DollarSign className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No revenue records yet</p>
            </div>
          ) : (
            <div className="premium-card rounded-sm overflow-hidden">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Type</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Description</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Amount</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Status</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => {
                    const Icon = getTypeIcon(record.revenue_type);
                    return (
                      <tr key={record.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <Icon className="w-4 h-4 text-slate-400" />
                            <Badge variant="outline" className={getTypeBadge(record.revenue_type)}>
                              {record.revenue_type}
                            </Badge>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-slate-600 text-sm">{record.description}</td>
                        <td className="px-6 py-4">
                          <span className="font-bold text-slate-900">₹{record.amount?.toLocaleString()}</span>
                        </td>
                        <td className="px-6 py-4">
                          <Badge className={record.status === "completed" ? "bg-emerald-500" : "bg-amber-500"}>
                            {record.status}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 text-slate-500 text-sm">
                          {new Date(record.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Revenue Model Info */}
          <div className="mt-8 premium-card p-6 rounded-sm">
            <h3 className="font-display text-lg font-semibold text-slate-900 mb-4">Revenue Model</h3>
            <div className="grid grid-cols-3 gap-6">
              <div className="p-4 bg-purple-50 rounded-sm">
                <div className="flex items-center gap-2 mb-2">
                  <CreditCard className="w-5 h-5 text-purple-600" />
                  <span className="font-medium text-purple-900">SaaS Subscription</span>
                </div>
                <p className="text-sm text-purple-700">Annual subscription fees from exporters</p>
                <p className="text-xs text-purple-600 mt-2">Basic: ₹9,999 | Premium: ₹24,999 | Enterprise: ₹49,999</p>
              </div>
              <div className="p-4 bg-blue-50 rounded-sm">
                <div className="flex items-center gap-2 mb-2">
                  <Percent className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-blue-900">Deal Commission</span>
                </div>
                <p className="text-sm text-blue-700">1.5% commission on closed deal value</p>
                <p className="text-xs text-blue-600 mt-2">Charged when deal is successfully closed</p>
              </div>
              <div className="p-4 bg-emerald-50 rounded-sm">
                <div className="flex items-center gap-2 mb-2">
                  <Wallet className="w-5 h-5 text-emerald-600" />
                  <span className="font-medium text-emerald-900">Financing Commission</span>
                </div>
                <p className="text-sm text-emerald-700">3% commission on approved financing</p>
                <p className="text-xs text-emerald-600 mt-2">Charged when exporter accepts NBFC offer</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
