import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import ScoreGauge from "@/components/ScoreGauge";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import {
  ArrowLeft, MapPin, Package, Calendar, Shield, FileText,
  Users, Zap, CheckCircle, Building2, TrendingUp, AlertTriangle, MessageSquare
} from "lucide-react";

export default function OpportunityDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, authAxios } = useAuth();
  const isAdmin = user?.role === "admin";

  const [opportunity, setOpportunity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [matching, setMatching] = useState(false);
  const [interests, setInterests] = useState([]);
  const [indicativeTerms, setIndicativeTerms] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [hasExpressedInterest, setHasExpressedInterest] = useState(false);

  const fetchOpportunity = async () => {
    try {
      const res = await authAxios.get(`/opportunities/${id}`);
      setOpportunity(res.data);

      if (isAdmin) {
        const interestsRes = await authAxios.get("/interests");
        const oppInterests = interestsRes.data.filter((i) => i.opportunity_id === id);
        setInterests(oppInterests);
      } else {
        const myInterests = await authAxios.get("/my-interests");
        setHasExpressedInterest(myInterests.data.some((i) => i.opportunity_id === id));
      }
    } catch (e) {
      toast.error("Failed to load opportunity");
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunity();
  }, [id]);

  const handleMatch = async () => {
    setMatching(true);
    try {
      const res = await authAxios.post(`/opportunities/${id}/match`);
      toast.success(`Matched ${res.data.matched_exporters.length} exporters`);
      fetchOpportunity();
    } catch (e) {
      toast.error("Matchmaking failed");
    } finally {
      setMatching(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await authAxios.put(`/opportunities/${id}/status?status=${newStatus}`);
      setOpportunity({ ...opportunity, status: newStatus });
      toast.success("Status updated");
    } catch (e) {
      toast.error("Failed to update status");
    }
  };

  const handleExpressInterest = async () => {
    setSubmitting(true);
    try {
      await authAxios.post("/deals/express-interest", {
        opportunity_id: id,
        indicative_terms: indicativeTerms || null
      });
      toast.success("Interest expressed successfully!");
      setHasExpressedInterest(true);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to express interest");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateDeal = async (exporterId) => {
    try {
      const res = await authAxios.post("/deals", {
        opportunity_id: id,
        exporter_id: exporterId
      });
      toast.success("Deal created! Opening Deal Room...");
      if (res.data?.id) {
        setTimeout(() => navigate(`/deals/${res.data.id}/room`), 800);
      } else {
        navigate("/admin/pipeline");
      }
    } catch (e) {
      toast.error("Failed to create deal");
    }
  };

  if (loading) {
    return (
      <div className="app-container">
        <Sidebar />
        <main className="main-content bg-offwhite flex items-center justify-center">
          <p className="text-slate-500">Loading...</p>
        </main>
      </div>
    );
  }

  if (!opportunity) return null;

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => navigate(-1)}
                data-testid="back-btn"
                className="text-slate-600"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight">
                  {opportunity.product_name}
                </h1>
                <p className="text-slate-500">{opportunity.sector} • {opportunity.source_country}</p>
              </div>
            </div>
            {isAdmin && (
              <div className="flex items-center gap-3">
                <Select value={opportunity.status} onValueChange={handleStatusChange}>
                  <SelectTrigger className="w-36" data-testid="status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Draft">Draft</SelectItem>
                    <SelectItem value="Active">Active</SelectItem>
                    <SelectItem value="Matched">Matched</SelectItem>
                    <SelectItem value="Closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  onClick={handleMatch}
                  disabled={matching}
                  data-testid="match-btn"
                  className="bg-gold hover:bg-amber-600 text-white"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  {matching ? "Matching..." : "Run AI Match"}
                </Button>
              </div>
            )}
          </div>
        </header>

        <div className="p-8">
          <div className="grid grid-cols-12 gap-8">
            {/* Left Column - Demand Summary */}
            <div className="col-span-5">
              <div className="premium-card p-6 rounded-sm">
                <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-6">
                  Demand Summary
                </h2>

                <div className="space-y-5">
                  <div className="flex items-start gap-3">
                    <MapPin className="w-5 h-5 text-slate-400 mt-0.5" strokeWidth={1.5} />
                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-400 mb-1">Source Country</p>
                      <p className="text-lg font-medium text-slate-900">{opportunity.source_country}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Package className="w-5 h-5 text-slate-400 mt-0.5" strokeWidth={1.5} />
                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-400 mb-1">Quantity</p>
                      <p className="text-lg font-medium text-slate-900">{opportunity.quantity}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-slate-400 mt-0.5" strokeWidth={1.5} />
                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-400 mb-1">Delivery Timeline</p>
                      <p className="text-lg font-medium text-slate-900">{opportunity.delivery_timeline}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-slate-400 mt-0.5" strokeWidth={1.5} />
                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-400 mb-1">Engagement Mode</p>
                      <p className="text-lg font-medium text-slate-900">{opportunity.engagement_mode}</p>
                    </div>
                  </div>

                  {opportunity.hs_code && (
                    <div className="flex items-start gap-3">
                      <Shield className="w-5 h-5 text-slate-400 mt-0.5" strokeWidth={1.5} />
                      <div>
                        <p className="text-xs uppercase tracking-wider text-slate-400 mb-1">HS Code</p>
                        <p className="text-lg font-mono font-medium text-slate-900">{opportunity.hs_code}</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Compliance Requirements */}
                <div className="mt-8 pt-6 border-t border-slate-100">
                  <p className="text-xs uppercase tracking-wider text-slate-400 mb-3">Compliance Requirements</p>
                  <div className="flex flex-wrap gap-2">
                    {opportunity.compliance_requirements.map((cert) => (
                      <Badge key={cert} variant="outline" className="bg-slate-50 border-slate-200 text-slate-700">
                        {cert}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>

              {/* Express Interest - Exporter Only */}
              {!isAdmin && (
                <div className="premium-card p-6 rounded-sm mt-6">
                  <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">
                    Express Interest
                  </h2>
                  {hasExpressedInterest ? (
                    <div className="flex items-center gap-2 text-emerald-600">
                      <CheckCircle className="w-5 h-5" />
                      <span className="font-medium">Interest Submitted</span>
                    </div>
                  ) : (
                    <>
                      <Textarea
                        placeholder="Enter your indicative terms (optional)..."
                        value={indicativeTerms}
                        onChange={(e) => setIndicativeTerms(e.target.value)}
                        data-testid="indicative-terms-input"
                        className="mb-4"
                        rows={3}
                      />
                      <Button
                        onClick={handleExpressInterest}
                        disabled={submitting}
                        data-testid="express-interest-btn"
                        className="w-full bg-navy hover:bg-charcoal text-white"
                      >
                        {submitting ? "Submitting..." : "Express Interest"}
                      </Button>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Center Column - Scores */}
            <div className="col-span-3">
              <div className="premium-card p-6 rounded-sm">
                <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-6">
                  AI Analysis
                </h2>

                <div className="flex flex-col items-center gap-8">
                  <div className="relative">
                    <ScoreGauge 
                      value={opportunity.opportunity_score} 
                      label="Opportunity Score"
                      size={120}
                      color="#059669"
                    />
                  </div>

                  <div className="relative">
                    <ScoreGauge 
                      value={opportunity.risk_score} 
                      label="Risk Level"
                      size={120}
                      color={opportunity.risk_score > 0.5 ? "#DC2626" : "#D97706"}
                    />
                  </div>
                </div>

                <div className="mt-8 pt-6 border-t border-slate-100">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500">Feasibility</span>
                      <span className={`font-medium ${opportunity.opportunity_score >= 0.7 ? "text-emerald-600" : "text-amber-600"}`}>
                        {opportunity.opportunity_score >= 0.7 ? "High" : opportunity.opportunity_score >= 0.4 ? "Medium" : "Low"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500">Complexity</span>
                      <span className={`font-medium ${opportunity.risk_score <= 0.3 ? "text-emerald-600" : "text-amber-600"}`}>
                        {opportunity.risk_score <= 0.3 ? "Low" : opportunity.risk_score <= 0.5 ? "Medium" : "High"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Matched Exporters */}
            <div className="col-span-4">
              {isAdmin && (
                <>
                  <div className="premium-card p-6 rounded-sm mb-6">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium">
                        Matched Exporters
                      </h2>
                      <Badge variant="outline" className="bg-slate-50">
                        {opportunity.matched_exporters?.length || 0} matches
                      </Badge>
                    </div>

                    {opportunity.matched_exporters?.length > 0 ? (
                      <div className="space-y-4">
                        {opportunity.matched_exporters.map((exp, idx) => (
                          <div key={exp.exporter_id} className="p-4 bg-slate-50 rounded-sm border border-slate-100">
                            <div className="flex items-start justify-between">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-navy rounded-full flex items-center justify-center text-white font-medium text-sm">
                                  {idx + 1}
                                </div>
                                <div>
                                  <p className="font-medium text-slate-900">{exp.company_name}</p>
                                  <p className="text-sm text-slate-500">Match Score: {exp.match_score}%</p>
                                </div>
                              </div>
                              <Button
                                size="sm"
                                onClick={() => handleCreateDeal(exp.exporter_id)}
                                data-testid={`create-deal-${exp.exporter_id}`}
                                className="bg-navy hover:bg-charcoal text-white"
                              >
                                Create Deal
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <Users className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                        <p className="text-slate-500 text-sm">No matches yet</p>
                        <p className="text-slate-400 text-xs">Click "Run AI Match" to find exporters</p>
                      </div>
                    )}
                  </div>

                  {/* Expressed Interests */}
                  <div className="premium-card p-6 rounded-sm">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium">
                        Expressed Interests
                      </h2>
                      <Badge variant="outline" className="bg-slate-50">
                        {interests.length} interests
                      </Badge>
                    </div>

                    {interests.length > 0 ? (
                      <div className="space-y-3">
                        {interests.map((interest) => (
                          <div key={interest.id} className="p-3 bg-slate-50 rounded-sm border border-slate-100">
                            <div className="flex items-center gap-2">
                              <Building2 className="w-4 h-4 text-slate-400" />
                              <span className="font-medium text-slate-900">{interest.exporter_company}</span>
                            </div>
                            {interest.indicative_terms && (
                              <p className="mt-2 text-sm text-slate-600 italic">"{interest.indicative_terms}"</p>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-center text-slate-400 text-sm py-4">No interests yet</p>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
