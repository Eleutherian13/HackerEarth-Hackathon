/**
 * ActionPlanReview Page
 *
 * Review and manage action plan items generated from court judgment.
 */

import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  CheckCircle,
  Clock,
  AlertTriangle,
  Flag,
  ChevronDown,
  ChevronUp,
  Loader,
} from "lucide-react";
import client from "@/lib/api-client";

interface ActionItem {
  id: string;
  title: string;
  description: string;
  action_type: string;
  priority: string;
  due_date: string;
  responsible_department: string;
  completion_status: string;
  risk_if_ignored: string;
}

export const ActionPlanReview: React.FC = () => {
  const { id: documentId } = useParams<{ id: string }>();
  const [items, setItems] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>(
    {},
  );

  useEffect(() => {
    const loadActionPlan = async () => {
      try {
        const { data } = await client.get(
          `/api/v1/documents/${documentId}/action-plan`,
        );
        setItems(data.action_items || []);
        setLoading(false);
      } catch (error) {
        console.error("Failed to load action plan:", error);
        setLoading(false);
      }
    };

    if (documentId) {
      loadActionPlan();
    }
  }, [documentId]);

  const toggleExpanded = (itemId: string) => {
    setExpandedItems((prev) => ({
      ...prev,
      [itemId]: !prev[itemId],
    }));
  };

  const handleMarkComplete = async (itemId: string) => {
    try {
      await client.post(`/api/v1/dashboard/actions/${itemId}/mark-complete`);

      setItems(
        items.map((item) =>
          item.id === itemId
            ? { ...item, completion_status: "COMPLETED" }
            : item,
        ),
      );
    } catch (error) {
      console.error("Failed to mark item complete:", error);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "CRITICAL":
        return "bg-red-100 text-red-800 border-red-300";
      case "HIGH":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "MEDIUM":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getTypeColor = (actionType: string) => {
    switch (actionType) {
      case "COMPLIANCE":
        return "bg-blue-100 text-blue-800";
      case "APPEAL_CONSIDERATION":
        return "bg-purple-100 text-purple-800";
      case "INTERNAL_REVIEW":
        return "bg-green-100 text-green-800";
      case "ESCALATION":
        return "bg-red-100 text-red-800";
      case "MONITORING":
        return "bg-indigo-100 text-indigo-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return <CheckCircle className="text-green-600" size={20} />;
      case "IN_PROGRESS":
        return <Clock className="text-blue-600" size={20} />;
      case "OVERDUE":
        return <AlertTriangle className="text-red-600" size={20} />;
      default:
        return <Flag className="text-gray-400" size={20} />;
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
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Action Plan</h1>
          <p className="text-gray-600">
            {items.length} action items identified
          </p>
        </div>

        {/* Items List */}
        <div className="space-y-4">
          {items.map((item) => (
            <div key={item.id} className="bg-white rounded-lg shadow">
              {/* Item Header */}
              <button
                onClick={() => toggleExpanded(item.id)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50"
              >
                <div className="flex items-center gap-4 flex-1 text-left">
                  {getStatusIcon(item.completion_status)}
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">
                      {item.title}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {item.responsible_department}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-semibold px-3 py-1 rounded border ${getPriorityColor(
                        item.priority,
                      )}`}
                    >
                      {item.priority}
                    </span>
                    <span
                      className={`text-xs font-semibold px-3 py-1 rounded ${getTypeColor(item.action_type)}`}
                    >
                      {item.action_type.replace(/_/g, " ")}
                    </span>
                  </div>
                </div>
                {expandedItems[item.id] ? (
                  <ChevronUp className="text-gray-400" size={20} />
                ) : (
                  <ChevronDown className="text-gray-400" size={20} />
                )}
              </button>

              {/* Item Details */}
              {expandedItems[item.id] && (
                <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-semibold text-gray-700 uppercase">
                        Due Date
                      </label>
                      <p className="text-sm text-gray-900 mt-1">
                        {new Date(item.due_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-gray-700 uppercase">
                        Status
                      </label>
                      <p className="text-sm text-gray-900 mt-1">
                        {item.completion_status}
                      </p>
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-gray-700 uppercase">
                      Description
                    </label>
                    <p className="text-sm text-gray-700 mt-1">
                      {item.description}
                    </p>
                  </div>

                  <div className="bg-red-50 border border-red-200 rounded p-4">
                    <label className="text-xs font-semibold text-red-700 uppercase">
                      Risk If Ignored
                    </label>
                    <p className="text-sm text-red-700 mt-1">
                      {item.risk_if_ignored}
                    </p>
                  </div>

                  {item.completion_status !== "COMPLETED" && (
                    <button
                      onClick={() => handleMarkComplete(item.id)}
                      className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
                    >
                      Mark as Complete
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {items.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">
              No action items generated yet
            </p>
            <p className="text-gray-400 text-sm mt-2">
              Please review and approve extracted fields first
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActionPlanReview;
