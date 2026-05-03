import { directives, Directive } from "@/data/laos";
import { AlertTriangle, FileText, Highlighter, Check, X, Edit3, ShieldCheck } from "lucide-react";
import { useState } from "react";

const sectionMeta: Record<Directive["sectionType"], { label: string; cls: string }> = {
  final_order: { label: "Final Order", cls: "bg-primary/10 text-primary border-primary/20" },
  interim_order: { label: "Interim Order", cls: "bg-warning/10 text-warning border-warning/20" },
  observation: { label: "Observation", cls: "bg-muted text-muted-foreground border-border" },
  condition: { label: "Condition", cls: "bg-info/10 text-info border-info/20" },
};

export const VerificationConsole = () => {
  const [selectedId, setSelectedId] = useState(directives[0].id);
  const selected = directives.find((d) => d.id === selectedId)!;

  return (
    <section className="border-b border-border bg-secondary/40 py-20">
      <div className="mx-auto max-w-[1400px] px-6">
        <div className="mb-10 flex items-end justify-between gap-8">
          <div>
            <div className="mb-3 text-[11px] uppercase tracking-[0.2em] text-accent">§ Layer 04 · Verification</div>
            <h2 className="max-w-2xl font-display text-4xl font-500 leading-tight text-ink">
              Side-by-side source highlighting. Per-directive confidence. Audit trail.
            </h2>
          </div>
          <div className="hidden items-center gap-2 rounded-sm border border-border bg-card px-4 py-2 text-xs lg:flex">
            <ShieldCheck className="h-4 w-4 text-success" />
            <span>Reviewer: <span className="font-500">R. Menon</span> · Session #VR-2041</span>
          </div>
        </div>

        <div className="grid gap-px overflow-hidden rounded-sm border border-border bg-border lg:grid-cols-2">
          {/* PDF pane */}
          <div className="bg-card p-6">
            <div className="mb-4 flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2 text-xs">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="font-mono">W.P.(C)_8421_2026.pdf</span>
                <span className="text-muted-foreground">· Page {selected.sourcePage} of 47</span>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
                <Highlighter className="h-3 w-3 text-gold" />
                Source highlight
              </div>
            </div>

            <div className="rounded-sm border border-border bg-[hsl(40,40%,99%)] p-6 font-display text-[13px] leading-[1.9] text-ink shadow-inner">
              <div className="mb-4 text-center text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
                In the High Court of Karnataka at Bengaluru
              </div>
              <div className="mb-2 text-muted-foreground">
                <span className="font-mono text-[11px]">¶ {selected.sourcePage * 1 + 5}.</span> Having heard
                learned counsel for the parties at length and on a careful perusal of the material on record…
              </div>
              <div className="mb-2 text-muted-foreground">
                <span className="font-mono text-[11px]">¶ {selected.sourcePage * 1 + 6}.</span> The contention of
                the respondent that the impugned discharge is within prescribed parameters cannot be sustained…
              </div>

              <div className="my-3 rounded-sm bg-gold/20 px-2 py-2 ring-1 ring-gold/40">
                <span className="font-mono text-[11px] text-accent">{selected.sourceParagraph}.</span>{" "}
                {selected.text}
              </div>

              <div className="mt-2 text-muted-foreground">
                <span className="font-mono text-[11px]">¶ {selected.sourcePage * 1 + 8}.</span> Liberty is
                granted to the parties to mention the matter in case any clarification is required.
              </div>
            </div>

            <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground">
              <span>Highlight derived from extraction · OCR confidence 0.99</span>
              <span className="font-mono">{selected.sourceParagraph}</span>
            </div>
          </div>

          {/* Structured form pane */}
          <div className="bg-card p-6">
            <div className="mb-4 flex items-center justify-between border-b border-border pb-3">
              <div className="text-xs uppercase tracking-wider text-muted-foreground">Extracted Directive</div>
              <span className={`rounded-sm border px-2 py-0.5 text-[10px] font-500 uppercase tracking-wider ${sectionMeta[selected.sectionType].cls}`}>
                {sectionMeta[selected.sectionType].label}
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <div className="mb-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">Directive text</div>
                <div className="rounded-sm border border-input bg-background p-3 text-sm leading-relaxed">
                  {selected.text}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Field label="Responsible department" value={selected.department} />
                <Field label="Deadline" value={typeof selected.deadline === "string" && selected.deadline.includes("-") ? new Date(selected.deadline).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "—"} />
                <Field label="Priority" value={selected.priority} mono />
                <Field label="Appeal route" value={selected.appealRoute.replace("_", " ")} mono />
              </div>

              <div className="rounded-sm border border-border bg-secondary/60 p-3">
                <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
                  <span>Confidence score</span>
                  <span className="font-mono text-foreground">{(selected.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-border">
                  <div
                    className={`h-full ${
                      selected.confidence > 0.9 ? "bg-success" : selected.confidence > 0.8 ? "bg-warning" : "bg-destructive"
                    }`}
                    style={{ width: `${selected.confidence * 100}%` }}
                  />
                </div>
                {selected.confidence < 0.9 && (
                  <div className="mt-2 flex items-start gap-1.5 text-[11px] text-warning">
                    <AlertTriangle className="mt-0.5 h-3 w-3" />
                    Below 90% — reviewer attention recommended.
                  </div>
                )}
              </div>

              {selected.dependsOn && (
                <div className="rounded-sm border border-dashed border-info/40 bg-info/5 p-3 text-xs">
                  <span className="font-500 text-info">Dependency:</span> blocks until{" "}
                  <span className="font-mono">{selected.dependsOn}</span> reaches{" "}
                  <span className="font-mono">complied</span>.
                </div>
              )}

              <div className="flex items-center gap-2 pt-2">
                <button className="inline-flex items-center gap-1.5 rounded-sm bg-success px-4 py-2 text-sm font-500 text-success-foreground hover:opacity-90">
                  <Check className="h-4 w-4" /> Approve
                </button>
                <button className="inline-flex items-center gap-1.5 rounded-sm border border-input bg-card px-4 py-2 text-sm font-500 hover:bg-secondary">
                  <Edit3 className="h-4 w-4" /> Edit
                </button>
                <button className="inline-flex items-center gap-1.5 rounded-sm border border-input bg-card px-4 py-2 text-sm font-500 text-destructive hover:bg-destructive/10">
                  <X className="h-4 w-4" /> Reject
                </button>
                <div className="ml-auto text-[11px] text-muted-foreground">
                  Audit · v3 · last edit by R. Menon
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* directive list */}
        <div className="mt-6 grid gap-2 lg:grid-cols-3">
          {directives.slice(0, 6).map((d) => (
            <button
              key={d.id}
              onClick={() => setSelectedId(d.id)}
              className={`rounded-sm border bg-card px-4 py-3 text-left transition-all ${
                d.id === selectedId ? "border-primary shadow-paper" : "border-border hover:border-primary/40"
              }`}
            >
              <div className="flex items-center justify-between text-[10px] uppercase tracking-wider">
                <span className={`rounded-sm border px-1.5 py-0.5 ${sectionMeta[d.sectionType].cls}`}>
                  {sectionMeta[d.sectionType].label}
                </span>
                <span className="font-mono text-muted-foreground">{d.id}</span>
              </div>
              <div className="mt-2 line-clamp-2 text-xs text-foreground">{d.text}</div>
              <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
                <span>{d.department}</span>
                <span className="font-mono">{(d.confidence * 100).toFixed(0)}%</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
};

const Field = ({ label, value, mono }: { label: string; value: string; mono?: boolean }) => (
  <div className="rounded-sm border border-input bg-background p-3">
    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
    <div className={`mt-1 text-sm capitalize ${mono ? "font-mono" : ""}`}>{value}</div>
  </div>
);
