import { useState } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Send, X, Sparkles } from "lucide-react";
import { SECTORS, REGIONS, HS_CODES_BY_SECTOR, CERTIFICATIONS_BY_SECTOR } from "@/data/tradeData";

export default function BuyerPostRFQ() {
  const { authAxios } = useAuth();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    product_name: "",
    sector: "",
    quantity: "",
    delivery_country: "",
    region: "",
    delivery_timeline: "",
    hs_code: "",
    budget_range: "",
    notes: "",
    compliance_requirements: [],
  });

  const availableCerts = CERTIFICATIONS_BY_SECTOR[form.sector] || [];
  const availableHsCodes = HS_CODES_BY_SECTOR[form.sector] || [];

  const toggleCert = (cert) => {
    setForm(f => ({
      ...f,
      compliance_requirements: f.compliance_requirements.includes(cert)
        ? f.compliance_requirements.filter(c => c !== cert)
        : [...f.compliance_requirements, cert],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.product_name || !form.sector || !form.quantity || !form.delivery_country || !form.region || !form.delivery_timeline) {
      toast.error("Please fill in all required fields");
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        hs_code: form.hs_code || null,
        budget_range: form.budget_range || null,
        notes: form.notes || null,
      };
      await authAxios.post("/buyer/rfqs", payload);
      toast.success("Requirement posted! Matching exporters now...");
      navigate("/buyer");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to post requirement");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-8 py-5">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate("/buyer")}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="font-display text-2xl font-semibold text-[#0A192F]">
                Post a Requirement
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">
                Describe what you need — our AI will match you with Indian exporters
              </p>
            </div>
          </div>
        </div>

        <div className="p-8 max-w-3xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Product & Sector */}
            <div className="bg-white border border-slate-200 rounded-sm p-6">
              <h2 className="font-display font-semibold text-[#0A192F] mb-4">Product Details</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <Label htmlFor="product_name">Product Name *</Label>
                  <Input
                    id="product_name"
                    placeholder="e.g. Premium Basmati Rice, Frozen Tiger Shrimp"
                    value={form.product_name}
                    onChange={e => setForm(f => ({ ...f, product_name: e.target.value }))}
                    className="mt-1"
                    data-testid="rfq-product-name"
                  />
                </div>
                <div>
                  <Label>Sector *</Label>
                  <Select value={form.sector} onValueChange={v => setForm(f => ({ ...f, sector: v, compliance_requirements: [] }))}>
                    <SelectTrigger className="mt-1" data-testid="rfq-sector">
                      <SelectValue placeholder="Select sector" />
                    </SelectTrigger>
                    <SelectContent>
                      {SECTORS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>HS Code (optional)</Label>
                  {availableHsCodes.length > 0 ? (
                    <Select
                      value={form.hs_code}
                      onValueChange={v => setForm(f => ({ ...f, hs_code: v }))}
                    >
                      <SelectTrigger className="mt-1 font-mono">
                        <SelectValue placeholder="Select HS code" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableHsCodes.map((item) => (
                          <SelectItem key={item.code} value={item.code} className="font-mono">
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <Input
                      placeholder="Select a sector first"
                      className="mt-1 font-mono"
                      disabled
                    />
                  )}
                </div>
                <div>
                  <Label htmlFor="quantity">Quantity Required *</Label>
                  <Input
                    id="quantity"
                    placeholder="e.g. 500 MT, 10,000 units"
                    value={form.quantity}
                    onChange={e => setForm(f => ({ ...f, quantity: e.target.value }))}
                    className="mt-1"
                    data-testid="rfq-quantity"
                  />
                </div>
                <div>
                  <Label htmlFor="budget_range">Budget Range (optional)</Label>
                  <Input
                    id="budget_range"
                    placeholder="e.g. $50,000 – $80,000"
                    value={form.budget_range}
                    onChange={e => setForm(f => ({ ...f, budget_range: e.target.value }))}
                    className="mt-1"
                  />
                </div>
              </div>
            </div>

            {/* Delivery */}
            <div className="bg-white border border-slate-200 rounded-sm p-6">
              <h2 className="font-display font-semibold text-[#0A192F] mb-4">Delivery Details</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="delivery_country">Destination Country *</Label>
                  <Input
                    id="delivery_country"
                    placeholder="e.g. UAE, Nigeria, Germany"
                    value={form.delivery_country}
                    onChange={e => setForm(f => ({ ...f, delivery_country: e.target.value }))}
                    className="mt-1"
                    data-testid="rfq-country"
                  />
                </div>
                <div>
                  <Label>Region *</Label>
                  <Select value={form.region} onValueChange={v => setForm(f => ({ ...f, region: v }))}>
                    <SelectTrigger className="mt-1" data-testid="rfq-region">
                      <SelectValue placeholder="Select region" />
                    </SelectTrigger>
                    <SelectContent>
                      {REGIONS.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="col-span-2">
                  <Label htmlFor="delivery_timeline">Delivery Timeline *</Label>
                  <Input
                    id="delivery_timeline"
                    placeholder="e.g. Q2 2025, within 60 days, by March 2025"
                    value={form.delivery_timeline}
                    onChange={e => setForm(f => ({ ...f, delivery_timeline: e.target.value }))}
                    className="mt-1"
                    data-testid="rfq-timeline"
                  />
                </div>
              </div>
            </div>

            {/* Compliance */}
            {form.sector && (
              <div className="bg-white border border-slate-200 rounded-sm p-6">
                <h2 className="font-display font-semibold text-[#0A192F] mb-2">Compliance Requirements</h2>
                <p className="text-sm text-slate-500 mb-4">Select certifications the exporter must hold</p>
                <div className="flex flex-wrap gap-2">
                  {availableCerts.map(cert => (
                    <button
                      key={cert}
                      type="button"
                      onClick={() => toggleCert(cert)}
                      className={`px-3 py-1.5 rounded-sm border text-sm font-medium transition-colors ${
                        form.compliance_requirements.includes(cert)
                          ? "bg-[#0A192F] text-white border-[#0A192F]"
                          : "bg-white text-slate-600 border-slate-300 hover:border-[#0A192F]"
                      }`}
                    >
                      {cert}
                    </button>
                  ))}
                </div>
                {form.compliance_requirements.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {form.compliance_requirements.map(c => (
                      <Badge key={c} className="bg-[#0A192F]/10 text-[#0A192F] gap-1">
                        {c}
                        <X className="w-3 h-3 cursor-pointer" onClick={() => toggleCert(c)} />
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Notes */}
            <div className="bg-white border border-slate-200 rounded-sm p-6">
              <h2 className="font-display font-semibold text-[#0A192F] mb-4">Additional Notes</h2>
              <Textarea
                placeholder="Any specific requirements, quality standards, packaging preferences, or other details..."
                value={form.notes}
                onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                rows={4}
              />
            </div>

            <div className="flex items-center gap-4">
              <Button
                type="submit"
                disabled={submitting}
                className="bg-[#0A192F] hover:bg-[#1E293B] text-white px-8"
                data-testid="submit-rfq-btn"
              >
                {submitting ? (
                  <>
                    <Sparkles className="w-4 h-4 mr-2 animate-pulse" />
                    Matching Exporters...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Post Requirement
                  </>
                )}
              </Button>
              <Button type="button" variant="outline" onClick={() => navigate("/buyer")}>
                Cancel
              </Button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
