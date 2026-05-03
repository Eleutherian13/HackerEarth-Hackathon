import { ArrowRight, FileCheck2, ShieldCheck, Activity } from "lucide-react";

export const Hero = () => {
  return (
    <section className="relative overflow-hidden border-b border-border bg-gradient-parchment">
      <div className="absolute inset-0 legal-grid opacity-[0.35]" aria-hidden />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-gold/60 to-transparent" />

      <div className="relative mx-auto grid max-w-[1400px] gap-10 px-6 py-16 lg:grid-cols-[1.3fr_1fr] lg:py-20">
        <div className="max-w-2xl">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-card/70 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            Live · Government of India · Pilot Deployment
          </div>
          <h1 className="font-display text-5xl font-500 leading-[1.05] tracking-tight text-ink text-balance lg:text-[64px]">
            Not a document reader.
            <span className="block italic text-accent">A compliance engine.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground">
            LAOS runs the post-judgment workflow — from the moment a verdict lands until the case is closed
            or appealed. Section-typed legal extraction, deadline-bound action items, mandatory verification,
            and Judgment DNA across the entire case history.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <button className="group inline-flex items-center gap-2 rounded-sm bg-primary px-5 py-3 text-sm font-500 text-primary-foreground shadow-paper transition-all hover:shadow-elevated">
              Open Verification Console
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </button>
            <button className="inline-flex items-center gap-2 rounded-sm border border-input bg-card px-5 py-3 text-sm font-500 hover:bg-secondary">
              Ingest Judgment PDF
            </button>
          </div>

          <div className="mt-10 grid grid-cols-3 gap-px overflow-hidden rounded-sm border border-border bg-border">
            {[
              { k: "1,284", v: "Directives extracted" },
              { k: "98.2%", v: "Source-traced" },
              { k: "0", v: "Unverified to dashboard" },
            ].map((s) => (
              <div key={s.v} className="bg-card px-5 py-4">
                <div className="font-display text-2xl font-600 text-ink">{s.k}</div>
                <div className="mt-1 text-[11px] uppercase tracking-wider text-muted-foreground">{s.v}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative">
          <div className="paper-elevated relative rounded-sm p-6">
            <div className="seal-line mb-4" />
            <div className="flex items-start justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Active Brief</div>
                <div className="mt-1 font-display text-lg font-600 leading-snug text-ink">
                  W.P.(C) 8421/2026
                </div>
                <div className="text-xs text-muted-foreground">High Court of Karnataka · 22 Apr 2026</div>
              </div>
              <span className="rounded-sm bg-accent/10 px-2 py-1 text-[10px] font-500 uppercase tracking-wider text-accent">
                Critical
              </span>
            </div>

            <div className="mt-5 space-y-3">
              {[
                { icon: FileCheck2, label: "Final Orders", v: "4", c: "text-primary" },
                { icon: Activity, label: "Interim · time-sensitive", v: "2", c: "text-warning" },
                { icon: ShieldCheck, label: "Conditions tracked", v: "3", c: "text-info" },
              ].map((r) => (
                <div key={r.label} className="flex items-center justify-between rounded-sm bg-secondary/50 px-3 py-2.5">
                  <div className="flex items-center gap-2.5">
                    <r.icon className={`h-4 w-4 ${r.c}`} strokeWidth={1.75} />
                    <span className="text-sm">{r.label}</span>
                  </div>
                  <span className="font-mono text-sm font-500">{r.v}</span>
                </div>
              ))}
            </div>

            <div className="mt-5 rounded-sm border border-dashed border-gold/50 bg-gold/5 p-3">
              <div className="text-[10px] uppercase tracking-wider text-gold">Judgment DNA</div>
              <div className="mt-1 text-sm text-foreground">
                <span className="font-600">2 prior orders</span> matched in this case lineage.
                One directive contradicts a 2024 interim order.
              </div>
            </div>
          </div>

          <div className="absolute -bottom-3 -right-3 -z-10 h-full w-full rounded-sm border border-border bg-secondary/50" />
        </div>
      </div>
    </section>
  );
};
