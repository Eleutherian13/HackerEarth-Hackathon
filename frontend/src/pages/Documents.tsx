/**
 * Documents List Page
 *
 * List all uploaded documents with status indicators.
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Loader, Eye, FileText } from "lucide-react";
import client from "@/lib/api-client";

interface Document {
  id: string;
  filename: string;
  processing_status: string;
  created_at: string;
  page_count: number;
  extracted_fields_count?: number;
}

export const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const { data } = await client.get("/api/v1/documents");
        setDocuments(data.documents || []);
        setLoading(false);
      } catch (error) {
        console.error("Failed to load documents:", error);
        setLoading(false);
      }
    };

    loadDocuments();
  }, []);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader className="animate-spin text-blue-600" size={40} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Documents</h1>
            <p className="text-gray-600">{documents.length} documents</p>
          </div>
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            <Upload size={20} />
            Upload New
          </button>
        </div>

        {/* Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                  Filename
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                  Pages
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                  Extracted Fields
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                  Uploaded
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm">
                    <div className="flex items-center gap-2">
                      <FileText size={18} className="text-blue-600" />
                      <span className="font-medium text-gray-900">
                        {doc.filename}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(doc.processing_status)}`}
                    >
                      {doc.processing_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {doc.page_count}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {doc.extracted_fields_count || 0}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <button
                      onClick={() => navigate(`/documents/${doc.id}/status`)}
                      className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-600 rounded hover:bg-blue-200 font-medium"
                    >
                      <Eye size={16} />
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {documents.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <FileText size={40} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500 text-lg">No documents uploaded yet</p>
            <button
              onClick={() => navigate("/")}
              className="mt-4 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium"
            >
              Upload a Document
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Documents;
