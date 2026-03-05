import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { CreditCard, CheckCircle, Crown, Star, Zap, Shield } from "lucide-react";

const PLANS = [
  {
    id: "Basic",
    name: "Basic",
    price: 9999,
    price_paise: 999900,
    icon: Star,
    features: [
      "View trade opportunities",
      "Express interest in deals",
      "Basic exporter profile",
      "Email support",
    ],
    color: "slate",
  },
  {
    id: "Premium",
    name: "Premium",
    price: 24999,
    price_paise: 2499900,
    icon: Zap,
    features: [
      "Everything in Basic",
      "Request trade financing (NBFC routing)",
      "Priority AI matchmaking",
      "Risk score & market intelligence",
      "Deal Room messaging",
      "WhatsApp deal alerts",
      "Priority support",
    ],
    color: "gold",
    popular: true,
  },
  {
    id: "Enterprise",
    name: "Enterprise",
    price: 49999,
    price_paise: 4999900,
    icon: Crown,
    features: [
      "Everything in Premium",
      "Dedicated account manager",
      "Custom NBFC financing terms",
      "Document intelligence (AI parse)",
      "API access",
      "Data export & reports",
      "24/7 phone support",
    ],
    color: "navy",
  },
];

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) { resolve(true); return; }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function ExporterSubscription() {
  const { authAxios, user } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(null); // plan id being upgraded

  const fetchSubscription = async () => {
    setLoading(true);
    try {
      const res = await authAxios.get("/subscription/me");
      setSubscription(res.data);
    } catch {
      toast.error("Failed to load subscription");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSubscription(); }, []);

  const handleSelectPlan = async (plan) => {
    setUpgrading(plan.id);
    try {
      // Step 1: Create Razorpay order
      const orderRes = await authAxios.post("/payments/create-order", { plan: plan.id });
      const { order_id, amount, currency, key_id, mock } = orderRes.data;

      // Step 2: For mock (dev mode), skip Razorpay UI and directly verify
      if (mock) {
        const mockPaymentId = `pay_mock_${Date.now()}`;
        const mockSig = "mock_signature";
        await authAxios.post("/payments/verify", {
          razorpay_order_id: order_id,
          razorpay_payment_id: mockPaymentId,
          razorpay_signature: mockSig,
          plan: plan.id,
        });
        toast.success(`${plan.name} plan activated! (dev mode)`);
        fetchSubscription();
        setUpgrading(null);
        return;
      }

      // Step 3: Load Razorpay and open payment modal
      const loaded = await loadRazorpayScript();
      if (!loaded) {
        toast.error("Failed to load payment gateway. Please try again.");
        setUpgrading(null);
        return;
      }

      const options = {
        key: key_id,
        amount,
        currency,
        name: "TradeNexus",
        description: `${plan.name} Subscription — 1 Year`,
        order_id,
        prefill: {
          name: user?.company_name,
          email: user?.email,
        },
        theme: { color: "#0A192F" },
        handler: async (response) => {
          try {
            await authAxios.post("/payments/verify", {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              plan: plan.id,
            });
            toast.success(`${plan.name} plan activated! Welcome aboard.`);
            fetchSubscription();
          } catch {
            toast.error("Payment verification failed. Contact support.");
          } finally {
            setUpgrading(null);
          }
        },
        modal: {
          ondismiss: () => setUpgrading(null),
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to initiate payment");
      setUpgrading(null);
    }
  };

  const isCurrentPlan = (planId) => subscription?.plan === planId && subscription?.is_valid;

  return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="bg-white border-b border-slate-200 px-8 py-5">
          <h1 className="font-display text-2xl font-semibold text-[#0A192F]">Subscription</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Choose a plan to unlock TradeNexus features
          </p>
        </div>

        <div className="p-8">
          {/* Current plan banner */}
          {!loading && subscription && (
            <div className="mb-8 p-5 bg-[#0A192F] rounded-sm flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-[#C5A059]/20 rounded-sm flex items-center justify-center">
                  <CreditCard className="w-5 h-5 text-[#C5A059]" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 uppercase tracking-wider">Current Plan</p>
                  <p className="text-xl font-display font-semibold text-white">{subscription.plan}</p>
                </div>
              </div>
              <div className="text-right">
                <Badge className={subscription.is_valid ? "bg-emerald-500 text-white" : "bg-red-500 text-white"}>
                  {subscription.is_valid ? "Active" : "Expired"}
                </Badge>
                {subscription.expiry && (
                  <p className="text-sm text-slate-400 mt-1">
                    Renews {new Date(subscription.expiry).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Plan cards */}
          <div className="grid grid-cols-3 gap-6">
            {PLANS.map((plan) => {
              const Icon = plan.icon;
              const current = isCurrentPlan(plan.id);
              const busy = upgrading === plan.id;

              return (
                <div
                  key={plan.id}
                  className={`bg-white border rounded-sm p-6 relative flex flex-col ${
                    plan.popular
                      ? "border-[#C5A059] shadow-lg"
                      : "border-slate-200"
                  }`}
                  data-testid={`plan-${plan.id.toLowerCase()}`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <Badge className="bg-[#C5A059] text-white text-xs px-3">Most Popular</Badge>
                    </div>
                  )}

                  <div className="text-center mb-6">
                    <div className={`w-12 h-12 mx-auto mb-3 rounded-sm flex items-center justify-center ${
                      plan.color === "gold" ? "bg-[#C5A059]/15" :
                      plan.color === "navy" ? "bg-[#0A192F]/10" : "bg-slate-100"
                    }`}>
                      <Icon className={`w-6 h-6 ${
                        plan.color === "gold" ? "text-[#C5A059]" :
                        plan.color === "navy" ? "text-[#0A192F]" : "text-slate-500"
                      }`} />
                    </div>
                    <h3 className="font-display text-xl font-semibold text-[#0A192F]">{plan.name}</h3>
                    <div className="mt-2">
                      <span className="text-3xl font-display font-bold text-[#0A192F]">
                        ₹{plan.price.toLocaleString("en-IN")}
                      </span>
                      <span className="text-slate-500 text-sm"> /year</span>
                    </div>
                  </div>

                  <ul className="space-y-2.5 mb-6 flex-1">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-slate-600">
                        <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <Button
                    onClick={() => !current && handleSelectPlan(plan)}
                    disabled={busy || current || !!upgrading}
                    className={`w-full ${
                      current
                        ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                        : plan.popular
                          ? "bg-[#C5A059] hover:bg-amber-600 text-white"
                          : "bg-[#0A192F] hover:bg-[#1E293B] text-white"
                    }`}
                    data-testid={`select-plan-${plan.id.toLowerCase()}`}
                  >
                    {current ? (
                      <><CheckCircle className="w-4 h-4 mr-2" />Current Plan</>
                    ) : busy ? (
                      "Processing..."
                    ) : (
                      `Select ${plan.name}`
                    )}
                  </Button>
                </div>
              );
            })}
          </div>

          {/* Security note */}
          <div className="mt-8 p-4 bg-slate-50 border border-slate-200 rounded-sm flex items-center gap-3">
            <Shield className="w-5 h-5 text-slate-400 flex-shrink-0" />
            <p className="text-sm text-slate-500">
              Payments processed securely via <strong>Razorpay</strong>. GST invoice provided automatically.
              Subscriptions auto-renew annually. Cancel any time from your account.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
