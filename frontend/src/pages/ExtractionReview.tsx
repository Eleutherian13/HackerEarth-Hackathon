/**
 * ExtractionReview Page
 *
 * Three-panel layout for reviewing extracted fields:
 * - LEFT: List of extracted fields grouped by category
 * - CENTER: PDF page with highlight overlays
 * - RIGHT: Source evidence and action buttons
 */

import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  Check,
  X,
  Edit2,
  Flag,
  ChevronDown,
  ChevronUp,
  Loader,
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff,
} from "lucide-react";
import client from "@/lib/api-client";
import PDFHighlightViewer from "../components/Review/PDFHighlightViewer";

interface ExtractedField {
  id: string;
  field_type: string;
  value: string;
  confidence_score: number;
  source_quotes: any[];
  verification_status: string;
  version: number;
  verified_at?: string;
  reviewer_comments?: string;
}

interface FieldCategory {
  name: string;
  icon: string;
  fields: ExtractedField[];
  color: string;
}

export const ExtractionReview: React.FC = () => {
  const { id: documentId } = useParams<{ id: string }>();
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedField, setSelectedField] = useState<ExtractedField | null>(
    null,
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [expandedCategories, setExpandedCategories] = useState<
    Record<string, boolean>
  >({});
  const [editingValue, setEditingValue] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: string;
    message: string;
  } | null>(null);

  // Load extracted fields
  useEffect(() => {
    const loadFields = async () => {
      setLoading(true);
      try {
        const { data } = await client.get(
          `/api/v1/documents/${documentId}/extractions`,
        );
        setFields(data.fields || []);

        // Set initial document metadata
        if (data.fields && data.fields.length > 0) {
          const { data: docData } = await client.get(
            `/api/v1/documents/${documentId}`,
          );
          setTotalPages(docData.page_count || 1);
        }

        setLoading(false);
      } catch (error) {
        console.error("Failed to load extractions:", error);
        setLoading(false);
      }
    };

    if (documentId) {
      loadFields();
    }
  }, [documentId]);

  // Group fields by category
  const categorizedFields: Record<string, ExtractedField[]> = {};
  fields.forEach((field) => {
    const category = field.field_type.replace(/_/g, " ");
    if (!categorizedFields[category]) {
      categorizedFields[category] = [];
    }
    categorizedFields[category].push(field);
  });

  const handleApprove = async () => {
    if (!selectedField) return;

    setSubmitting(true);
    try {
      const response = await fetch(
        `/api/v1/review/fields/${selectedField.id}/verify`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "APPROVE",
            expected_version: selectedField.version,
            comments: "",
          }),
        },
      );

      if (response.ok) {
        // Update field status
        setFields(
          fields.map((f) =>
            f.id === selectedField.id
              ? { ...f, verification_status: "APPROVED" }
              : f,
          ),
        );
        setSelectedField({ ...selectedField, verification_status: "APPROVED" });
        setFeedback({
          type: "success",
          message: "Field approved successfully",
        });
      } else {
        setFeedback({ type: "error", message: "Failed to approve field" });
      }
    } catch (error) {
      setFeedback({ type: "error", message: "Error approving field" });
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = async (newValue: string) => {
    if (!selectedField) return;

    setSubmitting(true);
    try {
      const response = await fetch(
        `/api/v1/review/fields/${selectedField.id}/verify`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "EDIT",
            expected_version: selectedField.version,
            edited_value: newValue,
            edit_reason: "User correction",
          }),
        },
      );

      if (response.ok) {
        setFields(
          fields.map((f) =>
            f.id === selectedField.id
              ? { ...f, value: newValue, verification_status: "EDITED" }
              : f,
          ),
        );
        setSelectedField({
          ...selectedField,
          value: newValue,
          verification_status: "EDITED",
        });
        setEditingValue(null);
        setFeedback({ type: "success", message: "Field updated successfully" });
      }
    } catch (error) {
      setFeedback({ type: "error", message: "Failed to update field" });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!selectedField) return;

    setSubmitting(true);
    try {
      const response = await fetch(
        `/api/v1/review/fields/${selectedField.id}/verify`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "REJECT",
            expected_version: selectedField.version,
          }),
        },
      );

      if (response.ok) {
        setFields(
          fields.map((f) =>
            f.id === selectedField.id
              ? { ...f, verification_status: "REJECTED" }
              : f,
          ),
        );
        setFeedback({ type: "success", message: "Field rejected" });
      }
    } catch (error) {
      setFeedback({ type: "error", message: "Failed to reject field" });
    } finally {
      setSubmitting(false);
    }
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [category]: !prev[category],
    }));
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.85) return "bg-green-100 text-green-800";
    if (confidence >= 0.7) return "bg-yellow-100 text-yellow-800";
    return "bg-orange-100 text-orange-800";
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "APPROVED":
        return <CheckCircle className="text-green-600" size={16} />;
      case "EDITED":
        return <Edit2 className="text-blue-600" size={16} />;
      case "REJECTED":
        return <X className="text-red-600" size={16} />;
      default:
        return <AlertCircle className="text-gray-400" size={16} />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <Loader className="animate-spin text-blue-600" size={40} />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* LEFT PANEL: Field List */}
      <div className="w-80 border-r border-gray-200 bg-white overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-semibold text-lg text-gray-900">
            Extracted Fields
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {fields.length} fields found
          </p>
        </div>

        <div className="divide-y divide-gray-200">
          {Object.entries(categorizedFields).map(
            ([category, categoryFields]) => (
              <div key={category} className="border-b border-gray-200">
                <button
                  onClick={() => toggleCategory(category)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 font-medium text-sm text-gray-700"
                >
                  <span>{category}</span>
                  {expandedCategories[category] ? (
                    <ChevronUp size={16} />
                  ) : (
                    <ChevronDown size={16} />
                  )}
                </button>

                {expandedCategories[category] && (
                  <div className="bg-gray-50 divide-y divide-gray-200">
                    {categoryFields.map((field) => (
                      <button
                        key={field.id}
                        onClick={() => setSelectedField(field)}
                        className={`w-full px-4 py-3 text-left text-sm hover:bg-blue-50 ${
                          selectedField?.id === field.id ? "bg-blue-100" : ""
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          {getStatusIcon(field.verification_status)}
                          <span className="font-medium text-gray-900 truncate">
                            {field.value.substring(0, 40)}
                            {field.value.length > 40 ? "..." : ""}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span
                            className={`text-xs px-2 py-1 rounded ${getConfidenceColor(
                              field.confidence_score,
                            )}`}
                          >
                            {(field.confidence_score * 100).toFixed(0)}%
                          </span>
                          <span className="text-xs text-gray-500">
                            {field.verification_status}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ),
          )}
        </div>
      </div>

      {/* CENTER PANEL: PDF Viewer */}
      <div className="flex-1 p-4 overflow-hidden">
        {selectedField && (
          <PDFHighlightViewer
            documentId={documentId || ""}
            pageNumber={currentPage}
            totalPages={totalPages}
            highlights={selectedField.source_quotes.map((quote, idx) => ({
              id: `quote-${idx}`,
              fieldType: selectedField.field_type,
              sourceQuote: quote.quote || "",
              bbox: {
                x: quote.bbox?.x || 0,
                y: quote.bbox?.y || 0,
                width: quote.bbox?.width || 100,
                height: quote.bbox?.height || 30,
              },
              color: "#3b82f6",
              confidence: selectedField.confidence_score,
            }))}
            onHighlightClick={(id) => console.log("Clicked highlight:", id)}
            onPageChange={setCurrentPage}
          />
        )}
      </div>

      {/* RIGHT PANEL: Details & Actions */}
      <div className="w-96 border-l border-gray-200 bg-white flex flex-col overflow-hidden">
        {selectedField ? (
          <>
            <div className="p-4 border-b border-gray-200 overflow-y-auto flex-1">
              <h3 className="font-semibold text-lg text-gray-900 mb-4">
                {selectedField.field_type.replace(/_/g, " ")}
              </h3>

              {feedback && (
                <div
                  className={`p-3 rounded-md mb-4 text-sm ${
                    feedback.type === "success"
                      ? "bg-green-50 text-green-800"
                      : "bg-red-50 text-red-800"
                  }`}
                >
                  {feedback.message}
                </div>
              )}

              <div className="space-y-4">
                {/* Current Value */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-2">
                    Extracted Value
                  </label>
                  {editingValue !== null ? (
                    <textarea
                      value={editingValue}
                      onChange={(e) => setEditingValue(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded text-sm"
                      rows={3}
                    />
                  ) : (
                    <p className="text-sm text-gray-700 p-2 bg-gray-50 rounded">
                      {selectedField.value}
                    </p>
                  )}
                </div>

                {/* Confidence */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-2">
                    Confidence Score
                  </label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          selectedField.confidence_score >= 0.85
                            ? "bg-green-600"
                            : selectedField.confidence_score >= 0.7
                              ? "bg-yellow-600"
                              : "bg-orange-600"
                        }`}
                        style={{
                          width: `${selectedField.confidence_score * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-sm font-semibold">
                      {(selectedField.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Status */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-2">
                    Status
                  </label>
                  <span
                    className={`inline-block px-3 py-1 rounded text-sm font-medium ${
                      selectedField.verification_status === "APPROVED"
                        ? "bg-green-100 text-green-800"
                        : selectedField.verification_status === "EDITED"
                          ? "bg-blue-100 text-blue-800"
                          : selectedField.verification_status === "REJECTED"
                            ? "bg-red-100 text-red-800"
                            : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {selectedField.verification_status}
                  </span>
                </div>

                {/* Source Evidence */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-2">
                    Source Evidence
                  </label>
                  {selectedField.source_quotes &&
                  selectedField.source_quotes.length > 0 ? (
                    <div className="space-y-2">
                      {selectedField.source_quotes.map((quote, idx) => (
                        <div
                          key={idx}
                          className="p-2 bg-blue-50 border border-blue-200 rounded text-xs text-gray-700"
                        >
                          "{quote.quote || quote}"
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">
                      No source quotes available
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="p-4 border-t border-gray-200 bg-gray-50 space-y-2">
              {selectedField.verification_status === "UNVERIFIED" && (
                <>
                  <button
                    onClick={handleApprove}
                    disabled={submitting}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2 font-medium"
                  >
                    <Check size={18} />
                    Approve
                  </button>

                  <button
                    onClick={() => setEditingValue(selectedField.value)}
                    disabled={submitting || editingValue !== null}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 font-medium"
                  >
                    <Edit2 size={18} />
                    Edit
                  </button>

                  <button
                    onClick={handleReject}
                    disabled={submitting}
                    className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2 font-medium"
                  >
                    <X size={18} />
                    Reject
                  </button>
                </>
              )}

              {editingValue !== null && (
                <>
                  <button
                    onClick={() => handleEdit(editingValue)}
                    disabled={submitting}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 font-medium"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={() => setEditingValue(null)}
                    className="w-full px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 font-medium"
                  >
                    Cancel
                  </button>
                </>
              )}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <Eye size={40} className="mx-auto mb-2 opacity-50" />
              <p>Select a field to review</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExtractionReview;
