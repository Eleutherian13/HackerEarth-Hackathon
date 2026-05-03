import client from './api-client';

// ==================== Auth Service ====================
export const authService = {
  login: async (credentials: { email: string; password: string }) => {
    const { data } = await client.post('/api/auth/login', credentials);
    return data;
  },

  register: async (userData: { email: string; password: string; full_name: string }) => {
    const { data } = await client.post('/api/auth/register', userData);
    return data;
  },

  refresh: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    const { data } = await client.post('/api/auth/refresh', { refresh_token: refreshToken });
    return data;
  },

  logout: async () => {
    try {
      await client.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    }
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_role');
  },
};

// ==================== User Service ====================
export const userService = {
  getProfile: async () => {
    const { data } = await client.get('/api/users/profile');
    return data;
  },

  updateProfile: async (userData: Record<string, any>) => {
    const { data } = await client.put('/api/users/profile', userData);
    return data;
  },

  getAllUsers: async (page?: number, limit?: number) => {
    const { data } = await client.get('/api/users', {
      params: { page, limit },
    });
    return data;
  },

  getUserById: async (userId: string) => {
    const { data } = await client.get(`/api/users/${userId}`);
    return data;
  },

  createUser: async (userData: Record<string, any>) => {
    const { data } = await client.post('/api/users', userData);
    return data;
  },

  updateUser: async (userId: string, userData: Record<string, any>) => {
    const { data } = await client.put(`/api/users/${userId}`, userData);
    return data;
  },

  deleteUser: async (userId: string) => {
    const { data } = await client.delete(`/api/users/${userId}`);
    return data;
  },
};

// ==================== Document Service ====================
export const documentService = {
  uploadDocument: async (file: File, caseId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (caseId) formData.append('case_id', caseId);
    
    const { data } = await client.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  getDocuments: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/api/documents', { params: filters });
    return data;
  },

  getDocumentById: async (documentId: string) => {
    const { data } = await client.get(`/api/documents/${documentId}`);
    return data;
  },

  deleteDocument: async (documentId: string) => {
    const { data } = await client.delete(`/api/documents/${documentId}`);
    return data;
  },

  previewDocument: async (documentId: string) => {
    const { data } = await client.get(`/api/documents/${documentId}/preview`);
    return data;
  },
};

// ==================== Case Service ====================
export const caseService = {
  getCases: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/api/cases', { params: filters });
    return data;
  },

  getCaseById: async (caseId: string) => {
    const { data } = await client.get(`/api/cases/${caseId}`);
    return data;
  },

  createCase: async (caseData: Record<string, any>) => {
    const { data } = await client.post('/api/cases', caseData);
    return data;
  },

  updateCase: async (caseId: string, caseData: Record<string, any>) => {
    const { data } = await client.put(`/api/cases/${caseId}`, caseData);
    return data;
  },

  deleteCase: async (caseId: string) => {
    const { data } = await client.delete(`/api/cases/${caseId}`);
    return data;
  },

  getCaseDocuments: async (caseId: string) => {
    const { data } = await client.get(`/api/cases/${caseId}/documents`);
    return data;
  },

  getCaseActions: async (caseId: string) => {
    const { data } = await client.get(`/api/cases/${caseId}/actions`);
    return data;
  },
};

// ==================== Review Service ====================
export const reviewService = {
  getReviews: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/api/reviews', { params: filters });
    return data;
  },

  getReviewById: async (reviewId: string) => {
    const { data } = await client.get(`/api/reviews/${reviewId}`);
    return data;
  },

  createReview: async (reviewData: Record<string, any>) => {
    const { data } = await client.post('/api/reviews', reviewData);
    return data;
  },

  updateReview: async (reviewId: string, reviewData: Record<string, any>) => {
    const { data } = await client.put(`/api/reviews/${reviewId}`, reviewData);
    return data;
  },

  submitReview: async (reviewId: string, decision: Record<string, any>) => {
    const { data } = await client.post(`/api/reviews/${reviewId}/submit`, decision);
    return data;
  },
};

// ==================== Action Service ====================
export const actionService = {
  getActions: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/api/actions', { params: filters });
    return data;
  },

  getActionById: async (actionId: string) => {
    const { data } = await client.get(`/api/actions/${actionId}`);
    return data;
  },

  createAction: async (actionData: Record<string, any>) => {
    const { data } = await client.post('/api/actions', actionData);
    return data;
  },

  updateAction: async (actionId: string, actionData: Record<string, any>) => {
    const { data } = await client.put(`/api/actions/${actionId}`, actionData);
    return data;
  },

  deleteAction: async (actionId: string) => {
    const { data } = await client.delete(`/api/actions/${actionId}`);
    return data;
  },

  updateActionStatus: async (actionId: string, status: string) => {
    const { data } = await client.patch(`/api/actions/${actionId}/status`, { status });
    return data;
  },
};

// ==================== Audit Service ====================
export const auditService = {
  getAuditTrail: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/api/audit-trail', { params: filters });
    return data;
  },

  getAuditById: async (auditId: string) => {
    const { data } = await client.get(`/api/audit-trail/${auditId}`);
    return data;
  },

  getUserActivityLog: async (userId: string, filters?: Record<string, any>) => {
    const { data } = await client.get(`/api/audit-trail/user/${userId}`, { params: filters });
    return data;
  },
};

// ==================== Analytics Service ====================
export const analyticsService = {
  getDashboardStats: async () => {
    const { data } = await client.get('/api/analytics/dashboard');
    return data;
  },

  getCaseStats: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/api/analytics/cases', { params: filters });
    return data;
  },

  getComplianceStats: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/api/analytics/compliance', { params: filters });
    return data;
  },

  getActionStats: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/api/analytics/actions', { params: filters });
    return data;
  },
};

// ==================== Export all services ====================
export default {
  authService,
  userService,
  documentService,
  caseService,
  reviewService,
  actionService,
  auditService,
  analyticsService,
};
