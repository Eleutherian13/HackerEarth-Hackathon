import { PageLayout } from "@/components/laos/PageLayout";
import { ShieldCheck, Edit3, Check, X, FileText, AlertTriangle } from "lucide-react";

const events = [
  {
    ts: "2026-05-03 11:42:08",
    actor: "R. Menon",
    role: "Sr. Legal Officer",
    action: "approved",
    target: "d-9002",
    detail: "Interim order verified against ¶ 49 · confidence 0.94",
  },
  {
    ts: "2026-05-03 10:18:55",
    actor: "System",
    role: "Action Engine",
    action: "escalated",
    target: "d-9006",
    detail: "Deadline T-0 reached; auto-escalated to Chief Secretary's office",
  },
  {
    ts: "2026-05-02 17:04:11",
    actor: "A. Krishnan",
    role: "Reviewer",
    action: "edited",
    target: "d-9005",
    detail: "Department mapping changed: Industries → Pollution Control Board",
  },
  {
    ts: "2026-05-02 14:33:20",
    actor: "System",
    role: "Legal Intelligence",
    action: "extracted",
    target: "W.P.(C) 8421/2026",
    detail: "9 directives extracted across 47 pages · 6 final, 1 interim, 1 observation, 1 condition",
  },
  {
    ts: "2026-05-02 09:47:02",
    actor: "R. Menon",
    role: "Sr. Legal Officer",
    action: "rejected",
    target: "d-8991",
    detail: "Confidence 0.61 · source paragraph mismatch · returned to extractor",
  },
  {
    ts: "2026-05-01 16:12:40",
    actor: "System",
    role: "Ingestion",
    action: "ingested",
    target: "W.P.(C) 8421/2026",
    detail: "Digital PDF · 47 pages · 4.2s processing",
  },
];

const actionMeta: Record<string, { icon: typeof Check; cls: string }> = {
  approved: { icon: Check, cls: "bg-success/10 text-success" },
  rejected: { icon: X, cls: "bg-destructive/10 text-destructive" },
  edited: { icon: Edit3, cls: "bg-info/10 text-info" },
  escalated: { icon: AlertTriangle, cls: "bg-warning/10 text-warning" },
  extracted: { icon: FileText, cls: "bg-primary/10 text-primary" },
  ingested: { icon: FileText, cls: "bg-muted text-muted-foreground" },
};

const AuditTrail = () => (
  <PageLayout
    eyebrow="§ Audit Trail"
    title="Every action. Every actor. Every version."
    description="Tamper-evident chronology of all reviewer and system actions, retained for the statutory period."
  >
    <section className="py-12">
      <div className="mx-auto max-w-[1400px] px-6">
        <div className="mb-6 flex items-center gap-2 rounded-sm border border-success/30 bg-success/5 px-4 py-2.5 text-xs">
          <ShieldCheck className="h-4 w-4 text-success" />
          <span>Chain integrity verified · last hash check 11:50 IST · {events.length} events shown</span>
        </div>

        <div className="paper rounded-sm">
          <div className="grid grid-cols-12 gap-4 border-b border-border bg-secondary/40 px-5 py-3 text-[10px] uppercase tracking-wider text-muted-foreground">
            <div className="col-span-2">Timestamp</div>
            <div className="col-span-2">Actor</div>
            <div className="col-span-1">Action</div>
            <div className="col-span-2">Target</div>
            <div className="col-span-5">Detail</div>
          </div>
          <div className="divide-y divide-border">
            {events.map((e, i) => {
              const meta = actionMeta[e.action];
              const Icon = meta.icon;
              return (
                <div key={i} className="grid grid-cols-12 items-center gap-4 px-5 py-4 hover:bg-secondary/40">
                  <div className="col-span-2 font-mono text-[11px] text-muted-foreground">{e.ts}</div>
                  <div className="col-span-2 text-xs">
                    <div className="font-500 text-foreground">{e.actor}</div>
                    <div className="text-muted-foreground">{e.role}</div>
                  </div>
                  <div className="col-span-1">
                    <span className={`inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-[10px] font-500 uppercase tracking-wider ${meta.cls}`}>
                      <Icon className="h-3 w-3" />
                      {e.action}
                    </span>
                  </div>
                  <div className="col-span-2 font-mono text-xs text-foreground">{e.target}</div>
                  <div className="col-span-5 text-xs text-muted-foreground">{e.detail}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  </PageLayout>
);

export default AuditTrail;
