/**
 * Dashboard Page
 *
 * Main dashboard showing action plan metrics and overview.
 */

import React, { useState, useEffect } from "react";
import { AlertTriangle, CheckCircle, Clock, TrendingUp } from "lucide-react";
import client from "@/lib/api-client";

interface DashboardMetrics {
  total_actions: number;
  by_priority: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  status: {
    overdue: number;
    due_this_week: number;
    completed: number;
    in_progress: number;
  };
  completion_rate_percent: number;
}

export const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const { data } = await client.get("/api/v1/dashboard/summary");
        setMetrics(data.metrics);
        setLoading(false);
      } catch (error) {
        console.error("Failed to load dashboard metrics:", error);
        setLoading(false);
      }
    };

    loadMetrics();
  }, []);

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-gray-600">Court judgment action plan overview</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Total Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-gray-600 font-medium">Total Actions</span>
              <TrendingUp className="text-blue-600" size={24} />
            </div>
            <div className="text-4xl font-bold text-gray-900">
              {metrics.total_actions}
            </div>
            <p className="text-sm text-gray-500 mt-2">Active action items</p>
          </div>

          {/* Completion Rate */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-gray-600 font-medium">Completion Rate</span>
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div className="text-4xl font-bold text-gray-900">
              {metrics.completion_rate_percent.toFixed(1)}%
            </div>
            <p className="text-sm text-gray-500 mt-2">
              {metrics.status.completed} completed
            </p>
          </div>

          {/* Critical Items */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-gray-600 font-medium">Critical Items</span>
              <AlertTriangle className="text-red-600" size={24} />
            </div>
            <div className="text-4xl font-bold text-gray-900">
              {metrics.by_priority.critical}
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Require immediate action
            </p>
          </div>

          {/* Overdue */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-gray-600 font-medium">Overdue</span>
              <Clock className="text-orange-600" size={24} />
            </div>
            <div className="text-4xl font-bold text-gray-900">
              {metrics.status.overdue}
            </div>
            <p className="text-sm text-gray-500 mt-2">Past due date</p>
          </div>
        </div>

        {/* Priority Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold text-gray-900 mb-4">
              Priority Breakdown
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-600"></div>
                  <span className="text-gray-700">Critical</span>
                </div>
                <span className="font-semibold text-gray-900">
                  {metrics.by_priority.critical}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-orange-600"></div>
                  <span className="text-gray-700">High</span>
                </div>
                <span className="font-semibold text-gray-900">
                  {metrics.by_priority.high}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-600"></div>
                  <span className="text-gray-700">Medium</span>
                </div>
                <span className="font-semibold text-gray-900">
                  {metrics.by_priority.medium}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gray-600"></div>
                  <span className="text-gray-700">Low</span>
                </div>
                <span className="font-semibold text-gray-900">
                  {metrics.by_priority.low}
                </span>
              </div>
            </div>
          </div>

          {/* Status Breakdown */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold text-gray-900 mb-4">
              Status Breakdown
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Completed</span>
                <span className="font-semibold text-green-600">
                  {metrics.status.completed}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-700">In Progress</span>
                <span className="font-semibold text-blue-600">
                  {metrics.status.in_progress}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Due This Week</span>
                <span className="font-semibold text-orange-600">
                  {metrics.status.due_this_week}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Overdue</span>
                <span className="font-semibold text-red-600">
                  {metrics.status.overdue}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Quick Links</h3>
            <div className="space-y-2">
              <a
                href="/documents"
                className="block px-4 py-2 bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
              >
                View Documents
              </a>
              <a
                href="/cases"
                className="block px-4 py-2 bg-green-50 text-green-600 rounded hover:bg-green-100"
              >
                View Cases
              </a>
              <a
                href="/departments"
                className="block px-4 py-2 bg-purple-50 text-purple-600 rounded hover:bg-purple-100"
              >
                View Departments
              </a>
              <a
                href="/audit"
                className="block px-4 py-2 bg-gray-50 text-gray-600 rounded hover:bg-gray-100"
              >
                Audit Trail
              </a>
            </div>
          </div>
        </div>

        {/* Footer Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <p className="text-sm text-blue-800">
            Dashboard updated in real-time. Last sync:{" "}
            {new Date().toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
