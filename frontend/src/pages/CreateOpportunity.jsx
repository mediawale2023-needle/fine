import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { ArrowLeft, Sparkles, Loader2, FileText } from "lucide-react";
import { SECTORS, REGIONS, HS_CODES_BY_SECTOR, CERTIFICATIONS_BY_SECTOR } from "@/data/tradeData";

const ENGAGEMENT_MODES = ["Introduction-only", "Introduction + Negotiation Support"];

export default function CreateOpportunity() {
  const { authAxios } = useAuth();
  const navigate = useNavigate();
  
  const [mode, setMode] = useState("manual"); // "manual" or "ai"
  const [rawText, setRawText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    sector: "",
    source_country: "",
    region: "",
    product_name: "",
    hs_code: "",
    quantity: "",
    delivery_timeline: "",
    compliance_requirements: [],
    engagement_mode: "Introduction-only"
  });

  const handleAIParse = async () => {
    if (!rawText.trim()) {
      toast.error("Please enter the raw text to parse");
      return;
    }
    
    setParsing(true);
    try {
      const res = await authAxios.post("/opportunities/parse", { raw_text: rawText });
      setFormData({
        sector: res.data.sector || "",
        source_country: res.data.source_country || "",
        region: res.data.region || "",
        product_name: res.data.product_name || "",
        hs_code: res.data.hs_code || "",
        quantity: res.data.quantity || "",
        delivery_timeline: res.data.delivery_timeline || "",
        compliance_requirements: res.data.compliance_requirements || [],
        engagement_mode: "Introduction + Negotiation Support"
      });
      toast.success("AI parsed the document successfully!");
      setMode("manual");
    } catch (e) {
      toast.error("AI parsing failed. Please enter details manually.");
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.sector || !formData.source_country || !formData.product_name || !formData.quantity) {
      toast.error("Please fill in all required fields");
      return;
    }
    
    setSubmitting(true);
    try {
      await authAxios.post("/opportunities", formData);
      toast.success("Opportunity created successfully!");
      navigate("/admin");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to create opportunity");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleCertification = (cert) => {
    setFormData((prev) => ({
      ...prev,
      compliance_requirements: prev.compliance_requirements.includes(cert)
        ? prev.compliance_requirements.filter((c) => c !== cert)
        : [...prev.compliance_requirements, cert]
    }));
  };

  const availableCerts = formData.sector ? CERTIFICATIONS_BY_SECTOR[formData.sector] || [] : [];
  const availableHsCodes = formData.sector ? HS_CODES_BY_SECTOR[formData.sector] || [] : [];

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={() => navigate("/admin")}
              data-testid="back-btn"
              className="text-slate-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight">
                Create Trade Opportunity
              </h1>
              <p className="text-slate-500">Add a new demand from embassy or institutional brief</p>
            </div>
          </div>
        </header>

        <div className="p-8 max-w-4xl">
          {/* Mode Toggle */}
          <div className="premium-card p-4 rounded-sm mb-6">
            <div className="flex gap-4">
              <Button
                variant={mode === "ai" ? "default" : "outline"}
                onClick={() => setMode("ai")}
                data-testid="ai-mode-btn"
                className={mode === "ai" ? "bg-gold hover:bg-amber-600 text-white" : ""}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                AI Parse Document
              </Button>
              <Button
                variant={mode === "manual" ? "default" : "outline"}
                onClick={() => setMode("manual")}
                data-testid="manual-mode-btn"
                className={mode === "manual" ? "bg-navy hover:bg-charcoal text-white" : ""}
              >
                <FileText className="w-4 h-4 mr-2" />
                Manual Entry
              </Button>
            </div>
          </div>

          {/* AI Parse Section */}
          {mode === "ai" && (
            <div className="premium-card p-6 rounded-sm mb-6">
              <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">
                Paste Raw Text or Brief
              </h2>
              <Textarea
                placeholder="Paste the embassy brief, email content, or trade demand document here..."
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                data-testid="raw-text-input"
                className="min-h-[200px] mb-4"
              />
              <Button
                onClick={handleAIParse}
                disabled={parsing}
                data-testid="parse-btn"
                className="bg-gold hover:bg-amber-600 text-white"
              >
                {parsing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Parsing with AI...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Parse with AI
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Manual Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="premium-card p-6 rounded-sm">
              <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-6">
                Opportunity Details
              </h2>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">Sector *</Label>
                  <Select 
                    value={formData.sector} 
                    onValueChange={(v) => setFormData({ ...formData, sector: v, compliance_requirements: [] })}
                  >
                    <SelectTrigger className="mt-1.5" data-testid="sector-select">
                      <SelectValue placeholder="Select sector" />
                    </SelectTrigger>
                    <SelectContent>
                      {SECTORS.map((s) => (
                        <SelectItem key={s} value={s}>{s}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">Region *</Label>
                  <Select 
                    value={formData.region} 
                    onValueChange={(v) => setFormData({ ...formData, region: v })}
                  >
                    <SelectTrigger className="mt-1.5" data-testid="region-select">
                      <SelectValue placeholder="Select region" />
                    </SelectTrigger>
                    <SelectContent>
                      {REGIONS.map((r) => (
                        <SelectItem key={r} value={r}>{r}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">Source Country *</Label>
                  <Input
                    value={formData.source_country}
                    onChange={(e) => setFormData({ ...formData, source_country: e.target.value })}
                    data-testid="country-input"
                    className="mt-1.5"
                    placeholder="e.g., Nigeria, UAE, Germany"
                  />
                </div>

                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">Product Name *</Label>
                  <Input
                    value={formData.product_name}
                    onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                    data-testid="product-input"
                    className="mt-1.5"
                    placeholder="e.g., Premium Basmati Rice"
                  />
                </div>

                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">HS Code</Label>
                  {availableHsCodes.length > 0 ? (
                    <Select
                      value={formData.hs_code}
                      onValueChange={(v) => setFormData({ ...formData, hs_code: v })}
                    >
                      <SelectTrigger className="mt-1.5 font-mono" data-testid="hscode-input">
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
                      value={formData.hs_code}
                      onChange={(e) => setFormData({ ...formData, hs_code: e.target.value })}
                      data-testid="hscode-input"
                      className="mt-1.5 font-mono"
                      placeholder="Select a sector first"
                      disabled
                    />
                  )}
                </div>

                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">Quantity *</Label>
                  <Input
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    data-testid="quantity-input"
                    className="mt-1.5"
                    placeholder="e.g., 2000 MT"
                  />
                </div>

                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">Delivery Timeline *</Label>
                  <Input
                    value={formData.delivery_timeline}
                    onChange={(e) => setFormData({ ...formData, delivery_timeline: e.target.value })}
                    data-testid="timeline-input"
                    className="mt-1.5"
                    placeholder="e.g., Q1 2025"
                  />
                </div>

                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">Engagement Mode</Label>
                  <Select 
                    value={formData.engagement_mode} 
                    onValueChange={(v) => setFormData({ ...formData, engagement_mode: v })}
                  >
                    <SelectTrigger className="mt-1.5" data-testid="engagement-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ENGAGEMENT_MODES.map((m) => (
                        <SelectItem key={m} value={m}>{m}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Compliance Requirements */}
              {formData.sector && (
                <div className="mt-6 pt-6 border-t border-slate-100">
                  <Label className="text-xs uppercase tracking-wider text-slate-500 mb-3 block">
                    Compliance Requirements
                  </Label>
                  <div className="flex flex-wrap gap-3">
                    {availableCerts.map((cert) => (
                      <div key={cert} className="flex items-center gap-2">
                        <Checkbox
                          id={cert}
                          checked={formData.compliance_requirements.includes(cert)}
                          onCheckedChange={() => toggleCertification(cert)}
                          data-testid={`cert-${cert}`}
                        />
                        <label htmlFor={cert} className="text-sm text-slate-700 cursor-pointer">
                          {cert}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/admin")}
                className="border-slate-200"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                data-testid="submit-btn"
                className="bg-navy hover:bg-charcoal text-white"
              >
                {submitting ? "Creating..." : "Create Opportunity"}
              </Button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
