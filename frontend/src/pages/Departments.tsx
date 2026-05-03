import { PageLayout } from "@/components/laos/PageLayout";
import { directives } from "@/data/laos";
import { Building2, Clock, AlertCircle } from "lucide-react";

const Departments = () => {
  const grouped = directives.reduce<Record<string, typeof directives>>((acc, d) => {
    if (d.department === "—") return acc;
    (acc[d.department] ||= []).push(d);
    return acc;
  }, {});

  return (
    <PageLayout
      eyebrow="§ Department Registry"
      title="Departments engaged."
      description="Every government department currently bound by an active directive."
    >
      <section className="py-12">
        <div className="mx-auto max-w-[1400px] px-6">
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {Object.entries(grouped).map(([dept, items]) => {
              const pending = items.filter((d) => d.status === "pending_review").length;
              const urgent = items.filter((d) => d.daysLeft >= 0 && d.daysLeft <= 14).length;
              return (
                <div key={dept} className="paper rounded-sm p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-9 w-9 items-center justify-center rounded-sm bg-primary/10">
                        <Building2 className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <div className="font-display text-sm font-600 text-ink">{dept}</div>
                        <div className="text-[11px] text-muted-foreground">{items.length} directives</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                    <div className="rounded-sm bg-warning/5 p-2.5">
                      <div className="flex items-center gap-1 text-warning">
                        <Clock className="h-3 w-3" />
                        <span className="text-[10px] uppercase tracking-wider">Pending</span>
                      </div>
                      <div className="mt-1 font-display text-xl font-600 text-ink">{pending}</div>
                    </div>
                    <div className="rounded-sm bg-destructive/5 p-2.5">
                      <div className="flex items-center gap-1 text-destructive">
                        <AlertCircle className="h-3 w-3" />
                        <span className="text-[10px] uppercase tracking-wider">≤ 14d</span>
                      </div>
                      <div className="mt-1 font-display text-xl font-600 text-ink">{urgent}</div>
                    </div>
                  </div>

                  <div className="mt-4 space-y-1.5 border-t border-border pt-3">
                    {items.slice(0, 3).map((d) => (
                      <div key={d.id} className="flex items-center justify-between text-[11px]">
                        <span className="line-clamp-1 text-muted-foreground">{d.text}</span>
                        <span className="ml-2 font-mono text-foreground">{d.daysLeft >= 0 ? `${d.daysLeft}d` : "—"}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </PageLayout>
  );
};

export default Departments;
