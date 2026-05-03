import { Scale } from "lucide-react";

export const Footer = () => (
  <footer className="bg-background py-10">
    <div className="mx-auto flex max-w-[1400px] flex-col items-start justify-between gap-6 px-6 md:flex-row md:items-center">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-sm bg-gradient-judicial">
          <Scale className="h-4 w-4 text-primary-foreground" strokeWidth={1.5} />
        </div>
        <div className="text-xs">
          <div className="font-display text-sm font-600 text-ink">LAOS</div>
          <div className="text-muted-foreground">Legal Action Orchestration System · v0.9 (Pilot)</div>
        </div>
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted-foreground">
        <span>Stack: FastAPI · pdfplumber · Tesseract · PostgreSQL</span>
        <span>·</span>
        <span>SOC2-aligned · Air-gapped deployable</span>
      </div>
    </div>
  </footer>
);
