import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Scale } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { authService } from "@/lib/api-service";

export default function Signup() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem("auth_token");
    if (token) {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      return toast.error("Password must be at least 8 characters");
    }
    if (!fullName.trim()) {
      return toast.error("Full name is required");
    }

    setLoading(true);
    try {
      const response = await authService.register({
        full_name: fullName,
        email,
        password,
      });

      if (response.access_token) {
        // Store tokens and user info
        localStorage.setItem("auth_token", response.access_token);
        if (response.refresh_token) {
          localStorage.setItem("refresh_token", response.refresh_token);
        }
        if (response.user) {
          localStorage.setItem("user_email", response.user.email);
          localStorage.setItem("user_id", response.user.id);
          if (response.user.role) {
            localStorage.setItem("user_role", response.user.role);
          }
        }

        toast.success("Account created successfully!");
        navigate("/", { replace: true });
      } else {
        toast.error("Account creation failed");
      }
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || "Registration failed";
      toast.error(message);
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
              Create credentials to begin reviewing directives and orchestrating compliance.
            </p>
          </div>

          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                name="fullName"
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Official Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@gov.in"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Minimum 8 characters.</p>
            </div>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Creating account…" : "Create Account"}
            </Button>
          </form>

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
