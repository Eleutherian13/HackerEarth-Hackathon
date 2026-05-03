import { PageLayout } from "@/components/laos/PageLayout";
import { cases } from "@/data/laos";
import { FileText, Filter } from "lucide-react";

const statusCls: Record<string, string> = {
  in_review: "bg-warning/10 text-warning",
  active: "bg-success/10 text-success",
  closed: "bg-muted text-muted-foreground",
  ingested: "bg-info/10 text-info",
  classified: "bg-primary/10 text-primary",
};

const priorityCls: Record<string, string> = {
  critical: "bg-destructive/10 text-destructive",
  high: "bg-warning/10 text-warning",
  medium: "bg-info/10 text-info",
  low: "bg-muted text-muted-foreground",
};

const Cases = () => {
  return (
    <PageLayout
      eyebrow="§ Case Registry"
      title="All cases under orchestration."
      description="Every judgment ingested by LAOS. Filter by court, bench, status, or priority."
    >
      <section className="py-12">
        <div className="mx-auto max-w-[1400px] px-6">
          <div className="mb-6 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Filter className="h-4 w-4" />
              {cases.length} cases · live registry
            </div>
            <div className="flex gap-2">
              {["All", "Critical", "Active", "Closed"].map((f, i) => (
                <button
                  key={f}
                  className={`rounded-sm border px-3 py-1.5 text-xs font-500 ${
                    i === 0
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-input bg-card text-foreground hover:bg-secondary"
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div className="paper rounded-sm">
            <div className="grid grid-cols-12 gap-4 border-b border-border bg-secondary/40 px-5 py-3 text-[10px] uppercase tracking-wider text-muted-foreground">
              <div className="col-span-5">Case</div>
              <div className="col-span-2">Court</div>
              <div className="col-span-1">Priority</div>
              <div className="col-span-2">Judgment</div>
              <div className="col-span-2 text-right">Directives</div>
            </div>
            <div className="divide-y divide-border">
              {cases.map((c) => (
                <div
                  key={c.id}
                  className="grid grid-cols-12 items-center gap-4 px-5 py-4 transition-colors hover:bg-secondary/40"
                >
                  <div className="col-span-5 min-w-0">
                    <div className="flex items-center gap-2">
                      <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="font-mono text-[11px] text-muted-foreground">{c.caseNo}</span>
                      <span
                        className={`rounded-sm px-1.5 py-0.5 text-[10px] font-500 uppercase tracking-wider ${statusCls[c.status]}`}
                      >
                        {c.status.replace("_", " ")}
                      </span>
                    </div>
                    <div className="mt-1 line-clamp-1 font-display text-sm font-600 text-ink">{c.title}</div>
                  </div>
                  <div className="col-span-2 text-xs">
                    <div className="text-foreground">{c.court}</div>
                    <div className="text-muted-foreground">{c.bench}</div>
                  </div>
                  <div className="col-span-1">
                    <span
                      className={`rounded-sm px-1.5 py-0.5 text-[10px] font-500 uppercase tracking-wider ${priorityCls[c.priority]}`}
                    >
                      {c.priority}
                    </span>
                  </div>
                  <div className="col-span-2 font-mono text-xs">
                    {new Date(c.judgmentDate).toLocaleDateString("en-GB")}
                  </div>
                  <div className="col-span-2 text-right text-xs">
                    <span className="font-mono">{c.directives}</span>
                    {c.pending > 0 && <span className="ml-1 text-warning">· {c.pending} pending</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </PageLayout>
  );
};

export default Cases;
