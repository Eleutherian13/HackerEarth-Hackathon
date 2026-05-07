import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Index from "./pages/Index.tsx";
import Cases from "./pages/Cases.tsx";
import VerificationPage from "./pages/VerificationPage.tsx";
import Departments from "./pages/Departments.tsx";
import AuditTrail from "./pages/AuditTrail.tsx";
import Login from "./pages/Login.tsx";
import Signup from "./pages/Signup.tsx";
import Upload from "./pages/Upload.tsx";
import ActionPlan from "./pages/ActionPlan.tsx";
import NotFound from "./pages/NotFound.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/verification" element={<VerificationPage />} />
          <Route path="/verification/:id" element={<VerificationPage />} />
          <Route path="/action-plan" element={<ActionPlan />} />
          <Route path="/action-plan/:id" element={<ActionPlan />} />
          <Route path="/departments" element={<Departments />} />
          <Route path="/audit" element={<AuditTrail />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
