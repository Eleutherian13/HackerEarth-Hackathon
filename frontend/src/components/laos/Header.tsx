import { Scale, Search, Bell, LogOut, LogIn } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { authApi } from "@/lib/api";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/cases", label: "Cases" },
  { to: "/upload", label: "Upload" },
  { to: "/verification", label: "Verification" },
  { to: "/action-plan", label: "Action Plan" },
  { to: "/departments", label: "Departments" },
  { to: "/audit", label: "Audit Trail" },
];

export const Header = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    authApi.me()
      .then((u) => {
        if (mounted && u?.email) setEmail((u as any).email ?? null);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const handleSignOut = async () => {
    await authApi.logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between gap-6 px-6">
        <NavLink to="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-gradient-judicial shadow-paper">
            <Scale className="h-5 w-5 text-primary-foreground" strokeWidth={1.5} />
          </div>
          <div className="leading-tight">
            <div className="font-display text-lg font-600 tracking-tight text-ink">LAOS</div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              Legal Action Orchestration
            </div>
          </div>
        </NavLink>

        <nav className="hidden items-center gap-1 text-sm md:flex">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                `rounded-sm px-3 py-1.5 transition-colors ${
                  isActive
                    ? "bg-secondary text-foreground"
                    : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <div className="relative hidden lg:block">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              placeholder="Search case no., directive, department…"
              className="h-9 w-72 rounded-sm border border-input bg-card pl-8 pr-3 text-sm placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-ring/30"
            />
          </div>
          <button className="relative inline-flex h-9 w-9 items-center justify-center rounded-sm border border-input bg-card hover:bg-secondary">
            <Bell className="h-4 w-4" />
            <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-accent" />
          </button>
          {email ? (
            <>
              <div className="ml-1 flex h-9 items-center gap-2 rounded-sm border border-input bg-card px-3">
                <div className="h-6 w-6 rounded-full bg-gradient-seal text-center text-[11px] font-600 uppercase leading-6 text-accent-foreground">
                  {email.slice(0, 2)}
                </div>
                <div className="hidden text-xs leading-tight md:block">
                  <div className="font-500 max-w-[140px] truncate">{email}</div>
                  <div className="text-muted-foreground">Legal Officer</div>
                </div>
              </div>
              <button
                onClick={handleSignOut}
                title="Sign out"
                className="inline-flex h-9 w-9 items-center justify-center rounded-sm border border-input bg-card hover:bg-secondary"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </>
          ) : (
            <NavLink
              to="/login"
              className="inline-flex h-9 items-center gap-2 rounded-sm bg-primary px-3 text-sm font-500 text-primary-foreground hover:bg-primary/90"
            >
              <LogIn className="h-4 w-4" /> Sign In
            </NavLink>
          )}
        </div>
      </div>
    </header>
  );
};
