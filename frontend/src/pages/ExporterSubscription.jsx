import { useState, useEffect } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { CreditCard, CheckCircle, Crown, Star, Zap } from "lucide-react";

const PLANS = [
  {
    id: "Basic",
    name: "Basic",
    price: 9999,
    icon: Star,
    features: [
      "View trade opportunities",
      "Express interest in deals",
      "Basic profile",
      "Email support"
    ],
    color: "slate"
  },
  {
    id: "Premium",
    name: "Premium",
    price: 24999,
    icon: Zap,
    features: [
      "Everything in Basic",
      "Request trade financing",
      "Priority matching",
      "Risk score access",
      "Priority support"
    ],
    color: "gold",
    popular: true
  },
  {
    id: "Enterprise",
    name: "Enterprise",
    price: 49999,
    icon: Crown,
    features: [
      "Everything in Premium",
      "Dedicated account manager",
      "Custom financing terms",
      "API access",
      "24/7 phone support"
    ],
    color: "navy"
  }
];

export default function ExporterSubscription() {
  const { authAxios, user } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);

  const fetchSubscription = async () => {
    setLoading(true);
    try {
      const res = await authAxios.get("/subscription/me");
      setSubscription(res.data);
    } catch (e) {
      toast.error("Failed to load subscription");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscription();
  }, []);

  const handleUpgrade = async (planId) => {
    setUpgrading(true);
    try {
      await authAxios.post("/subscription/upgrade", { plan: planId });
      toast.success(`Successfully upgraded to ${planId} plan!`);
      fetchSubscription();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to upgrade");
    } finally {
      setUpgrading(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content bg-offwhite">
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div>
            <h1 className="font-display text-3xl font-bold text-slate-900 tracking-tight">
              Subscription
            </h1>
            <p className="mt-1 text-slate-500">Manage your TradeNexus subscription plan</p>
          </div>
        </header>

        <div className="p-8">
          {/* Current Plan */}
          {subscription && (
            <div className="premium-card p-6 rounded-sm mb-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gold/20 rounded-sm flex items-center justify-center">
                    <CreditCard className="w-6 h-6 text-gold" />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500 font-medium">Current Plan</p>
                    <p className="text-2xl font-bold text-slate-900">{subscription.plan}</p>
                  </div>
                </div>
                <div className="text-right">
                  <Badge className={subscription.is_valid ? "bg-emerald-500" : "bg-red-500"}>
                    {subscription.is_valid ? "Active" : "Expired"}
                  </Badge>
                  {subscription.expiry && (
                    <p className="text-sm text-slate-500 mt-1">
                      Expires: {new Date(subscription.expiry).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Plan Cards */}
          <div className="grid grid-cols-3 gap-6">
            {PLANS.map((plan) => {
              const isCurrentPlan = subscription?.plan === plan.id;
              const Icon = plan.icon;
              
              return (
                <div
                  key={plan.id}
                  className={`premium-card p-6 rounded-sm relative ${
                    plan.popular ? "border-2 border-gold" : ""
                  }`}
                >
                  {plan.popular && (
                    <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gold text-white">
                      Most Popular
                    </Badge>
                  )}
                  
                  <div className="text-center mb-6">
                    <div className={`w-14 h-14 mx-auto mb-4 rounded-sm flex items-center justify-center ${
                      plan.color === "gold" ? "bg-gold/20" :
                      plan.color === "navy" ? "bg-navy/10" : "bg-slate-100"
                    }`}>
                      <Icon className={`w-7 h-7 ${
                        plan.color === "gold" ? "text-gold" :
                        plan.color === "navy" ? "text-navy" : "text-slate-600"
                      }`} />
                    </div>
                    <h3 className="font-display text-xl font-bold text-slate-900">{plan.name}</h3>
                    <div className="mt-2">
                      <span className="text-3xl font-bold text-slate-900">₹{plan.price.toLocaleString()}</span>
                      <span className="text-slate-500">/year</span>
                    </div>
                  </div>

                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-slate-600">
                        <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <Button
                    onClick={() => handleUpgrade(plan.id)}
                    disabled={upgrading || isCurrentPlan}
                    className={`w-full ${
                      isCurrentPlan 
                        ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                        : plan.popular 
                          ? "bg-gold hover:bg-amber-600 text-white" 
                          : "bg-navy hover:bg-charcoal text-white"
                    }`}
                  >
                    {isCurrentPlan ? "Current Plan" : upgrading ? "Processing..." : "Select Plan"}
                  </Button>
                </div>
              );
            })}
          </div>

          {/* Info Note */}
          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-sm">
            <p className="text-sm text-blue-700">
              <strong>Note:</strong> Subscription is required to access trade financing features. 
              Premium and Enterprise plans include priority matching and advanced analytics.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
