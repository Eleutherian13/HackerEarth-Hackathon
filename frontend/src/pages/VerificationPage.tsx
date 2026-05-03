import { PageLayout } from "@/components/laos/PageLayout";
import { VerificationConsole } from "@/components/laos/VerificationConsole";

const VerificationPage = () => (
  <PageLayout
    eyebrow="§ Layer 04 · Verification"
    title="Verification Console."
    description="Review every extracted directive against its source paragraph before it enters the compliance dashboard."
  >
    <VerificationConsole />
  </PageLayout>
);

export default VerificationPage;
