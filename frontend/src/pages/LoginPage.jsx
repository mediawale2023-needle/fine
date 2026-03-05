import { useState } from "react";
import { useAuth, API } from "@/App";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Building2, Lock, Mail, ArrowRight } from "lucide-react";
import axios from "axios";

const ROLE_OPTIONS = [
  { value: "exporter", label: "Indian Exporter" },
  { value: "buyer", label: "International Buyer" },
];

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [role, setRole] = useState("exporter");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const getHomeRoute = (userRole) => {
    if (userRole === "admin") return "/admin";
    if (userRole === "buyer") return "/buyer";
    return "/exporter";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isLogin) {
        const user = await login(email, password);
        toast.success("Welcome back!");
        navigate(getHomeRoute(user.role));
      } else {
        const user = await register(email, password, companyName, role);
        toast.success("Account created successfully!");
        navigate(role === "buyer" ? "/buyer/profile" : "/exporter/profile");
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const seedDemoData = async () => {
    try {
      await axios.post(`${API}/seed`);
      toast.success("Demo data seeded! Login: admin@tradenexus.com / admin123");
    } catch (e) {
      toast.info("Demo data already exists");
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Hero Image */}
      <div 
        className="hidden lg:flex lg:w-1/2 login-hero items-end p-12"
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1688786063751-a91b041b7821?crop=entropy&cs=srgb&fm=jpg&q=85')" }}
      >
        <div className="relative z-10 text-white max-w-lg">
          <h1 className="font-display text-5xl font-bold mb-4 tracking-tight">
            TradeNexus AI
          </h1>
          <p className="text-lg text-slate-200 leading-relaxed">
            Enterprise-grade AI trade matchmaking engine. Converting international demand into verified, high-probability trade opportunities.
          </p>
          <div className="mt-8 flex items-center gap-6 text-sm text-slate-300">
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-gold"></div>
              Africa
            </span>
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-gold"></div>
              Middle East
            </span>
            <span className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-gold"></div>
              Europe
            </span>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-offwhite">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-navy rounded-sm flex items-center justify-center">
                <span className="text-gold font-display font-bold text-xl">T</span>
              </div>
              <span className="font-display text-xl font-semibold text-navy">TradeNexus</span>
            </div>
            <h2 className="font-display text-3xl font-bold text-slate-900 tracking-tight">
              {isLogin ? "Welcome Back" : "Create Account"}
            </h2>
            <p className="mt-2 text-slate-500">
              {isLogin ? "Sign in to access your trade dashboard" : "Register to get started"}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLogin && (
              <>
                {/* Role selector */}
                <div>
                  <Label className="text-xs uppercase tracking-wider text-slate-500 font-medium">
                    I am registering as
                  </Label>
                  <div className="mt-1.5 flex gap-2">
                    {ROLE_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setRole(opt.value)}
                        className={`flex-1 py-2.5 px-3 rounded-sm border text-sm font-medium transition-colors ${
                          role === opt.value
                            ? "bg-[#0A192F] text-white border-[#0A192F]"
                            : "bg-white text-slate-600 border-slate-300 hover:border-[#0A192F]"
                        }`}
                        data-testid={`role-${opt.value}`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <Label htmlFor="company" className="text-xs uppercase tracking-wider text-slate-500 font-medium">
                    Company Name
                  </Label>
                  <div className="mt-1.5 relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="company"
                      data-testid="company-input"
                      type="text"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      className="pl-10 h-12 bg-white border-slate-300 focus:ring-gold focus:border-gold"
                      placeholder="Your Company Ltd"
                      required={!isLogin}
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <Label htmlFor="email" className="text-xs uppercase tracking-wider text-slate-500 font-medium">
                Email Address
              </Label>
              <div className="mt-1.5 relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  id="email"
                  data-testid="email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 h-12 bg-white border-slate-300 focus:ring-gold focus:border-gold"
                  placeholder="you@company.com"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="password" className="text-xs uppercase tracking-wider text-slate-500 font-medium">
                Password
              </Label>
              <div className="mt-1.5 relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  id="password"
                  data-testid="password-input"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 h-12 bg-white border-slate-300 focus:ring-gold focus:border-gold"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              data-testid="login-submit-btn"
              disabled={loading}
              className="w-full h-12 bg-navy hover:bg-charcoal text-white font-medium rounded-sm btn-pressed"
            >
              {loading ? "Please wait..." : (
                <span className="flex items-center justify-center gap-2">
                  {isLogin ? "Sign In" : "Create Account"}
                  <ArrowRight className="w-4 h-4" />
                </span>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-teal-deep hover:text-navy transition-colors"
              data-testid="toggle-auth-mode"
            >
              {isLogin ? "New exporter? Create an account" : "Already have an account? Sign in"}
            </button>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-200">
            <button
              onClick={seedDemoData}
              className="w-full text-sm text-slate-500 hover:text-slate-700 transition-colors"
              data-testid="seed-demo-btn"
            >
              Load Demo Data (for testing)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
