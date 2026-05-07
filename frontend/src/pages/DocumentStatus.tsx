/**
 * Document Status Page
 *
 * Shows detailed status and available actions for a single document.
 */

import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  FileText,
  CheckCircle,
  Clock,
  AlertTriangle,
  Loader,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import client from "@/lib/api-client";

interface DocumentStatus {
  id: string;
  filename: string;
  processing_status: string;
  page_count: number;
  created_at: string;
  extracted_fields_count?: number;
  verified_fields_count?: number;
  action_items_count?: number;
  error_message?: string;
}

export const DocumentStatus: React.FC = () => {
  const { id: documentId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [document, setDocument] = useState<DocumentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);

  useEffect(() => {
    const loadDocument = async () => {
      try {
        const { data } = await client.get(`/api/v1/documents/${documentId}`);
        setDocument(data);
        setLoading(false);
      } catch (error) {
        console.error("Failed to load document:", error);
        setLoading(false);
      }
    };

    if (documentId) {
      loadDocument();
    }
  }, [documentId]);

  const handleExtract = async () => {
    if (!documentId) return;

    setExtracting(true);
    try {
      const { data } = await client.post(
        `/api/v1/documents/${documentId}/extract`,
      );
      setDocument((prev) =>
        prev ? { ...prev, processing_status: "EXTRACTING" } : null,
      );

      // Poll for completion
      const interval = setInterval(async () => {
        try {
          const { data: checkData } = await client.get(
            `/api/v1/documents/${documentId}`,
          );
          setDocument(checkData);

          if (checkData.processing_status !== "EXTRACTING") {
            clearInterval(interval);
            setExtracting(false);
          }
        } catch (error) {
          console.error("Error polling document status:", error);
        }
      }, 2000);
    } catch (error) {
      console.error("Failed to extract:", error);
      setExtracting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "VERIFIED":
        return <CheckCircle className="text-green-600" size={24} />;
      case "PENDING_REVIEW":
        return <Clock className="text-blue-600" size={24} />;
      case "EXTRACTING":
        return <Loader className="animate-spin text-yellow-600" size={24} />;
      case "FAILED":
        return <AlertTriangle className="text-red-600" size={24} />;
      default:
        return <FileText className="text-gray-600" size={24} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "VERIFIED":
        return "bg-green-100 text-green-800";
      case "PENDING_REVIEW":
        return "bg-blue-100 text-blue-800";
      case "EXTRACTING":
        return "bg-yellow-100 text-yellow-800";
      case "FAILED":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading || !document) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader className="animate-spin text-blue-600" size={40} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate("/documents")}
          className="mb-6 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded font-medium flex items-center gap-2"
        >
          ← Back to Documents
        </button>

        {/* Header */}
        <div className="bg-white rounded-lg shadow p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              {getStatusIcon(document.processing_status)}
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  {document.filename}
                </h1>
                <p className="text-gray-600 mt-1">Document ID: {documentId}</p>
              </div>
            </div>
            <span
              className={`text-lg font-semibold px-4 py-2 rounded-full ${getStatusColor(document.processing_status)}`}
            >
              {document.processing_status}
            </span>
          </div>

          {/* Error Message */}
          {document.error_message && (
            <div className="bg-red-50 border border-red-200 rounded p-4 mb-6">
              <p className="text-red-800 font-medium">Error</p>
              <p className="text-red-700 mt-1">{document.error_message}</p>
            </div>
          )}

          {/* Document Details */}
          <div className="grid grid-cols-4 gap-4">
            <div className="border-l-4 border-blue-600 pl-4">
              <p className="text-sm text-gray-600 uppercase font-semibold">
                Pages
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {document.page_count}
              </p>
            </div>
            <div className="border-l-4 border-green-600 pl-4">
              <p className="text-sm text-gray-600 uppercase font-semibold">
                Extracted Fields
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {document.extracted_fields_count || 0}
              </p>
            </div>
            <div className="border-l-4 border-blue-400 pl-4">
              <p className="text-sm text-gray-600 uppercase font-semibold">
                Verified Fields
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {document.verified_fields_count || 0}
              </p>
            </div>
            <div className="border-l-4 border-purple-600 pl-4">
              <p className="text-sm text-gray-600 uppercase font-semibold">
                Action Items
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {document.action_items_count || 0}
              </p>
            </div>
          </div>

          <p className="text-sm text-gray-500 mt-6">
            Uploaded: {new Date(document.created_at).toLocaleString()}
          </p>
        </div>

        {/* Workflow Progress */}
        <div className="bg-white rounded-lg shadow p-8 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            Processing Workflow
          </h2>
          <div className="space-y-4">
            {/* Step 1: Upload */}
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0">
                <CheckCircle className="text-green-600" size={24} />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-gray-900">Document Uploaded</p>
                <p className="text-sm text-gray-600">
                  PDF processed and stored
                </p>
              </div>
            </div>

            {/* Step 2: Extraction */}
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0">
                {document.extracted_fields_count ? (
                  <CheckCircle className="text-green-600" size={24} />
                ) : (
                  <Clock className="text-gray-400" size={24} />
                )}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-gray-900">Extract Fields</p>
                <p className="text-sm text-gray-600">
                  AI extracts judgment details
                </p>
              </div>
              {!document.extracted_fields_count && (
                <button
                  onClick={handleExtract}
                  disabled={
                    extracting || document.processing_status === "EXTRACTING"
                  }
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 font-medium"
                >
                  {extracting ? (
                    <>
                      <Loader className="animate-spin" size={16} />
                      Extracting...
                    </>
                  ) : (
                    <>
                      <RefreshCw size={16} />
                      Extract
                    </>
                  )}
                </button>
              )}
            </div>

            {/* Step 3: Review */}
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0">
                {document.verified_fields_count ? (
                  <CheckCircle className="text-green-600" size={24} />
                ) : (
                  <Clock className="text-gray-400" size={24} />
                )}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-gray-900">Review & Verify</p>
                <p className="text-sm text-gray-600">
                  Human review and verification
                </p>
              </div>
              {document.extracted_fields_count &&
                !document.verified_fields_count && (
                  <button
                    onClick={() => navigate(`/documents/${documentId}/review`)}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2 font-medium"
                  >
                    Review <ArrowRight size={16} />
                  </button>
                )}
            </div>

            {/* Step 4: Action Plan */}
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0">
                {document.action_items_count ? (
                  <CheckCircle className="text-green-600" size={24} />
                ) : (
                  <Clock className="text-gray-400" size={24} />
                )}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-gray-900">
                  Generate Action Plan
                </p>
                <p className="text-sm text-gray-600">Create actionable items</p>
              </div>
              {document.verified_fields_count &&
                !document.action_items_count && (
                  <button
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center gap-2 font-medium"
                    onClick={() => {
                      // Trigger action plan generation
                      fetch(
                        `/api/v1/review/documents/${documentId}/generate-action-plan`,
                        {
                          method: "POST",
                        },
                      );
                    }}
                  >
                    Generate <ArrowRight size={16} />
                  </button>
                )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          {document.extracted_fields_count && (
            <button
              onClick={() => navigate(`/documents/${documentId}/review`)}
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold"
            >
              Review Extractions
            </button>
          )}
          {document.action_items_count && (
            <button
              onClick={() => navigate(`/documents/${documentId}/action-plan`)}
              className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
            >
              View Action Plan
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentStatus;
