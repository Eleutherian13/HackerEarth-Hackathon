import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Scale, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3000";

export default function Signup() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleAccessRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !fullName) {
      return toast.error("Please fill in all fields");
    }
    
    setLoading(true);
    try {
      const url = `${API_URL}/api/v1/auth/request-access`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, full_name: fullName }),
      });
      
      if (response.ok) {
        setSubmitted(true);
        toast.success("Access request submitted successfully");
      } else {
        let errorMessage = "Failed to submit access request";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          // If response isn't JSON, use status text
          errorMessage = response.statusText || errorMessage;
        }
        toast.error(errorMessage);
      }
    } catch (error) {
      toast.error("Network error. Please try again.");
      console.error("Access request error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-parchment flex items-center justify-center px-6 py-12">
      <title>Request Access — LAOS</title>
      <div className="w-full max-w-md">
        <Link to="/" className="mb-8 flex items-center justify-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-sm bg-gradient-judicial shadow-paper">
            <Scale className="h-5 w-5 text-primary-foreground" strokeWidth={1.5} />
          </div>
          <div className="leading-tight">
            <div className="font-display text-xl font-600 tracking-tight text-ink">LAOS</div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              Legal Action Orchestration
            </div>
          </div>
        </Link>

        <div className="rounded-sm border border-border bg-card p-8 shadow-paper">
          <div className="mb-6">
            <div className="text-[11px] uppercase tracking-[0.2em] text-accent">Departmental Onboarding</div>
            <h1 className="mt-1 font-display text-2xl font-500 text-ink">Request Officer Access</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Submit your details for admin approval to begin reviewing directives.
            </p>
          </div>

          {submitted ? (
            <div className="space-y-4">
              <div className="flex gap-3 rounded-sm border border-green-200 bg-green-50 p-4">
                <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-500 text-green-900">Request Submitted</p>
                  <p className="text-sm text-green-700 mt-1">An administrator will review your request and create your account. You'll receive an email with login details.</p>
                </div>
              </div>
              <div className="pt-4">
                <Link to="/login" className="block text-center">
                  <Button variant="outline" className="w-full">
                    Back to Login
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleAccessRequest} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Officer Name"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email">Official Email</Label>
                <Input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@gov.in"
                />
              </div>
              <div className="flex gap-2 rounded-sm border border-amber-200 bg-amber-50 p-3 text-sm">
                <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <p className="text-amber-700">
                  Account creation requires administrator approval. You'll be notified when your access is ready.
                </p>
              </div>
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? "Submitting…" : "Submit Access Request"}
              </Button>
            </form>
          )}

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already enrolled?{" "}
            <Link to="/login" className="font-500 text-foreground underline-offset-4 hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
