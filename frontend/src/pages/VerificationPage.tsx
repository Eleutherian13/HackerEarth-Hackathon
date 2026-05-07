import { PageLayout } from "@/components/laos/PageLayout";
import { VerificationConsole } from "@/components/laos/VerificationConsole";
import { ApiErrorBanner } from "@/components/laos/ApiErrorBanner";
import { documentsApi } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Check, X, Edit3, FileText, Loader2 } from "lucide-react";
import { useParams } from "react-router-dom";
import { useState } from "react";
import type { ExtractedFieldResponse } from "@/types/laos-api";

const VerificationPage = () => {
  const { id } = useParams<{ id: string }>();

  // No id → keep the original demo console (mock data) so marketing flow still works.
  if (!id) {
    return (
      <PageLayout
        eyebrow="§ Layer 04 · Verification"
        title="Verification Console."
        description="Review every extracted directive against its source paragraph before it enters the compliance dashboard."
      >
        <VerificationConsole />
      </PageLayout>
    );
  }

  return <LiveVerification id={id} />;
};

const LiveVerification = ({ id }: { id: string }) => {
  const doc = useApi(() => documentsApi.get(id), [id]);
  const fields = useApi(() => documentsApi.fields(id), [id]);
  const [busy, setBusy] = useState<string | null>(null);

  const review = async (
    f: ExtractedFieldResponse,
    status: "approved" | "rejected" | "edited",
    value?: string
  ) => {
    setBusy(f.id);
    try {
      await documentsApi.reviewField(id, {
        field_id: f.id,
        status,
        field_value: value,
      });
      await fields.refetch();
    } finally {
      setBusy(null);
    }
  };

  const finalize = async () => {
    await documentsApi.finalizeReview(id);
    await doc.refetch();
  };

  return (
    <PageLayout
      eyebrow={`§ Document · ${id.slice(0, 8)}`}
      title={doc.data?.original_filename ?? doc.data?.filename ?? "Verification"}
      description={
        doc.data
          ? `${doc.data.case_number ?? "Unknown case"} · ${doc.data.court ?? ""} · status ${doc.data.status}`
          : "Loading document…"
      }
    >
      <section className="py-10">
        <div className="mx-auto max-w-[1400px] space-y-6 px-6">
          {(doc.error || fields.error) && (
            <ApiErrorBanner error={doc.error ?? fields.error ?? ""} />
          )}

          {(doc.loading || fields.loading) && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading…
            </div>
          )}

          {fields.data && (
            <>
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground">
                  {fields.data.length} extracted fields ·{" "}
                  {fields.data.filter((f) => f.status === "pending").length} pending
                </div>
                <button
                  onClick={finalize}
                  disabled={fields.data.some((f) => f.status === "pending")}
                  className="rounded-sm bg-success px-4 py-2 text-sm font-500 text-success-foreground disabled:opacity-50"
                >
                  Finalize Review
                </button>
              </div>

              <div className="grid gap-3">
                {fields.data.map((f) => (
                  <div key={f.id} className="paper rounded-sm p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-muted-foreground">
                          <FileText className="h-3 w-3" />
                          {f.field_name}
                          {f.source_page && (
                            <span className="font-mono">· p.{f.source_page}</span>
                          )}
                          <span
                            className={`rounded-sm px-1.5 py-0.5 text-[10px] font-500 ${
                              f.status === "approved"
                                ? "bg-success/10 text-success"
                                : f.status === "rejected"
                                  ? "bg-destructive/10 text-destructive"
                                  : f.status === "edited"
                                    ? "bg-info/10 text-info"
                                    : "bg-warning/10 text-warning"
                            }`}
                          >
                            {f.status}
                          </span>
                        </div>
                        <div className="mt-2 text-sm text-foreground">{f.field_value}</div>
                        <div className="mt-2 text-[11px] text-muted-foreground">
                          Confidence{" "}
                          <span className="font-mono">
                            {(f.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        <button
                          disabled={busy === f.id}
                          onClick={() => review(f, "approved")}
                          className="inline-flex items-center gap-1.5 rounded-sm bg-success px-3 py-1.5 text-xs font-500 text-success-foreground hover:opacity-90 disabled:opacity-50"
                        >
                          <Check className="h-3 w-3" /> Approve
                        </button>
                        <button
                          disabled={busy === f.id}
                          onClick={() => {
                            const v = prompt("Edit field value", f.field_value);
                            if (v != null) review(f, "edited", v);
                          }}
                          className="inline-flex items-center gap-1.5 rounded-sm border border-input bg-card px-3 py-1.5 text-xs font-500 hover:bg-secondary disabled:opacity-50"
                        >
                          <Edit3 className="h-3 w-3" /> Edit
                        </button>
                        <button
                          disabled={busy === f.id}
                          onClick={() => review(f, "rejected")}
                          className="inline-flex items-center gap-1.5 rounded-sm border border-input bg-card px-3 py-1.5 text-xs font-500 text-destructive hover:bg-destructive/10 disabled:opacity-50"
                        >
                          <X className="h-3 w-3" /> Reject
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

export default VerificationPage;
