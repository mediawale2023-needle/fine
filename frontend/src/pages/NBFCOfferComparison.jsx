import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Building2, CheckCircle, TrendingDown,
  AlertTriangle, Send, RefreshCw
} from "lucide-react";

function OfferCard({ offer, isBest, onAccept, accepting }) {
  return (
    <div className={`bg-white border rounded-sm p-6 relative ${
      isBest ? "border-[#C5A059] shadow-md" : "border-slate-200"
    }`}>
      {isBest && (
        <div className="absolute -top-3 left-6">
          <Badge className="bg-[#C5A059] text-white text-xs px-3">Best Rate</Badge>
        </div>
      )}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-[#0A192F]/5 rounded-sm flex items-center justify-center">
            <Building2 className="w-5 h-5 text-[#0A192F]" />
          </div>
          <div>
            <p className="font-semibold text-[#0A192F]">{offer.nbfc_partner}</p>
            <p className="text-xs text-slate-400">
              {offer.received_at ? new Date(offer.received_at).toLocaleDateString() : "Today"}
            </p>
          </div>
        </div>
        <TrendingDown className={`w-5 h-5 ${isBest ? "text-emerald-500" : "text-slate-300"}`} />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-5">
        <div className="bg-slate-50 rounded-sm p-3">
          <p className="text-xs text-slate-500">Offer Amount</p>
          <p className="text-xl font-display font-semibold text-[#0A192F]">
            ₹{offer.offer_amount?.toLocaleString("en-IN")}
          </p>
        </div>
        <div className="bg-slate-50 rounded-sm p-3">
          <p className="text-xs text-slate-500">Interest Rate</p>
          <p className={`text-xl font-display font-semibold ${isBest ? "text-emerald-600" : "text-[#0A192F]"}`}>
            {offer.interest_rate}% p.a.
          </p>
        </div>
        <div className="bg-slate-50 rounded-sm p-3">
          <p className="text-xs text-slate-500">Tenure</p>
          <p className="text-lg font-semibold text-[#0A192F]">
            {offer.tenure_months || 6} months
          </p>
        </div>
        <div className="bg-slate-50 rounded-sm p-3">
          <p className="text-xs text-slate-500">Processing Fee</p>
          <p className="text-lg font-semibold text-[#0A192F]">
            ₹{offer.processing_fee?.toLocaleString("en-IN") || "—"}
          </p>
        </div>
      </div>

      {offer.notes && (
        <p className="text-xs text-slate-500 mb-4 italic">{offer.notes}</p>
      )}

      {onAccept && (
        <Button
          onClick={() => onAccept(offer)}
          disabled={accepting}
          className={`w-full ${
            isBest
              ? "bg-[#C5A059] hover:bg-amber-600 text-white"
              : "bg-[#0A192F] hover:bg-[#1E293B] text-white"
          }`}
        >
          <CheckCircle className="w-4 h-4 mr-2" />
          {accepting ? "Accepting..." : "Accept This Offer"}
        </Button>
      )}
    </div>
  );
}

export default function NBFCOfferComparison() {
  const { requestId } = useParams();
  const { authAxios, user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [accepting, setAccepting] = useState(false);

  const fetchOffers = async () => {
    setLoading(true);
    try {
      const res = await authAxios.get(`/finance-requests/${requestId}/offers`);
      setData(res.data);
    } catch {
      toast.error("Failed to load NBFC offers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOffers(); }, [requestId]);

  const handleSubmitToNBFCs = async () => {
    setSubmitting(true);
    try {
      const res = await authAxios.post(`/finance-requests/${requestId}/submit-to-nbfcs`);
      toast.success(res.data.message);
      fetchOffers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to submit to NBFCs");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAcceptOffer = async (offer) => {
    setAccepting(true);
    try {
      await authAxios.post(`/finance-requests/${requestId}/accept-offer`, {
        nbfc_partner: offer.nbfc_partner,
        offer_amount: offer.offer_amount,
        interest_rate: offer.interest_rate,
        admin_notes: `Accepted via offer comparison. Rate: ${offer.interest_rate}%`,
      });
      toast.success("Offer accepted! Financing in progress.");
      fetchOffers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to accept offer");
    } finally {
      setAccepting(false);
    }
  };

  const offers = data?.offers || [];
  const bestOffer = offers.length > 0
    ? offers.reduce((best, o) => (o.interest_rate < best.interest_rate ? o : best), offers[0])
    : null;

  const canSubmit = data?.status === "requested" || data?.status === "under_review";
  const hasOffers = offers.length > 0;
  const isExporter = user?.role === "exporter";

  return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="font-display text-2xl font-semibold text-[#0A192F]">
                  NBFC Offers
                </h1>
                <p className="text-sm text-slate-500 mt-0.5">
                  Finance Request · {requestId?.slice(0, 8)}...
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" size="sm" onClick={fetchOffers}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              {user?.role === "admin" && canSubmit && (
                <Button
                  onClick={handleSubmitToNBFCs}
                  disabled={submitting}
                  className="bg-[#0A192F] text-white"
                  data-testid="submit-to-nbfcs-btn"
                >
                  <Send className="w-4 h-4 mr-2" />
                  {submitting ? "Submitting..." : "Submit to All NBFCs"}
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="p-8">
          {loading ? (
            <div className="text-center py-20 text-slate-400">Loading offers...</div>
          ) : (
            <>
              {/* Status banner */}
              <div className={`mb-6 p-4 rounded-sm border flex items-center gap-3 ${
                hasOffers ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200"
              }`}>
                {hasOffers ? (
                  <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                )}
                <div>
                  <p className={`text-sm font-medium ${hasOffers ? "text-emerald-800" : "text-amber-800"}`}>
                    {hasOffers
                      ? `${offers.length} NBFC offer${offers.length > 1 ? "s" : ""} received`
                      : "No offers yet"}
                  </p>
                  <p className={`text-xs ${hasOffers ? "text-emerald-600" : "text-amber-600"}`}>
                    Status: <strong>{data?.status}</strong>
                    {canSubmit && !hasOffers && " · Admin can submit to NBFCs to get offers"}
                  </p>
                </div>
              </div>

              {/* Offers grid */}
              {hasOffers && (
                <div className="grid grid-cols-3 gap-6 mb-8">
                  {offers.map((offer, idx) => (
                    <OfferCard
                      key={idx}
                      offer={offer}
                      isBest={offer.nbfc_partner === bestOffer?.nbfc_partner && offer.interest_rate === bestOffer?.interest_rate}
                      onAccept={isExporter ? handleAcceptOffer : null}
                      accepting={accepting}
                    />
                  ))}
                </div>
              )}

              {/* Selected offer summary */}
              {data?.selected_offer?.nbfc_partner && (
                <div className="bg-white border border-slate-200 rounded-sm p-6">
                  <h3 className="font-display font-semibold text-[#0A192F] mb-4 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    Selected / Pre-selected Offer
                  </h3>
                  <div className="grid grid-cols-4 gap-4">
                    {[
                      { label: "NBFC Partner", value: data.selected_offer.nbfc_partner },
                      { label: "Amount", value: `₹${data.selected_offer.offer_amount?.toLocaleString("en-IN")}` },
                      { label: "Interest Rate", value: `${data.selected_offer.interest_rate}% p.a.` },
                      { label: "Tenure", value: `${data.selected_offer.tenure_months || 6} months` },
                    ].map(item => (
                      <div key={item.label} className="bg-slate-50 rounded-sm p-3">
                        <p className="text-xs text-slate-500">{item.label}</p>
                        <p className="font-semibold text-[#0A192F] mt-1">{item.value || "—"}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty state */}
              {!hasOffers && (
                <div className="text-center py-16 bg-white border border-slate-200 rounded-sm">
                  <Building2 className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 font-medium">Awaiting NBFC offers</p>
                  <p className="text-sm text-slate-400 mt-1">
                    {user?.role === "admin"
                      ? 'Click "Submit to All NBFCs" to fan out this request and receive offers within hours.'
                      : "Your financing request has been submitted. NBFC offers will appear here once received."}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
