import { ReactNode } from "react";
import { Header } from "./Header";
import { Footer } from "./Footer";

interface PageLayoutProps {
  eyebrow?: string;
  title: string;
  description?: string;
  children: ReactNode;
}

export const PageLayout = ({ eyebrow, title, description, children }: PageLayoutProps) => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <section className="border-b border-border bg-gradient-parchment">
          <div className="mx-auto max-w-[1400px] px-6 py-12">
            {eyebrow && (
              <div className="mb-3 text-[11px] uppercase tracking-[0.2em] text-accent">{eyebrow}</div>
            )}
            <h1 className="font-display text-4xl font-500 leading-tight text-ink">{title}</h1>
            {description && (
              <p className="mt-3 max-w-2xl text-sm text-muted-foreground">{description}</p>
            )}
          </div>
        </section>
        {children}
      </main>
      <Footer />
    </div>
  );
};
