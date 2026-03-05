import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Save } from "lucide-react";

const SECTORS = [
  "Agriculture",
  "Marine / Frozen Foods",
  "Pharma",
  "Special Chemicals",
  "Value-Added Agri Products",
];

const INDUSTRIES = [
  "Food & Beverage",
  "Pharmaceuticals",
  "Retail & Distribution",
  "Manufacturing",
  "Healthcare",
  "Chemicals",
  "Other",
];

export default function BuyerProfile() {
  const { authAxios } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isNew, setIsNew] = useState(false);
  const [form, setForm] = useState({
    company_name: "",
    country: "",
    industry: "",
    annual_import_volume: "",
    preferred_sectors: [],
  });

  useEffect(() => {
    const load = async () => {
      try {
        const res = await authAxios.get("/buyer/profile");
        setForm({
          company_name: res.data.company_name || "",
          country: res.data.country || "",
          industry: res.data.industry || "",
          annual_import_volume: res.data.annual_import_volume || "",
          preferred_sectors: res.data.preferred_sectors || [],
        });
      } catch (err) {
        if (err.response?.status === 404) setIsNew(true);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const toggleSector = (sector) => {
    setForm(f => ({
      ...f,
      preferred_sectors: f.preferred_sectors.includes(sector)
        ? f.preferred_sectors.filter(s => s !== sector)
        : [...f.preferred_sectors, sector],
    }));
  };

  const handleSave = async () => {
    if (!form.company_name || !form.country || !form.industry) {
      toast.error("Please fill in company name, country, and industry");
      return;
    }
    setSaving(true);
    try {
      if (isNew) {
        await authAxios.post("/buyer/profile", form);
        setIsNew(false);
        toast.success("Profile created successfully");
      } else {
        await authAxios.put("/buyer/profile", form);
        toast.success("Profile updated");
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar />
      <div className="flex-1 flex items-center justify-center text-slate-400">Loading...</div>
    </div>
  );

  return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="bg-white border-b border-slate-200 px-8 py-5">
          <h1 className="font-display text-2xl font-semibold text-[#0A192F]">Buyer Profile</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {isNew ? "Set up your profile to post requirements" : "Manage your company profile"}
          </p>
        </div>

        <div className="p-8 max-w-2xl space-y-6">
          <div className="bg-white border border-slate-200 rounded-sm p-6">
            <h2 className="font-display font-semibold text-[#0A192F] mb-4">Company Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="company_name">Company Name</Label>
                <Input
                  id="company_name"
                  value={form.company_name}
                  onChange={e => setForm(f => ({ ...f, company_name: e.target.value }))}
                  className="mt-1"
                  data-testid="buyer-company-name"
                />
              </div>
              <div>
                <Label htmlFor="country">Country</Label>
                <Input
                  id="country"
                  placeholder="e.g. UAE, Nigeria"
                  value={form.country}
                  onChange={e => setForm(f => ({ ...f, country: e.target.value }))}
                  className="mt-1"
                />
              </div>
              <div>
                <Label>Industry</Label>
                <Select value={form.industry} onValueChange={v => setForm(f => ({ ...f, industry: v }))}>
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Select industry" />
                  </SelectTrigger>
                  <SelectContent>
                    {INDUSTRIES.map(i => <SelectItem key={i} value={i}>{i}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2">
                <Label htmlFor="annual_import_volume">Annual Import Volume (approx.)</Label>
                <Input
                  id="annual_import_volume"
                  placeholder="e.g. $2M, ₹5 Cr"
                  value={form.annual_import_volume}
                  onChange={e => setForm(f => ({ ...f, annual_import_volume: e.target.value }))}
                  className="mt-1"
                />
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-sm p-6">
            <h2 className="font-display font-semibold text-[#0A192F] mb-2">Preferred Sectors</h2>
            <p className="text-sm text-slate-500 mb-4">Which sectors are you primarily interested in?</p>
            <div className="flex flex-wrap gap-2">
              {SECTORS.map(sector => (
                <button
                  key={sector}
                  type="button"
                  onClick={() => toggleSector(sector)}
                  className={`px-3 py-2 rounded-sm border text-sm font-medium transition-colors ${
                    form.preferred_sectors.includes(sector)
                      ? "bg-[#0A192F] text-white border-[#0A192F]"
                      : "bg-white text-slate-600 border-slate-300 hover:border-[#0A192F]"
                  }`}
                >
                  {sector}
                </button>
              ))}
            </div>
          </div>

          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-[#0A192F] hover:bg-[#1E293B] text-white"
            data-testid="save-buyer-profile-btn"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? "Saving..." : isNew ? "Create Profile" : "Save Changes"}
          </Button>
        </div>
      </main>
    </div>
  );
}
