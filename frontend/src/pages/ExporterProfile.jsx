import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Building2, Save, CheckCircle } from "lucide-react";
import { SECTORS } from "@/data/tradeData";

const ALL_CERTIFICATIONS = [
  "FSSAI", "ISO 22000", "HACCP", "BRC", "Halal", "Organic", "GlobalG.A.P.", "MSC", "ASC",
  "WHO-GMP", "USFDA", "EU-GMP", "ISO 9001", "ISO 13485", "GLP",
  "ISO 14001", "REACH", "MSDS", "ADR", "ISO 45001",
  "OEKO-TEX", "GOTS", "SA8000", "BCI",
  "CE Mark", "RoHS", "FCC", "BIS",
  "IATF 16949", "AIS", "Kosher", "FDA",
  "BIS Hallmark", "Kimberley Process", "RJC",
  "LWG", "FSC", "PEFC", "Fair Trade", "EPCH",
];
const SAMPLE_COUNTRIES = [
  "Nigeria", "Kenya", "South Africa", "Ghana", "Ethiopia", "Tanzania",
  "UAE", "Saudi Arabia", "Qatar", "Oman", "Kuwait", "Bahrain",
  "Germany", "France", "UK", "Netherlands", "Spain", "Italy", "Belgium", "Poland",
  "USA", "Canada", "Brazil", "Australia", "Japan", "Singapore", "Malaysia",
  "Morocco", "Egypt", "Bangladesh", "Sri Lanka",
];

export default function ExporterProfile() {
  const { authAxios, user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    sectors: [],
    products: "",
    capacity: "",
    certifications: [],
    country_experience: []
  });

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await authAxios.get("/exporter-profiles/me");
      setProfile(res.data);
      setFormData({
        sectors: res.data.sectors || [],
        products: res.data.products?.join(", ") || "",
        capacity: res.data.capacity || "",
        certifications: res.data.certifications || [],
        country_experience: res.data.country_experience || []
      });
    } catch (e) {
      // Profile doesn't exist yet
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.sectors.length === 0 || !formData.products || !formData.capacity) {
      toast.error("Please fill in all required fields");
      return;
    }
    
    const payload = {
      sectors: formData.sectors,
      products: formData.products.split(",").map((p) => p.trim()).filter(Boolean),
      capacity: formData.capacity,
      certifications: formData.certifications,
      country_experience: formData.country_experience
    };
    
    setSaving(true);
    try {
      if (profile) {
        await authAxios.put("/exporter-profiles/me", payload);
        toast.success("Profile updated successfully!");
      } else {
        await authAxios.post("/exporter-profiles", payload);
        toast.success("Profile created successfully!");
      }
      fetchProfile();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const toggleSector = (sector) => {
    setFormData((prev) => ({
      ...prev,
      sectors: prev.sectors.includes(sector)
        ? prev.sectors.filter((s) => s !== sector)
        : [...prev.sectors, sector]
    }));
  };

  const toggleCertification = (cert) => {
    setFormData((prev) => ({
      ...prev,
      certifications: prev.certifications.includes(cert)
        ? prev.certifications.filter((c) => c !== cert)
        : [...prev.certifications, cert]
    }));
  };

  const toggleCountry = (country) => {
    setFormData((prev) => ({
      ...prev,
      country_experience: prev.country_experience.includes(country)
        ? prev.country_experience.filter((c) => c !== country)
        : [...prev.country_experience, country]
    }));
  };

  if (loading) {
    return (
      <div className="app-container">
        <Sidebar />
        <main className="main-content bg-offwhite flex items-center justify-center">
          <p className="text-slate-500">Loading profile...</p>
        </main>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-navy rounded-sm flex items-center justify-center">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight">
                {user?.company_name}
              </h1>
              <p className="text-slate-500">Manage your exporter profile</p>
            </div>
            {profile && (
              <Badge className="ml-auto bg-emerald-500 text-white">
                <CheckCircle className="w-3 h-3 mr-1" />
                Profile Active
              </Badge>
            )}
          </div>
        </header>

        <div className="p-8 max-w-4xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Sectors */}
            <div className="premium-card p-6 rounded-sm">
              <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">
                Sectors Served *
              </h2>
              <div className="flex flex-wrap gap-3">
                {SECTORS.map((sector) => (
                  <button
                    key={sector}
                    type="button"
                    onClick={() => toggleSector(sector)}
                    data-testid={`sector-${sector.replace(/\s+/g, '-').toLowerCase()}`}
                    className={`px-4 py-2 rounded-sm border text-sm font-medium transition-colors ${
                      formData.sectors.includes(sector)
                        ? "bg-navy text-white border-navy"
                        : "bg-white text-slate-700 border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    {sector}
                  </button>
                ))}
              </div>
            </div>

            {/* Products & Capacity */}
            <div className="premium-card p-6 rounded-sm">
              <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">
                Products & Capacity
              </h2>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">Products *</Label>
                  <Input
                    value={formData.products}
                    onChange={(e) => setFormData({ ...formData, products: e.target.value })}
                    data-testid="products-input"
                    className="mt-1.5"
                    placeholder="e.g., Basmati Rice, Wheat, Spices"
                  />
                  <p className="text-xs text-slate-400 mt-1">Comma-separated list</p>
                </div>
                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500">Annual Capacity *</Label>
                  <Input
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                    data-testid="capacity-input"
                    className="mt-1.5"
                    placeholder="e.g., 5000 MT/year"
                  />
                </div>
              </div>
            </div>

            {/* Certifications */}
            <div className="premium-card p-6 rounded-sm">
              <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">
                Certifications
              </h2>
              <div className="flex flex-wrap gap-3">
                {ALL_CERTIFICATIONS.map((cert) => (
                  <div key={cert} className="flex items-center gap-2">
                    <Checkbox
                      id={cert}
                      checked={formData.certifications.includes(cert)}
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

            {/* Country Experience */}
            <div className="premium-card p-6 rounded-sm">
              <h2 className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">
                Country Experience
              </h2>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_COUNTRIES.map((country) => (
                  <button
                    key={country}
                    type="button"
                    onClick={() => toggleCountry(country)}
                    data-testid={`country-${country.toLowerCase()}`}
                    className={`px-3 py-1.5 rounded-sm border text-sm transition-colors ${
                      formData.country_experience.includes(country)
                        ? "bg-teal-deep text-white border-teal-deep"
                        : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    {country}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit */}
            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={saving}
                data-testid="save-profile-btn"
                className="bg-navy hover:bg-charcoal text-white px-8"
              >
                <Save className="w-4 h-4 mr-2" />
                {saving ? "Saving..." : (profile ? "Update Profile" : "Create Profile")}
              </Button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
