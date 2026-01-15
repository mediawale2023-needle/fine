import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { RefreshCw, Building2, Package, ChevronRight, ArrowRight } from "lucide-react";

const STAGES = ["Received", "Interest", "Shortlisted", "Introduction", "Negotiation", "Closed"];

const stageColors = {
  "Received": "bg-slate-100 border-slate-200",
  "Interest": "bg-blue-50 border-blue-200",
  "Shortlisted": "bg-purple-50 border-purple-200",
  "Introduction": "bg-amber-50 border-amber-200",
  "Negotiation": "bg-teal-50 border-teal-200",
  "Closed": "bg-emerald-50 border-emerald-200"
};

export default function PipelineView() {
  const { authAxios } = useAuth();
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDeals = async () => {
    setLoading(true);
    try {
      const res = await authAxios.get("/deals");
      setDeals(res.data);
    } catch (e) {
      toast.error("Failed to load deals");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeals();
  }, []);

  const handleStageChange = async (dealId, newStage) => {
    try {
      await authAxios.put(`/deals/${dealId}/stage?stage=${newStage}`);
      setDeals(deals.map((d) => d.id === dealId ? { ...d, stage: newStage } : d));
      toast.success("Stage updated");
    } catch (e) {
      toast.error("Failed to update stage");
    }
  };

  const getDealsByStage = (stage) => deals.filter((d) => d.stage === stage);

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-3xl font-bold text-slate-900 tracking-tight">
                Deal Pipeline
              </h1>
              <p className="mt-1 text-slate-500">Track and manage active trade deals</p>
            </div>
            <Button
              variant="outline"
              onClick={fetchDeals}
              data-testid="refresh-btn"
              className="border-slate-200"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </header>

        <div className="p-8">
          {/* Stage Headers */}
          <div className="flex items-center gap-2 mb-6">
            {STAGES.map((stage, idx) => (
              <div key={stage} className="flex items-center">
                <div className={`px-4 py-2 rounded-sm text-sm font-medium ${stageColors[stage]} border`}>
                  {stage}
                  <Badge variant="secondary" className="ml-2 bg-white/80">
                    {getDealsByStage(stage).length}
                  </Badge>
                </div>
                {idx < STAGES.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-slate-300 mx-1" />
                )}
              </div>
            ))}
          </div>

          {/* Pipeline Kanban */}
          {loading ? (
            <div className="text-center py-12 text-slate-500">Loading pipeline...</div>
          ) : deals.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No deals in pipeline</p>
              <p className="text-sm text-slate-400">Create deals from opportunity matches</p>
            </div>
          ) : (
            <div className="grid grid-cols-6 gap-4" data-testid="pipeline-kanban">
              {STAGES.map((stage) => (
                <div key={stage} className="pipeline-stage p-3">
                  <p className="text-xs uppercase tracking-wider text-slate-400 font-medium mb-3 px-1">
                    {stage}
                  </p>
                  <div className="space-y-3">
                    {getDealsByStage(stage).map((deal) => (
                      <div 
                        key={deal.id} 
                        className="pipeline-card"
                        data-testid={`deal-card-${deal.id}`}
                      >
                        <div className="flex items-start gap-2 mb-3">
                          <div className="w-8 h-8 bg-navy rounded-sm flex items-center justify-center flex-shrink-0">
                            <Building2 className="w-4 h-4 text-white" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-medium text-slate-900 text-sm truncate">
                              {deal.exporter_company}
                            </p>
                            <p className="text-xs text-slate-500 truncate">
                              {deal.opportunity_product}
                            </p>
                          </div>
                        </div>

                        {/* Move to next stage */}
                        {stage !== "Closed" && (
                          <Select
                            value={deal.stage}
                            onValueChange={(val) => handleStageChange(deal.id, val)}
                          >
                            <SelectTrigger 
                              className="h-8 text-xs bg-white"
                              data-testid={`stage-select-${deal.id}`}
                            >
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {STAGES.map((s) => (
                                <SelectItem key={s} value={s} className="text-xs">{s}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}

                        {stage === "Closed" && (
                          <Badge className="w-full justify-center bg-emerald-500 text-white">
                            Completed
                          </Badge>
                        )}

                        <p className="text-xs text-slate-400 mt-2">
                          Updated: {new Date(deal.updated_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Summary Stats */}
          {deals.length > 0 && (
            <div className="mt-8 premium-card p-6 rounded-sm">
              <h3 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">
                Pipeline Summary
              </h3>
              <div className="grid grid-cols-6 gap-4">
                {STAGES.map((stage) => {
                  const count = getDealsByStage(stage).length;
                  const percentage = deals.length > 0 ? Math.round((count / deals.length) * 100) : 0;
                  return (
                    <div key={stage} className="text-center">
                      <p className="text-2xl font-bold text-slate-900">{count}</p>
                      <p className="text-xs text-slate-500">{stage}</p>
                      <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-navy transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
