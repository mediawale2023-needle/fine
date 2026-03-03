import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Wallet, Plus, RefreshCw, TrendingUp, AlertTriangle, CheckCircle, Clock, Building2 } from "lucide-react";

const PAYMENT_METHODS = [
  { value: "LC", label: "Letter of Credit (LC)" },
  { value: "advance", label: "Advance Payment" },
  { value: "open_account", label: "Open Account" }
];

export default function ExporterFinancing() {
  const { authAxios, user } = useAuth();
  const [financeRequests, setFinanceRequests] = useState([]);
  const [myDeals, setMyDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    purchase_order_value: "",
    financing_amount_requested: "",
    production_time_days: "",
    shipment_date: "",
    buyer_country: "",
    payment_method: "LC",
    exporter_bank_details: "",
    past_export_turnover: ""
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [financeRes, dealsRes] = await Promise.all([
        authAxios.get("/finance-requests"),
        authAxios.get("/deals")
      ]);
      setFinanceRequests(financeRes.data);
      setMyDeals(dealsRes.data.filter(d => d.stage !== "Closed"));
    } catch (e) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRequestFinancing = async () => {
    if (!selectedDeal || !formData.purchase_order_value || !formData.financing_amount_requested) {
      toast.error("Please fill all required fields");
      return;
    }

    setSubmitting(true);
    try {
      await authAxios.post("/finance-requests", {
        deal_id: selectedDeal.id,
        purchase_order_value: parseFloat(formData.purchase_order_value),
        financing_amount_requested: parseFloat(formData.financing_amount_requested),
        production_time_days: parseInt(formData.production_time_days) || 30,
        shipment_date: formData.shipment_date,
        buyer_country: formData.buyer_country,
        payment_method: formData.payment_method,
        exporter_bank_details: formData.exporter_bank_details,
        past_export_turnover: parseFloat(formData.past_export_turnover) || 10000000
      });
      toast.success("Financing request submitted!");
      setShowRequestModal(false);
      setSelectedDeal(null);
      setFormData({
        purchase_order_value: "",
        financing_amount_requested: "",
        production_time_days: "",
        shipment_date: "",
        buyer_country: "",
        payment_method: "LC",
        exporter_bank_details: "",
        past_export_turnover: ""
      });
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to submit request");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAcceptOffer = async (requestId) => {
    try {
      const res = await authAxios.post(`/finance-requests/${requestId}/accept`);
      toast.success(`Offer accepted! Commission: ₹${res.data.financing_commission.toLocaleString()}`);
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to accept offer");
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

  const getRiskBadge = (category) => {
    const styles = {
      Low: "bg-emerald-100 text-emerald-800",
      Medium: "bg-amber-100 text-amber-800",
      High: "bg-orange-100 text-orange-800",
      "Very High": "bg-red-100 text-red-800"
    };
    return styles[category] || "bg-slate-100 text-slate-800";
  };

  // Get deals that don't have financing requests
  const availableDeals = myDeals.filter(d => !financeRequests.some(fr => fr.deal_id === d.id));

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-3xl font-bold text-slate-900 tracking-tight">
                Trade Financing
              </h1>
              <p className="mt-1 text-slate-500">Request financing for your trade deals</p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={fetchData} className="border-slate-200">
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Dialog open={showRequestModal} onOpenChange={setShowRequestModal}>
                <DialogTrigger asChild>
                  <Button className="bg-navy hover:bg-charcoal text-white" disabled={availableDeals.length === 0}>
                    <Plus className="w-4 h-4 mr-2" />
                    Request Financing
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle className="font-display text-xl">Request Trade Financing</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div>
                      <Label className="text-xs uppercase tracking-wider text-slate-500">Select Deal *</Label>
                      <Select value={selectedDeal?.id || ""} onValueChange={(v) => setSelectedDeal(myDeals.find(d => d.id === v))}>
                        <SelectTrigger className="mt-1.5">
                          <SelectValue placeholder="Select a deal" />
                        </SelectTrigger>
                        <SelectContent>
                          {availableDeals.map((d) => (
                            <SelectItem key={d.id} value={d.id}>
                              {d.opportunity_product} ({d.stage})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs uppercase tracking-wider text-slate-500">Purchase Order Value (₹) *</Label>
                        <Input
                          type="number"
                          value={formData.purchase_order_value}
                          onChange={(e) => setFormData({ ...formData, purchase_order_value: e.target.value })}
                          className="mt-1.5"
                          placeholder="e.g., 5000000"
                        />
                      </div>
                      <div>
                        <Label className="text-xs uppercase tracking-wider text-slate-500">Financing Amount (₹) *</Label>
                        <Input
                          type="number"
                          value={formData.financing_amount_requested}
                          onChange={(e) => setFormData({ ...formData, financing_amount_requested: e.target.value })}
                          className="mt-1.5"
                          placeholder="e.g., 3500000"
                        />
                      </div>
                      <div>
                        <Label className="text-xs uppercase tracking-wider text-slate-500">Production Time (days)</Label>
                        <Input
                          type="number"
                          value={formData.production_time_days}
                          onChange={(e) => setFormData({ ...formData, production_time_days: e.target.value })}
                          className="mt-1.5"
                          placeholder="e.g., 45"
                        />
                      </div>
                      <div>
                        <Label className="text-xs uppercase tracking-wider text-slate-500">Shipment Date</Label>
                        <Input
                          type="date"
                          value={formData.shipment_date}
                          onChange={(e) => setFormData({ ...formData, shipment_date: e.target.value })}
                          className="mt-1.5"
                        />
                      </div>
                      <div>
                        <Label className="text-xs uppercase tracking-wider text-slate-500">Buyer Country</Label>
                        <Input
                          value={formData.buyer_country}
                          onChange={(e) => setFormData({ ...formData, buyer_country: e.target.value })}
                          className="mt-1.5"
                          placeholder="e.g., Nigeria"
                        />
                      </div>
                      <div>
                        <Label className="text-xs uppercase tracking-wider text-slate-500">Payment Method</Label>
                        <Select value={formData.payment_method} onValueChange={(v) => setFormData({ ...formData, payment_method: v })}>
                          <SelectTrigger className="mt-1.5">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {PAYMENT_METHODS.map((m) => (
                              <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="col-span-2">
                        <Label className="text-xs uppercase tracking-wider text-slate-500">Bank Details</Label>
                        <Input
                          value={formData.exporter_bank_details}
                          onChange={(e) => setFormData({ ...formData, exporter_bank_details: e.target.value })}
                          className="mt-1.5"
                          placeholder="Bank Name, Account Number, IFSC"
                        />
                      </div>
                      <div className="col-span-2">
                        <Label className="text-xs uppercase tracking-wider text-slate-500">Past Export Turnover (₹)</Label>
                        <Input
                          type="number"
                          value={formData.past_export_turnover}
                          onChange={(e) => setFormData({ ...formData, past_export_turnover: e.target.value })}
                          className="mt-1.5"
                          placeholder="e.g., 50000000"
                        />
                      </div>
                    </div>

                    <Button
                      onClick={handleRequestFinancing}
                      disabled={submitting}
                      className="w-full bg-navy hover:bg-charcoal text-white mt-4"
                    >
                      {submitting ? "Submitting..." : "Submit Financing Request"}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </header>

        <div className="p-8">
          {/* Stats */}
          <div className="grid grid-cols-4 gap-6 mb-8">
            <div className="premium-card p-6 rounded-sm">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-50 rounded-sm flex items-center justify-center">
                  <Wallet className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{financeRequests.length}</p>
                  <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Total Requests</p>
                </div>
              </div>
            </div>
            <div className="premium-card p-6 rounded-sm">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-amber-50 rounded-sm flex items-center justify-center">
                  <Clock className="w-6 h-6 text-amber-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">
                    {financeRequests.filter(r => ["requested", "under_review", "sent_to_nbfc"].includes(r.financing_status)).length}
                  </p>
                  <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Pending</p>
                </div>
              </div>
            </div>
            <div className="premium-card p-6 rounded-sm">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-emerald-50 rounded-sm flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">
                    {financeRequests.filter(r => r.financing_status === "nbfc_offer_received").length}
                  </p>
                  <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Offers Received</p>
                </div>
              </div>
            </div>
            <div className="premium-card p-6 rounded-sm">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-green-50 rounded-sm flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">
                    {financeRequests.filter(r => r.financing_status === "accepted_by_exporter").length}
                  </p>
                  <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Accepted</p>
                </div>
              </div>
            </div>
          </div>

          {/* Finance Requests List */}
          {loading ? (
            <div className="text-center py-12 text-slate-500">Loading...</div>
          ) : financeRequests.length === 0 ? (
            <div className="text-center py-12">
              <Wallet className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No financing requests yet</p>
              <p className="text-sm text-slate-400">Click "Request Financing" to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {financeRequests.map((req) => (
                <div key={req.id} className="premium-card p-6 rounded-sm">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="font-display text-lg font-semibold text-slate-900">
                          {req.opportunity_product}
                        </h3>
                        <Badge variant="outline" className={getStatusBadge(req.financing_status)}>
                          {req.financing_status.replace(/_/g, " ")}
                        </Badge>
                        {req.risk_category && (
                          <Badge className={getRiskBadge(req.risk_category)}>
                            Risk: {req.risk_category} ({req.risk_score})
                          </Badge>
                        )}
                      </div>

                      <div className="grid grid-cols-4 gap-6 text-sm">
                        <div>
                          <p className="text-slate-400 text-xs uppercase">Order Value</p>
                          <p className="font-medium text-slate-900">₹{req.purchase_order_value?.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs uppercase">Requested</p>
                          <p className="font-medium text-slate-900">₹{req.financing_amount_requested?.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs uppercase">Buyer Country</p>
                          <p className="font-medium text-slate-900">{req.buyer_country}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs uppercase">Payment Method</p>
                          <p className="font-medium text-slate-900">{req.payment_method}</p>
                        </div>
                      </div>

                      {/* NBFC Offer Details */}
                      {req.financing_status === "nbfc_offer_received" && req.nbfc_offer_amount && (
                        <div className="mt-4 p-4 bg-emerald-50 border border-emerald-200 rounded-sm">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-xs uppercase text-emerald-600 font-medium">NBFC Offer from {req.nbfc_partner}</p>
                              <p className="text-lg font-bold text-emerald-800">
                                ₹{req.nbfc_offer_amount?.toLocaleString()} @ {req.nbfc_interest_rate}% p.a.
                              </p>
                            </div>
                            <Button
                              onClick={() => handleAcceptOffer(req.id)}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white"
                            >
                              Accept Offer
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
