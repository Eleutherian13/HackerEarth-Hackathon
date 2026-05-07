import { PageLayout } from "@/components/laos/PageLayout";
import { ApiErrorBanner } from "@/components/laos/ApiErrorBanner";
import { actionPlanApi } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Loader2, Check, X, AlertTriangle } from "lucide-react";
import { useParams } from "react-router-dom";
import { useState } from "react";
import type { ActionStatus } from "@/types/laos-api";

const priorityCls: Record<string, string> = {
  critical: "bg-destructive/10 text-destructive",
  high: "bg-warning/10 text-warning",
  medium: "bg-info/10 text-info",
  low: "bg-muted text-muted-foreground",
};

const ActionPlanPage = () => {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return (
      <PageLayout
        eyebrow="§ Action Plan"
        title="Action Plan."
        description="Open a case to view its directive-level action plan."
      >
        <section className="py-12">
          <div className="mx-auto max-w-3xl px-6 text-sm text-muted-foreground">
            Pass a document id in the URL: <code>/action-plan/&lt;document_id&gt;</code>
          </div>
        </section>
      </PageLayout>
    );
  }

  return <LivePlan id={id} />;
};

const LivePlan = ({ id }: { id: string }) => {
  const items = useApi(() => actionPlanApi.list(id), [id]);
  const [busy, setBusy] = useState<string | null>(null);

  const review = async (action_id: string, status: ActionStatus) => {
    setBusy(action_id);
    try {
      await actionPlanApi.review(id, { action_id, status });
      await items.refetch();
    } finally {
      setBusy(null);
    }
  };

  return (
    <PageLayout
      eyebrow={`§ Action Plan · ${id.slice(0, 8)}`}
      title="Directive-level Action Plan."
      description="Each directive becomes a tracked task with department, deadline and dependency."
    >
      <section className="py-10">
        <div className="mx-auto max-w-[1400px] space-y-6 px-6">
          {items.error && <ApiErrorBanner error={items.error} />}
          {items.loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading action plan…
            </div>
          )}

          {items.data && (
            <>
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground">
                  {items.data.length} actions ·{" "}
                  {items.data.filter((a) => a.status === "pending_review").length} pending review
                </div>
                <button
                  onClick={() => actionPlanApi.finalize(id).then(() => items.refetch())}
                  className="rounded-sm bg-primary px-4 py-2 text-sm font-500 text-primary-foreground hover:bg-primary/90"
                >
                  Finalize Plan
                </button>
              </div>

              <div className="grid gap-3">
                {items.data.map((a) => (
                  <div key={a.id} className="paper rounded-sm p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-wider">
                          <span className={`rounded-sm px-1.5 py-0.5 font-500 ${priorityCls[a.priority]}`}>
                            {a.priority}
                          </span>
                          <span className="text-muted-foreground">
                            {a.department ?? "Unassigned"}
                          </span>
                          {a.deadline && (
                            <span className="font-mono text-muted-foreground">
                              · due {new Date(a.deadline).toLocaleDateString("en-GB")}
                            </span>
                          )}
                          <span className="rounded-sm bg-secondary px-1.5 py-0.5 text-muted-foreground">
                            {a.status.replace("_", " ")}
                          </span>
                        </div>
                        <div className="mt-2 text-sm leading-relaxed text-foreground">
                          {a.directive_text}
                        </div>
                        {a.depends_on && (
                          <div className="mt-2 inline-flex items-center gap-1 text-[11px] text-info">
                            <AlertTriangle className="h-3 w-3" /> blocks until{" "}
                            <span className="font-mono">{a.depends_on}</span> complies
                          </div>
                        )}
                      </div>
                      <div className="flex shrink-0 flex-col gap-1.5">
                        <button
                          disabled={busy === a.id}
                          onClick={() => review(a.id, "approved")}
                          className="inline-flex items-center gap-1.5 rounded-sm bg-success px-3 py-1.5 text-xs font-500 text-success-foreground hover:opacity-90 disabled:opacity-50"
                        >
                          <Check className="h-3 w-3" /> Approve
                        </button>
                        <button
                          disabled={busy === a.id}
                          onClick={() => review(a.id, "complied")}
                          className="inline-flex items-center gap-1.5 rounded-sm border border-input bg-card px-3 py-1.5 text-xs font-500 hover:bg-secondary disabled:opacity-50"
                        >
                          Mark Complied
                        </button>
                        <button
                          disabled={busy === a.id}
                          onClick={() => review(a.id, "escalated")}
                          className="inline-flex items-center gap-1.5 rounded-sm border border-input bg-card px-3 py-1.5 text-xs font-500 text-destructive hover:bg-destructive/10 disabled:opacity-50"
                        >
                          <X className="h-3 w-3" /> Escalate
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </section>
    </PageLayout>
  );
};

export default ActionPlanPage;
