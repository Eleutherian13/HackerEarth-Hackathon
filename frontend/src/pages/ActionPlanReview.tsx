import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Container,
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
} from "@mui/material";
import { Refresh as RefreshIcon } from "@mui/icons-material";
import { useActionPlan } from "../hooks/useActionPlan";
import { useActionPlanReview } from "../hooks/useActionPlanReview";
import SummaryCards from "../components/ActionReview/SummaryCards";
import ActionItemsTable from "../components/ActionReview/ActionItemsTable";
import ActionItemDetail from "../components/ActionReview/ActionItemDetail";
import { ActionPlanItem } from "../hooks/useActionPlan";

const ActionPlanReview: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useActionPlan(id);
  const {
    submitReview,
    editActionItem,
    finalizePlan,
    loading: reviewLoading,
    error: reviewError,
  } = useActionPlanReview(id);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [modifications, setModifications] = useState<
    Record<string, Record<string, string>>
  >({});
  const [rationaleValues, setRationaleValues] = useState<
    Record<string, string>
  >({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [finalizeMessage, setFinalizeMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedItemId && data && data.length > 0) {
      setSelectedItemId(data[0].id);
    }
  }, [data, selectedItemId]);

  const selectedItem = useMemo<ActionPlanItem | undefined>(() => {
    return data?.find((item) => item.id === selectedItemId) ?? data?.[0];
  }, [data, selectedItemId]);

  const handleFieldChange = (
    itemId: string,
    fieldKey: string,
    value: string,
  ) => {
    setModifications((prev) => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        [fieldKey]: value,
      },
    }));
  };

  const handleRationaleChange = (itemId: string, value: string) => {
    setRationaleValues((prev) => ({ ...prev, [itemId]: value }));
  };

  const handleReviewAction = async (
    itemId: string,
    action: "APPROVE" | "REJECT",
  ) => {
    try {
      const requestPayload: any = { action };
      if (action === "REJECT") {
        requestPayload.rationale =
          rationaleValues[itemId] || "Rejected after review.";
      }
      await submitReview(itemId, requestPayload);
      setSuccessMessage(`Action item ${action.toLowerCase()}d successfully.`);
      setFinalizeMessage(null);
      await refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveChanges = async () => {
    if (!selectedItem) {
      return;
    }
    const payload = modifications[selectedItem.id] || {};
    if (Object.keys(payload).length === 0) {
      setSuccessMessage("No changes to save for the selected action item.");
      return;
    }

    try {
      await editActionItem(selectedItem.id, payload);
      setSuccessMessage("Action item saved successfully.");
      setFinalizeMessage(null);
      await refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleFinalize = async () => {
    try {
      const result = await finalizePlan();
      setFinalizeMessage(
        `Plan finalized with ${result.reviewed_action_items} reviewed items.`,
      );
      setSuccessMessage(null);
      await refetch();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading && !data) {
    return (
      <Container
        maxWidth="lg"
        sx={{ py: 4, display: "flex", justifyContent: "center" }}
      >
        <CircularProgress />
      </Container>
    );
  }

  if (error && !data) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
        <Button onClick={() => navigate("/documents")} sx={{ mt: 2 }}>
          Back to Documents
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box
        sx={{
          mb: 4,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Action Plan Review
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Review generated compliance and appeal action items for case{" "}
            {data?.[0]?.document_id || id}.
          </Typography>
        </Box>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
          <Button
            variant="outlined"
            onClick={refetch}
            startIcon={<RefreshIcon />}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handleFinalize}
            disabled={reviewLoading}
          >
            Finalize Plan
          </Button>
        </Box>
      </Box>

      {(reviewError || successMessage || finalizeMessage) && (
        <Box sx={{ mb: 3 }}>
          {reviewError && <Alert severity="error">{reviewError}</Alert>}
          {successMessage && <Alert severity="success">{successMessage}</Alert>}
          {finalizeMessage && (
            <Alert severity="success">{finalizeMessage}</Alert>
          )}
        </Box>
      )}

      {data && data.length > 0 ? (
        <>
          <SummaryCards items={data} />
          <Grid container spacing={3}>
            <Grid item xs={12} lg={7}>
              <ActionItemsTable
                items={data}
                selectedItemId={selectedItem?.id}
                onSelect={(itemId) => setSelectedItemId(itemId)}
              />
            </Grid>
            <Grid item xs={12} lg={5}>
              {selectedItem ? (
                <ActionItemDetail
                  item={selectedItem}
                  modifications={modifications[selectedItem.id] || {}}
                  rationale={rationaleValues[selectedItem.id] || ""}
                  onFieldChange={(fieldKey, value) =>
                    handleFieldChange(selectedItem.id, fieldKey, value)
                  }
                  onReviewAction={handleReviewAction}
                  onSaveChanges={handleSaveChanges}
                  onRationaleChange={(value) =>
                    handleRationaleChange(selectedItem.id, value)
                  }
                  loading={reviewLoading}
                />
              ) : (
                <Alert severity="info">
                  Select an action item to review its details.
                </Alert>
              )}
            </Grid>
          </Grid>
        </>
      ) : (
        <Alert severity="info">
          No action plan items were generated for this document.
        </Alert>
      )}

      <Box sx={{ mt: 4, display: "flex", gap: 2, flexWrap: "wrap" }}>
        <Button
          variant="outlined"
          onClick={() => navigate(`/documents/${id}/status`)}
        >
          Back to Extraction
        </Button>
        <Button variant="contained" onClick={() => navigate("/documents")}>
          Documents List
        </Button>
      </Box>
    </Container>
  );
};

export default ActionPlanReview;
