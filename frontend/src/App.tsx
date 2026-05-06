import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
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
import AdminAccessRequests from "./pages/AdminAccessRequests.tsx";
import NotFound from "./pages/NotFound.tsx";

const queryClient = new QueryClient();

const ProtectedAdminRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem("access_token");
  const role = localStorage.getItem("user_role");
  const isAdmin = role === "SUPERADMIN" || role === "ADMIN";
  if (!token || !isAdmin) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/verification" element={<VerificationPage />} />
          <Route path="/departments" element={<Departments />} />
          <Route path="/audit" element={<AuditTrail />} />
          <Route path="/admin/access-requests" element={<ProtectedAdminRoute><AdminAccessRequests /></ProtectedAdminRoute>} />
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
