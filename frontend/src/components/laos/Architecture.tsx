import { layers } from "@/data/laos";
import { ChevronRight } from "lucide-react";
import { useState } from "react";

export const Architecture = () => {
  const [active, setActive] = useState(1);
  const layer = layers[active];

  return (
    <section className="border-b border-border bg-background py-20">
      <div className="mx-auto max-w-[1400px] px-6">
        <div className="mb-12 flex items-end justify-between gap-8">
          <div>
            <div className="mb-3 text-[11px] uppercase tracking-[0.2em] text-accent">§ Architecture</div>
            <h2 className="max-w-2xl font-display text-4xl font-500 leading-tight text-ink">
              Five layers, one mandate: nothing unverified reaches the dashboard.
            </h2>
          </div>
          <p className="hidden max-w-sm text-sm text-muted-foreground lg:block">
            Each layer addresses a blind spot competitors will skip. Click any to inspect.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          <div className="space-y-2">
            {layers.map((l, i) => {
              const isActive = i === active;
              return (
                <button
                  key={l.n}
                  onClick={() => setActive(i)}
                  className={`group flex w-full items-center gap-5 rounded-sm border px-5 py-4 text-left transition-all ${
                    isActive
                      ? "border-primary bg-card shadow-elevated"
                      : "border-border bg-card/60 hover:border-primary/40 hover:bg-card"
                  }`}
                >
                  <div
                    className={`font-display text-2xl font-600 tabular-nums ${
                      isActive ? "text-accent" : "text-muted-foreground"
                    }`}
                  >
                    {l.n}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline gap-3">
                      <span className="font-display text-lg font-600 text-ink">{l.name}</span>
                      {l.highlight && (
                        <span className="rounded-sm bg-accent/10 px-2 py-0.5 text-[10px] font-500 uppercase tracking-wider text-accent">
                          Differentiator
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">{l.role}</div>
                  </div>
                  <div className="hidden text-right text-xs sm:block">
                    <div className="font-mono text-foreground">{l.metric}</div>
                  </div>
                  <ChevronRight
                    className={`h-4 w-4 shrink-0 transition-transform ${
                      isActive ? "translate-x-0 text-accent" : "-translate-x-1 text-muted-foreground"
                    }`}
                  />
                </button>
              );
            })}
          </div>

          <div className="paper-elevated rounded-sm p-8">
            <div className="seal-line mb-6" />
            <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              Layer {layer.n} · Detail
            </div>
            <h3 className="mt-2 font-display text-3xl font-500 text-ink">{layer.name}</h3>
            <p className="mt-4 text-sm leading-relaxed text-foreground/80">{layer.detail}</p>

            <div className="mt-8 grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-border bg-border">
              {[
                { k: "Input", v: layer.role },
                { k: "Status", v: layer.metric },
              ].map((x) => (
                <div key={x.k} className="bg-card p-4">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{x.k}</div>
                  <div className="mt-1 text-sm font-500">{x.v}</div>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-sm bg-secondary/60 p-4 font-mono text-[11px] leading-relaxed text-muted-foreground">
              <span className="text-accent">$</span> laos pipeline trace --layer {layer.n}
              <br />
              <span className="text-success">✓</span> {layer.name.toLowerCase()} ready · ingress/egress contract OK
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
