import { cases, directives } from "@/data/laos";
import { AlertCircle, Clock, TrendingUp, Building2 } from "lucide-react";
import { useApi } from "@/hooks/useApi";
import { dashboardApi } from "@/lib/api";

const statusCls: Record<string, string> = {
  in_review: "bg-warning/10 text-warning",
  active: "bg-success/10 text-success",
  closed: "bg-muted text-muted-foreground",
  ingested: "bg-info/10 text-info",
  classified: "bg-primary/10 text-primary",
};

export const Dashboard = () => {
  const upcoming = directives
    .filter((d) => d.daysLeft >= 0 && d.daysLeft < 60)
    .sort((a, b) => a.daysLeft - b.daysLeft);

  const stats = useApi(() => dashboardApi.summary(), []);
  const live = stats.data;
  const liveOn = !!live;

  return (
    <section className="border-b border-border bg-background py-20">
      <div className="mx-auto max-w-[1400px] px-6">
        <div className="mb-10 flex items-end justify-between gap-8">
          <div>
            <div className="mb-3 text-[11px] uppercase tracking-[0.2em] text-accent">§ Layer 05 · Orchestration</div>
            <h2 className="max-w-2xl font-display text-4xl font-500 leading-tight text-ink">
              The compliance dashboard. Department-aware. Deadline-driven.
            </h2>
          </div>
        </div>

        {/* KPI strip */}
        <div className="mb-8 grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-border bg-border md:grid-cols-4">
          {[
            { i: TrendingUp, k: liveOn ? String(live!.active_cases) : "47", v: "Active cases", c: "text-info" },
            { i: Clock, k: liveOn ? String(live!.due_in_7_days) : "12", v: "Due in 7 days", c: "text-warning" },
            { i: AlertCircle, k: liveOn ? String(live!.escalated) : "3", v: "Escalated", c: "text-destructive" },
            { i: Building2, k: liveOn ? String(live!.departments_engaged) : "18", v: "Departments engaged", c: "text-primary" },
          ].map((s) => (
            <div key={s.v} className="bg-card p-5">
              <s.i className={`h-5 w-5 ${s.c}`} strokeWidth={1.5} />
              <div className="mt-3 font-display text-3xl font-600 text-ink">{s.k}</div>
              <div className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">{s.v}</div>
            </div>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
          {/* case pipeline */}
          <div className="paper rounded-sm">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div>
                <div className="font-display text-lg font-600">Case Pipeline</div>
                <div className="text-xs text-muted-foreground">Last 14 days · sorted by judgment date</div>
              </div>
              <div className="text-[11px] uppercase tracking-wider text-muted-foreground">5 of 47</div>
            </div>

            <div className="divide-y divide-border">
              {cases.map((c) => (
                <div key={c.id} className="grid grid-cols-12 items-center gap-4 px-5 py-4 transition-colors hover:bg-secondary/40">
                  <div className="col-span-6">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] text-muted-foreground">{c.caseNo}</span>
                      <span className={`rounded-sm px-1.5 py-0.5 text-[10px] font-500 uppercase tracking-wider ${statusCls[c.status]}`}>
                        {c.status.replace("_", " ")}
                      </span>
                      {c.dnaMatches > 0 && (
                        <span className="rounded-sm bg-gold/10 px-1.5 py-0.5 text-[10px] font-500 uppercase tracking-wider text-gold">
                          DNA · {c.dnaMatches}
                        </span>
                      )}
                    </div>
                    <div className="mt-1 line-clamp-1 font-display text-sm font-600 text-ink">{c.title}</div>
                    <div className="text-[11px] text-muted-foreground">{c.court} · {c.bench}</div>
                  </div>
                  <div className="col-span-2 text-xs">
                    <div className="text-muted-foreground">Judgment</div>
                    <div className="font-mono">{new Date(c.judgmentDate).toLocaleDateString("en-GB")}</div>
                  </div>
                  <div className="col-span-2 text-xs">
                    <div className="text-muted-foreground">Directives</div>
                    <div>
                      <span className="font-mono text-foreground">{c.directives}</span>
                      {c.pending > 0 && (
                        <span className="ml-1 text-warning">· {c.pending} pending</span>
                      )}
                    </div>
                  </div>
                  <div className="col-span-2 text-xs">
                    <div className="text-muted-foreground">Type</div>
                    <div className="font-mono uppercase">{c.pdfType} · {c.pages}p</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* deadlines */}
          <div className="paper rounded-sm">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div>
                <div className="font-display text-lg font-600">Deadline Watch</div>
                <div className="text-xs text-muted-foreground">Auto-escalation at T-3 days</div>
              </div>
              <div className="text-[11px] uppercase tracking-wider text-warning">{upcoming.length} pending</div>
            </div>
            <div className="divide-y divide-border">
              {upcoming.map((d) => {
                const urgency = d.daysLeft <= 7 ? "destructive" : d.daysLeft <= 21 ? "warning" : "info";
                const cls = urgency === "destructive" ? "text-destructive bg-destructive/5" : urgency === "warning" ? "text-warning bg-warning/5" : "text-info bg-info/5";
                return (
                  <div key={d.id} className="px-5 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-[11px] uppercase tracking-wider text-muted-foreground">{d.department}</div>
                        <div className="mt-1 line-clamp-2 text-xs leading-snug text-foreground">{d.text}</div>
                      </div>
                      <div className={`shrink-0 rounded-sm px-2 py-1 text-center ${cls}`}>
                        <div className="font-display text-lg font-600 leading-none">{d.daysLeft}</div>
                        <div className="text-[9px] uppercase tracking-wider">days</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
