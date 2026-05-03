import { dnaTimeline } from "@/data/laos";
import { Dna, AlertTriangle } from "lucide-react";

const outcomeMeta: Record<string, { label: string; cls: string }> = {
  ordered: { label: "Ordered", cls: "bg-info/10 text-info" },
  complied: { label: "Complied", cls: "bg-success/10 text-success" },
  partial: { label: "Partial", cls: "bg-warning/10 text-warning" },
  active: { label: "Active", cls: "bg-accent/10 text-accent" },
};

export const JudgmentDNA = () => {
  return (
    <section className="border-b border-border bg-primary py-20 text-primary-foreground">
      <div className="mx-auto max-w-[1400px] px-6">
        <div className="mb-10 grid gap-8 lg:grid-cols-[1fr_1.2fr]">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.2em] text-gold">
              <Dna className="h-4 w-4" /> Signature feature
            </div>
            <h2 className="font-display text-4xl font-500 leading-tight">
              Judgment DNA — case evolution across years, not just pages.
            </h2>
            <p className="mt-5 max-w-md text-sm leading-relaxed text-primary-foreground/75">
              When a fresh PDF lands, LAOS fingerprints it against the entire case lineage. Prior orders,
              what was complied, what slipped, and any directive that contradicts a previous one —
              surfaced before the brief leaves the verification console.
            </p>
            <div className="mt-6 rounded-sm border border-gold/30 bg-gold/5 p-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-gold" />
                <div className="text-sm">
                  <span className="font-600 text-gold">Contradiction detected.</span>{" "}
                  Directive <span className="font-mono">d-9005</span> conflicts with the conditional liberty
                  granted in <span className="font-mono">I.A. 18/2024</span>. Flag for legal counsel.
                </div>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute left-[7px] top-2 bottom-2 w-px bg-gradient-to-b from-gold/60 via-primary-foreground/20 to-transparent" />
            <div className="space-y-5">
              {dnaTimeline.map((e, i) => (
                <div key={e.date} className="relative pl-8">
                  <div className={`absolute left-0 top-1.5 h-3.5 w-3.5 rounded-full border-2 ${i === dnaTimeline.length - 1 ? "border-gold bg-gold shadow-seal" : "border-primary-foreground/40 bg-primary"}`} />
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="font-mono text-xs text-primary-foreground/70">
                      {new Date(e.date).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })}
                    </span>
                    <span className={`rounded-sm px-2 py-0.5 text-[10px] font-500 uppercase tracking-wider ${outcomeMeta[e.outcome].cls}`}>
                      {outcomeMeta[e.outcome].label}
                    </span>
                  </div>
                  <div className="mt-1 font-mono text-xs text-gold">{e.caseNo}</div>
                  <div className="mt-1 text-sm text-primary-foreground/90">{e.event}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
