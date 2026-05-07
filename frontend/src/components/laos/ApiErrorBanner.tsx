import { AlertTriangle } from "lucide-react";
import { API_BASE_URL } from "@/lib/api-config";

export const ApiErrorBanner = ({ error }: { error: string }) => (
  <div className="flex items-start gap-3 rounded-sm border border-warning/40 bg-warning/5 p-4 text-xs">
    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
    <div>
      <div className="font-500 text-warning">Backend unreachable</div>
      <div className="mt-1 text-muted-foreground">{error}</div>
      <div className="mt-1 font-mono text-[11px] text-muted-foreground">
        API: {API_BASE_URL}
      </div>
    </div>
  </div>
);
