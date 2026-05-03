import { Header } from "@/components/laos/Header";
import { Hero } from "@/components/laos/Hero";
import { Architecture } from "@/components/laos/Architecture";
import { VerificationConsole } from "@/components/laos/VerificationConsole";
import { JudgmentDNA } from "@/components/laos/JudgmentDNA";
import { Dashboard } from "@/components/laos/Dashboard";
import { Footer } from "@/components/laos/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <Hero />
        <Architecture />
        <VerificationConsole />
        <JudgmentDNA />
        <Dashboard />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
