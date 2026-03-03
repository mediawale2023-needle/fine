import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Wallet, RefreshCw, Building2, AlertTriangle, Send, CheckCircle } from "lucide-react";

const FINANCING_STATUSES = [
  { value: "requested", label: "Requested" },
  { value: "under_review", label: "Under Review" },
  { value: "sent_to_nbfc", label: "Sent to NBFC" },
  { value: "nbfc_offer_received", label: "NBFC Offer Received" },
  { value: "accepted_by_exporter", label: "Accepted by Exporter" },
  { value: "rejected", label: "Rejected" }
];

export default function AdminFinanceRequests() {
  const { authAxios } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [showOfferModal, setShowOfferModal] = useState(false);
  const [offerData, setOfferData] = useState({
    nbfc_partner: "",
    offer_amount: "",
    interest_rate: "",
    admin_notes: ""
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const params = statusFilter !== "all" ? `?status=${statusFilter}` : "";
      const res = await authAxios.get(`/finance-requests${params}`);
      setRequests(res.data);
    } catch (e) {
      toast.error("Failed to load finance requests");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [statusFilter]);

  const handleStatusChange = async (requestId, newStatus) => {
    try {
      await authAxios.put(`/finance-requests/${requestId}/status?status=${newStatus}`);
      toast.success("Status updated");
      fetchRequests();
    } catch (e) {
      toast.error("Failed to update status");
    }
  };

  const handleRecordOffer = async () => {
    if (!offerData.nbfc_partner || !offerData.offer_amount || !offerData.interest_rate) {
      toast.error("Please fill all required fields");
      return;
    }

    setSubmitting(true);
    try {
      await authAxios.put(`/finance-requests/${selectedRequest.id}/nbfc-offer`, {
        nbfc_partner: offerData.nbfc_partner,
        offer_amount: parseFloat(offerData.offer_amount),
        interest_rate: parseFloat(offerData.interest_rate),
        admin_notes: offerData.admin_notes
      });
      toast.success("NBFC offer recorded");
      setShowOfferModal(false);
      setSelectedRequest(null);
      setOfferData({ nbfc_partner: "", offer_amount: "", interest_rate: "", admin_notes: "" });
      fetchRequests();
    } catch (e) {
      toast.error("Failed to record offer");
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      requested: "bg-blue-50 text-blue-700 border-blue-200",
      under_review: "bg-amber-50 text-amber-700 border-amber-200",
      sent_to_nbfc: "bg-purple-50 text-purple-700 border-purple-200",
      nbfc_offer_received: "bg-emerald-50 text-emerald-700 border-emerald-200",
      accepted_by_exporter: "bg-green-100 text-green-800 border-green-300",
      rejected: "bg-red-50 text-red-700 border-red-200"
    };
    return styles[status] || "bg-slate-50 text-slate-700";
  };

  const getRiskColor = (category) => {
    const colors = {
      Low: "text-emerald-600",
      Medium: "text-amber-600",
      High: "text-orange-600",
      "Very High": "text-red-600"
    };
    return colors[category] || "text-slate-600";
  };

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-3xl font-bold text-slate-900 tracking-tight">
                Finance Requests
              </h1>
              <p className="mt-1 text-slate-500">Manage exporter financing requests</p>
            </div>
            <Button variant="outline" onClick={fetchRequests} className="border-slate-200">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </header>

        <div className="p-8">
          {/* Stats Row */}
          <div className="grid grid-cols-5 gap-4 mb-6">
            {FINANCING_STATUSES.slice(0, 5).map((status) => {
              const count = requests.filter(r => r.financing_status === status.value).length;
              return (
                <div key={status.value} className="premium-card p-4 rounded-sm text-center">
                  <p className="text-2xl font-bold text-slate-900">{count}</p>
                  <p className="text-xs uppercase tracking-wider text-slate-500">{status.label}</p>
                </div>
              );
            })}
          </div>

          {/* Filter */}
          <div className="premium-card p-4 rounded-sm mb-6">
            <div className="flex items-center gap-4">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48 bg-white">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  {FINANCING_STATUSES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Requests Table */}
          {loading ? (
            <div className="text-center py-12 text-slate-500">Loading...</div>
          ) : requests.length === 0 ? (
            <div className="text-center py-12">
              <Wallet className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No finance requests found</p>
            </div>
          ) : (
            <div className="premium-card rounded-sm overflow-hidden">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Exporter</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Deal</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Loan Requested</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Risk Score</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Status</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">NBFC</th>
                    <th className="text-left px-6 py-4 text-xs uppercase tracking-wider text-slate-500 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map((req) => (
                    <tr key={req.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-slate-400" />
                          <span className="font-medium text-slate-900">{req.exporter_company}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-600">{req.opportunity_product}</td>
                      <td className="px-6 py-4">
                        <span className="font-medium text-slate-900">
                          ₹{req.financing_amount_requested?.toLocaleString()}
                        </span>
                        <span className="text-xs text-slate-400 block">
                          of ₹{req.purchase_order_value?.toLocaleString()}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {req.risk_score !== null && (
                          <div className="flex items-center gap-2">
                            <AlertTriangle className={`w-4 h-4 ${getRiskColor(req.risk_category)}`} />
                            <span className={`font-medium ${getRiskColor(req.risk_category)}`}>
                              {req.risk_score} ({req.risk_category})
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <Select
                          value={req.financing_status}
                          onValueChange={(v) => handleStatusChange(req.id, v)}
                        >
                          <SelectTrigger className="h-8 text-xs w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {FINANCING_STATUSES.map((s) => (
                              <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-6 py-4">
                        {req.nbfc_partner ? (
                          <div>
                            <span className="font-medium text-slate-900">{req.nbfc_partner}</span>
                            {req.nbfc_offer_amount && (
                              <span className="text-xs text-slate-500 block">
                                ₹{req.nbfc_offer_amount?.toLocaleString()} @ {req.nbfc_interest_rate}%
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {req.financing_status === "sent_to_nbfc" && !req.nbfc_partner && (
                          <Dialog open={showOfferModal && selectedRequest?.id === req.id} onOpenChange={(open) => {
                            setShowOfferModal(open);
                            if (open) setSelectedRequest(req);
                          }}>
                            <DialogTrigger asChild>
                              <Button size="sm" className="bg-gold hover:bg-amber-600 text-white">
                                <Send className="w-3 h-3 mr-1" />
                                Record Offer
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Record NBFC Offer</DialogTitle>
                              </DialogHeader>
                              <div className="space-y-4 mt-4">
                                <div>
                                  <Label className="text-xs uppercase tracking-wider text-slate-500">NBFC Partner *</Label>
                                  <Input
                                    value={offerData.nbfc_partner}
                                    onChange={(e) => setOfferData({ ...offerData, nbfc_partner: e.target.value })}
                                    className="mt-1.5"
                                    placeholder="e.g., HDFC Bank, ICICI"
                                  />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <Label className="text-xs uppercase tracking-wider text-slate-500">Offer Amount (₹) *</Label>
                                    <Input
                                      type="number"
                                      value={offerData.offer_amount}
                                      onChange={(e) => setOfferData({ ...offerData, offer_amount: e.target.value })}
                                      className="mt-1.5"
                                    />
                                  </div>
                                  <div>
                                    <Label className="text-xs uppercase tracking-wider text-slate-500">Interest Rate (% p.a.) *</Label>
                                    <Input
                                      type="number"
                                      step="0.1"
                                      value={offerData.interest_rate}
                                      onChange={(e) => setOfferData({ ...offerData, interest_rate: e.target.value })}
                                      className="mt-1.5"
                                    />
                                  </div>
                                </div>
                                <div>
                                  <Label className="text-xs uppercase tracking-wider text-slate-500">Notes</Label>
                                  <Textarea
                                    value={offerData.admin_notes}
                                    onChange={(e) => setOfferData({ ...offerData, admin_notes: e.target.value })}
                                    className="mt-1.5"
                                    rows={3}
                                  />
                                </div>
                                <Button
                                  onClick={handleRecordOffer}
                                  disabled={submitting}
                                  className="w-full bg-navy hover:bg-charcoal text-white"
                                >
                                  {submitting ? "Saving..." : "Record Offer"}
                                </Button>
                              </div>
                            </DialogContent>
                          </Dialog>
                        )}
                        {req.financing_status === "accepted_by_exporter" && (
                          <Badge className="bg-emerald-500 text-white">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Completed
                          </Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
