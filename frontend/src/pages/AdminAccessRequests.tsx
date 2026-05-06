import { useState, useEffect } from "react";
import { PageLayout } from "@/components/laos/PageLayout";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CheckCircle2, XCircle, Clock, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface AccessRequest {
  id: string;
  email: string;
  full_name: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";
  created_at: string;
}

interface Department {
  id: string;
  name: string;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const AdminAccessRequests = () => {
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDept, setSelectedDept] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    fetchRequests();
    fetchDepartments();
  }, []);

  const getHeaders = () => {
    const token = localStorage.getItem("access_token");
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  };

  const fetchDepartments = async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) return;
      const response = await fetch(`${API_URL}/api/v1/admin/departments`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        const depts = data.items || data.departments || data || [];
        setDepartments(depts);
        if (depts.length > 0) setSelectedDept(depts[0].id);
      }
    } catch {
      // Departments not critical
    }
  };

  const fetchRequests = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const token = localStorage.getItem("access_token");

      if (!token) {
        toast({
          title: "Not authenticated",
          description: "Please log in with an admin account",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      const response = await fetch(
        `${apiUrl}/api/v1/admin/access-requests?status=PENDING`,
        { headers: getHeaders() }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch requests");
      }

      const data = await response.json();
      setRequests(data.items || []);
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to load requests",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (requestId: string) => {
    try {
      setProcessing(requestId);

      if (!selectedDept) {
        toast({
          title: "Error",
          description: "No department selected. Please select a department first.",
          variant: "destructive",
        });
        return;
      }

      const response = await fetch(
        `${API_URL}/api/v1/admin/access-requests/${requestId}/approve`,
        {
          method: "POST",
          headers: getHeaders(),
          body: JSON.stringify({ department_id: selectedDept }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to approve request");
      }

      toast({
        title: "Success",
        description: "Request approved. User account created and email sent.",
      });

      setRequests(requests.filter((r) => r.id !== requestId));
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to approve request",
        variant: "destructive",
      });
    } finally {
      setProcessing(null);
    }
  };

  const handleReject = async (requestId: string) => {
    const reason = prompt("Enter rejection reason:");
    if (!reason) return;

    try {
      setProcessing(requestId);

      const response = await fetch(
        `${API_URL}/api/v1/admin/access-requests/${requestId}/reject`,
        {
          method: "POST",
          headers: getHeaders(),
          body: JSON.stringify({ reason }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to reject request");
      }

      toast({
        title: "Success",
        description: "Request rejected and user notified.",
      });

      setRequests(requests.filter((r) => r.id !== requestId));
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to reject request",
        variant: "destructive",
      });
    } finally {
      setProcessing(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <PageLayout
      eyebrow="§ Administrative Dashboard"
      title="Access Requests"
      description="Review and manage pending officer access requests."
    >
      <section className="py-12">
        <div className="mx-auto max-w-[1400px] px-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <Clock className="h-8 w-8 animate-spin text-muted-foreground mx-auto mb-2" />
                <p className="text-muted-foreground">Loading requests...</p>
              </div>
            </div>
          ) : requests.length === 0 ? (
            <Card className="p-12 text-center border-dashed">
              <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto mb-3" />
              <h3 className="text-lg font-600 text-ink mb-1">All caught up!</h3>
              <p className="text-muted-foreground">No pending access requests at this time.</p>
            </Card>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <AlertCircle className="h-4 w-4" />
                  <span>{requests.length} pending request{requests.length !== 1 ? "s" : ""}</span>
                </div>
                {departments.length > 0 && (
                  <div className="flex items-center gap-2">
                    <label htmlFor="dept" className="text-sm text-muted-foreground">Department:</label>
                    <select
                      id="dept"
                      value={selectedDept}
                      onChange={(e) => setSelectedDept(e.target.value)}
                      className="text-sm border rounded px-2 py-1 bg-card"
                    >
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              <div className="space-y-3">
                {requests.map((request) => (
                  <Card key={request.id} className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-display text-lg font-600 text-ink">
                            {request.full_name}
                          </h3>
                          <span className="text-xs bg-warning/10 text-warning px-2 py-1 rounded">
                            PENDING
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground mb-1">{request.email}</p>
                        <p className="text-xs text-muted-foreground">
                          Requested: {formatDate(request.created_at)}
                        </p>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          onClick={() => handleApprove(request.id)}
                          disabled={processing === request.id}
                          className="gap-2 bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle2 className="h-4 w-4" />
                          Approve
                        </Button>
                        <Button
                          onClick={() => handleReject(request.id)}
                          disabled={processing === request.id}
                          variant="outline"
                          className="gap-2 border-destructive text-destructive hover:bg-destructive/5"
                        >
                          <XCircle className="h-4 w-4" />
                          Reject
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>
    </PageLayout>
  );
};

export default AdminAccessRequests;
