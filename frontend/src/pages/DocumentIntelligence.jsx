import { useState, useRef } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import {
  Upload, FileText, Sparkles, CheckCircle, X,
  ChevronDown, ChevronUp, Package, Globe, DollarSign, Calendar
} from "lucide-react";

const DOC_TYPES = ["LC", "Invoice", "Bill of Lading", "Certificate of Origin", "Other"];

function ResultField({ label, value }) {
  if (!value) return null;
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
      <span className="text-sm text-slate-700 font-medium">{
        Array.isArray(value) ? value.join(", ") : String(value)
      }</span>
    </div>
  );
}

export default function DocumentIntelligence() {
  const { authAxios } = useAuth();
  const fileRef = useRef(null);

  const [mode, setMode] = useState("paste"); // "paste" | "upload"
  const [rawText, setRawText] = useState("");
  const [docHint, setDocHint] = useState("");
  const [file, setFile] = useState(null);
  const [parsing, setParsing] = useState(false);
  const [result, setResult] = useState(null);
  const [showRaw, setShowRaw] = useState(false);
  const [history, setHistory] = useState([]);

  const handleParse = async () => {
    if (mode === "paste" && !rawText.trim()) {
      toast.error("Paste your document content first");
      return;
    }
    if (mode === "upload" && !file) {
      toast.error("Select a file to upload");
      return;
    }

    setParsing(true);
    setResult(null);
    try {
      let res;
      if (mode === "paste") {
        const form = new FormData();
        form.append("content", rawText);
        form.append("doc_hint", docHint);
        res = await authAxios.post("/documents/parse", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      } else {
        const form = new FormData();
        form.append("file", file);
        res = await authAxios.post("/documents/upload", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }
      const parsed = res.data.parsed || res.data;
      setResult(parsed);
      setHistory(h => [{ ...parsed, _id: Date.now(), filename: file?.name || "pasted" }, ...h.slice(0, 4)]);
      toast.success("Document parsed successfully");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Parsing failed");
    } finally {
      setParsing(false);
    }
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer?.files?.[0];
    if (dropped) setFile(dropped);
  };

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) setFile(selected);
  };

  return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-8 py-5">
          <h1 className="font-display text-2xl font-semibold text-[#0A192F]">
            Document Intelligence
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            AI-powered extraction from LCs, Invoices, Bills of Lading, and more
          </p>
        </div>

        <div className="p-8 grid grid-cols-2 gap-8">
          {/* Left: Input */}
          <div className="space-y-6">
            {/* Mode toggle */}
            <div className="bg-white border border-slate-200 rounded-sm p-1 inline-flex">
              {["paste", "upload"].map(m => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-5 py-2 rounded-sm text-sm font-medium transition-colors capitalize ${
                    mode === m
                      ? "bg-[#0A192F] text-white"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  {m === "paste" ? "Paste Text" : "Upload File"}
                </button>
              ))}
            </div>

            {/* Doc type hint */}
            <div className="bg-white border border-slate-200 rounded-sm p-5">
              <Label className="mb-2 block">Document Type Hint (optional)</Label>
              <Select value={docHint} onValueChange={setDocHint}>
                <SelectTrigger>
                  <SelectValue placeholder="Let AI detect automatically" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Auto-detect</SelectItem>
                  {DOC_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-400 mt-2">
                Providing a hint improves extraction accuracy
              </p>
            </div>

            {mode === "paste" ? (
              <div className="bg-white border border-slate-200 rounded-sm p-5">
                <Label className="mb-2 block">Document Content</Label>
                <Textarea
                  placeholder={`Paste the full text of your LC, Invoice, or Bill of Lading here...\n\nExample:\nLETTER OF CREDIT\nNo: LC/2025/00123\nAmount: USD 250,000\nProduct: Premium Basmati Rice, HS 1006.30\nQuantity: 500 MT\nBeneficiary: AgriMax Exports Pvt Ltd, India\nApplicant: Al Baraka Trading LLC, UAE\n...`}
                  value={rawText}
                  onChange={e => setRawText(e.target.value)}
                  rows={14}
                  className="font-mono text-xs"
                  data-testid="doc-paste-input"
                />
              </div>
            ) : (
              <div
                className="bg-white border-2 border-dashed border-slate-300 rounded-sm p-10 text-center cursor-pointer hover:border-[#0A192F] transition-colors"
                onClick={() => fileRef.current?.click()}
                onDragOver={e => e.preventDefault()}
                onDrop={handleFileDrop}
                data-testid="file-drop-zone"
              >
                <input
                  ref={fileRef}
                  type="file"
                  className="hidden"
                  accept=".txt,.pdf,.doc,.docx"
                  onChange={handleFileChange}
                />
                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <FileText className="w-8 h-8 text-[#0A192F]" />
                    <div className="text-left">
                      <p className="font-medium text-[#0A192F]">{file.name}</p>
                      <p className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <button
                      onClick={e => { e.stopPropagation(); setFile(null); }}
                      className="ml-2 text-slate-400 hover:text-slate-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                    <p className="text-slate-500 font-medium">Drop file here or click to browse</p>
                    <p className="text-xs text-slate-400 mt-1">Supports TXT, PDF (max 5MB)</p>
                  </>
                )}
              </div>
            )}

            <Button
              onClick={handleParse}
              disabled={parsing}
              className="w-full bg-[#0A192F] hover:bg-[#1E293B] text-white h-11"
              data-testid="parse-document-btn"
            >
              {parsing ? (
                <>
                  <Sparkles className="w-4 h-4 mr-2 animate-pulse" />
                  Analysing Document...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Extract Data with AI
                </>
              )}
            </Button>
          </div>

          {/* Right: Result + History */}
          <div className="space-y-6">
            {result ? (
              <div className="bg-white border border-slate-200 rounded-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    <h3 className="font-display font-semibold text-[#0A192F]">Extracted Data</h3>
                  </div>
                  <Badge className="bg-[#0A192F]/10 text-[#0A192F]">{result.doc_type}</Badge>
                </div>

                <div className="p-5 grid grid-cols-2 gap-4">
                  <ResultField label="Product" value={result.product_name} />
                  <ResultField label="HS Code" value={result.hs_code} />
                  <ResultField label="Quantity" value={result.quantity} />
                  <ResultField label="Value" value={result.value_usd ? `${result.currency || "USD"} ${result.value_usd?.toLocaleString()}` : null} />
                  <ResultField label="Buyer" value={result.buyer_name} />
                  <ResultField label="Seller / Exporter" value={result.seller_name} />
                  <ResultField label="Origin" value={result.origin_country} />
                  <ResultField label="Destination" value={result.destination_country} />
                  <ResultField label="Delivery Date" value={result.delivery_date} />
                  <ResultField label="Payment Terms" value={result.payment_terms} />
                  <div className="col-span-2">
                    <ResultField label="Compliance Required" value={result.compliance_requirements} />
                  </div>
                  {result.key_notes && (
                    <div className="col-span-2 bg-amber-50 border border-amber-200 rounded-sm p-3">
                      <p className="text-xs text-amber-700 font-medium mb-1">Notes</p>
                      <p className="text-sm text-amber-800">{result.key_notes}</p>
                    </div>
                  )}
                </div>

                {/* Raw JSON toggle */}
                <div className="border-t border-slate-100">
                  <button
                    onClick={() => setShowRaw(s => !s)}
                    className="w-full px-5 py-3 flex items-center justify-between text-xs text-slate-400 hover:text-slate-600"
                  >
                    <span>View raw JSON</span>
                    {showRaw ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                  {showRaw && (
                    <pre className="px-5 pb-5 text-xs text-slate-600 bg-slate-50 overflow-auto max-h-60">
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white border border-dashed border-slate-300 rounded-sm p-12 text-center">
                <FileText className="w-10 h-10 text-slate-200 mx-auto mb-3" />
                <p className="text-slate-400 font-medium">Extracted data will appear here</p>
                <p className="text-sm text-slate-300 mt-1">
                  Paste or upload a trade document and click Extract
                </p>
              </div>
            )}

            {/* Recent parses */}
            {history.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-sm">
                <div className="px-5 py-3 border-b border-slate-100">
                  <h4 className="text-sm font-semibold text-[#0A192F]">Recent Parses (this session)</h4>
                </div>
                <div className="divide-y divide-slate-50">
                  {history.map(h => (
                    <div
                      key={h._id}
                      className="px-5 py-3 flex items-center justify-between hover:bg-slate-50 cursor-pointer"
                      onClick={() => setResult(h)}
                    >
                      <div className="flex items-center gap-3">
                        <FileText className="w-4 h-4 text-slate-400" />
                        <div>
                          <p className="text-sm text-[#0A192F]">{h.product_name || "Unknown product"}</p>
                          <p className="text-xs text-slate-400">{h.doc_type} · {h.filename}</p>
                        </div>
                      </div>
                      <Badge className="text-xs bg-slate-100 text-slate-600">{h.destination_country || h.origin_country}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
