import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import {
  PlusCircle, Package, MapPin, Calendar, RefreshCw,
  ClipboardList, CheckCircle, Clock
} from "lucide-react";

const STATUS_COLORS = {
  Active: "bg-emerald-100 text-emerald-700",
  Closed: "bg-slate-100 text-slate-600",
  Matched: "bg-blue-100 text-blue-700",
  Draft: "bg-amber-100 text-amber-700",
};

export default function BuyerDashboard() {
  const { authAxios, user } = useAuth();
  const navigate = useNavigate();
  const [rfqs, setRfqs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rfqRes, profileRes] = await Promise.allSettled([
        authAxios.get("/buyer/rfqs"),
        authAxios.get("/buyer/profile"),
      ]);
      if (rfqRes.status === "fulfilled") setRfqs(rfqRes.value.data);
      if (profileRes.status === "fulfilled") setProfile(profileRes.value.data);
    } catch {
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const stats = {
    total: rfqs.length,
    active: rfqs.filter(r => r.status === "Active").length,
    matched: rfqs.filter(r => r.matched_exporters?.length > 0).length,
    closed: rfqs.filter(r => r.status === "Closed").length,
  };

  return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-8 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-2xl font-semibold text-[#0A192F]">
                Buyer Dashboard
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">
                {user?.company_name} · Buyer Portal
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" size="sm" onClick={fetchData}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button
                size="sm"
                onClick={() => navigate("/buyer/post-rfq")}
                className="bg-[#0A192F] hover:bg-[#1E293B] text-white"
                data-testid="post-rfq-btn"
              >
                <PlusCircle className="w-4 h-4 mr-2" />
                Post Requirement
              </Button>
            </div>
          </div>
        </div>

        <div className="p-8">
          {/* Profile setup alert */}
          {!profile && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-sm flex items-center justify-between">
              <p className="text-sm text-amber-800">
                Complete your buyer profile to post requirements and get better matches.
              </p>
              <Button size="sm" variant="outline" onClick={() => navigate("/buyer/profile")}>
                Set Up Profile
              </Button>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            {[
              { label: "Total RFQs", value: stats.total, icon: ClipboardList, color: "text-[#0A192F]" },
              { label: "Active", value: stats.active, icon: Clock, color: "text-emerald-600" },
              { label: "Matched", value: stats.matched, icon: CheckCircle, color: "text-blue-600" },
              { label: "Closed", value: stats.closed, icon: Package, color: "text-slate-500" },
            ].map(stat => (
              <div key={stat.label} className="bg-white border border-slate-200 rounded-sm p-5">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs text-slate-500 uppercase tracking-wider">{stat.label}</p>
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                </div>
                <p className={`text-3xl font-display font-semibold ${stat.color}`}>{stat.value}</p>
              </div>
            ))}
          </div>

          {/* RFQ List */}
          <div className="bg-white border border-slate-200 rounded-sm">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="font-display font-semibold text-[#0A192F]">My Requirements (RFQs)</h2>
              <span className="text-xs text-slate-400">{rfqs.length} total</span>
            </div>

            {loading ? (
              <div className="p-12 text-center text-slate-400">Loading...</div>
            ) : rfqs.length === 0 ? (
              <div className="p-12 text-center">
                <ClipboardList className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500 font-medium">No requirements posted yet</p>
                <p className="text-sm text-slate-400 mt-1">Post your first requirement to find Indian exporters</p>
                <Button
                  className="mt-4 bg-[#0A192F] text-white"
                  onClick={() => navigate("/buyer/post-rfq")}
                >
                  Post First Requirement
                </Button>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {rfqs.map(rfq => (
                  <div
                    key={rfq.id}
                    className="px-6 py-4 flex items-center justify-between"
                    data-testid={`rfq-row-${rfq.id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-[#0A192F]/5 rounded-sm flex items-center justify-center flex-shrink-0">
                        <Package className="w-5 h-5 text-[#0A192F]" />
                      </div>
                      <div>
                        <p className="font-medium text-[#0A192F]">{rfq.product_name}</p>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-xs text-slate-400 flex items-center gap-1">
                            <MapPin className="w-3 h-3" />{rfq.delivery_country}
                          </span>
                          <span className="text-xs text-slate-400 flex items-center gap-1">
                            <Package className="w-3 h-3" />{rfq.quantity}
                          </span>
                          <span className="text-xs text-slate-400 flex items-center gap-1">
                            <Calendar className="w-3 h-3" />{rfq.delivery_timeline}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-xs text-slate-400">Matched exporters</p>
                        <p className="font-semibold text-[#0A192F]">{rfq.matched_exporters?.length || 0}</p>
                      </div>
                      <Badge className={`text-xs ${STATUS_COLORS[rfq.status] || "bg-slate-100"}`}>
                        {rfq.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
