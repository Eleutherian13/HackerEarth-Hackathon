import { PageLayout } from "@/components/laos/PageLayout";
import { ApiErrorBanner } from "@/components/laos/ApiErrorBanner";
import { documentsApi } from "@/lib/api";
import { ApiError } from "@/lib/api";
import { Upload as UploadIcon, FileText, CheckCircle2, X } from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

const UploadPage = () => {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const onPick = (f: File | null) => {
    setError(null);
    setDone(null);
    setProgress(0);
    setFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const doc = await documentsApi.upload(file, setProgress);
      setDone(doc.id);
      setTimeout(() => navigate(`/verification/${doc.id}`), 800);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setError("Authentication required. Please sign in and try again.");
        setTimeout(() => navigate("/login"), 600);
        return;
      }
      setError(
        e instanceof ApiError
          ? `${e.message} (${e.status || "network"})`
          : String(e),
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <PageLayout
      eyebrow="§ Layer 01 · Ingestion"
      title="Upload Judgment."
      description="Submit a court judgment PDF. LAOS will classify, OCR if needed, and extract directives for review."
    >
      <section className="py-12">
        <div className="mx-auto max-w-3xl px-6">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files?.[0];
              if (f) onPick(f);
            }}
            onClick={() => inputRef.current?.click()}
            className="paper flex cursor-pointer flex-col items-center justify-center rounded-sm border-2 border-dashed border-border p-12 text-center transition-colors hover:border-primary/40 hover:bg-secondary/30"
          >
            <div className="flex h-14 w-14 items-center justify-center rounded-sm bg-gradient-judicial shadow-paper">
              <UploadIcon
                className="h-6 w-6 text-primary-foreground"
                strokeWidth={1.5}
              />
            </div>
            <div className="mt-4 font-display text-xl font-600 text-ink">
              Drop a PDF, or click to browse
            </div>
            <div className="mt-1 text-xs text-muted-foreground">
              Digital or scanned · up to 100MB · processing typically 4–60s
            </div>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => onPick(e.target.files?.[0] ?? null)}
            />
          </div>

          {file && (
            <div className="mt-6 paper rounded-sm p-5">
              <div className="flex items-start gap-3">
                <FileText className="mt-0.5 h-5 w-5 text-primary" />
                <div className="min-w-0 flex-1">
                  <div className="truncate font-500">{file.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                  {(uploading || progress > 0) && (
                    <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-border">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  )}
                </div>
                <button
                  onClick={() => onPick(null)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {done && (
                <div className="mt-4 flex items-center gap-2 text-sm text-success">
                  <CheckCircle2 className="h-4 w-4" /> Uploaded · routing to
                  verification…
                </div>
              )}

              <div className="mt-4 flex items-center justify-end gap-2">
                <button
                  onClick={handleUpload}
                  disabled={uploading || !!done}
                  className="inline-flex items-center gap-2 rounded-sm bg-primary px-4 py-2 text-sm font-500 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  <UploadIcon className="h-4 w-4" />
                  {uploading
                    ? `Uploading… ${progress.toFixed(0)}%`
                    : "Submit for ingestion"}
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-6">
              <ApiErrorBanner error={error} />
            </div>
          )}
        </div>
      </section>
    </PageLayout>
  );
};

export default UploadPage;
