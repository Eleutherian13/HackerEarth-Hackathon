import client from './api-client';

// ==================== Auth Service ====================
export const authService = {
  login: async (credentials: { email: string; password: string }) => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    const { data } = await client.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },

  register: async (userData: {
    email: string;
    password: string;
    full_name: string;
  }) => {
    const { data } = await client.post('/auth/register', userData);
    return data;
  },

  refresh: async () => {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      throw new Error('No refresh token found');
    }

    const { data } = await client.post('/auth/refresh', {
      refresh_token: refreshToken,
    });

    return data;
  },

  logout: async () => {
    try {
      await client.post('/auth/logout');
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
    const { data } = await client.get('/auth/me');
    return data;
  },

  updateProfile: async (userData: Record<string, any>) => {
    const { data } = await client.put('/auth/me', userData);
    return data;
  },

  getAllUsers: async (page?: number, limit?: number) => {
    const { data } = await client.get('/admin/users', {
      params: {
        page,
        per_page: limit ?? 10,
      },
    });
    return data;
  },

  getUserById: async (userId: string) => {
    const { data } = await client.get(`/users/${userId}`);
    return data;
  },

  createUser: async (userData: Record<string, any>) => {
    const { data } = await client.post('/users', userData);
    return data;
  },

  updateUser: async (userId: string, userData: Record<string, any>) => {
    const { data } = await client.put(`/users/${userId}`, userData);
    return data;
  },

  deleteUser: async (userId: string) => {
    const { data } = await client.delete(`/users/${userId}`);
    return data;
  },
};

// ==================== Document Service ====================
export const documentService = {
  uploadDocument: async (file: File, caseId?: string) => {
    const formData = new FormData();
    formData.append('file', file);

    if (caseId) {
      formData.append('case_id', caseId);
    }

    const { data } = await client.post('/documents/upload', formData);
    return data;
  },

  getDocuments: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/documents', {
      params: filters,
    });
    return data;
  },

  getDocumentById: async (documentId: string) => {
    const { data } = await client.get(`/documents/${documentId}`);
    return data;
  },

  deleteDocument: async (documentId: string) => {
    const { data } = await client.delete(`/documents/${documentId}`);
    return data;
  },

  previewDocument: async (documentId: string) => {
    const { data } = await client.get(
      `/documents/${documentId}/preview`
    );
    return data;
  },
};

// ==================== Case Service ====================
export const caseService = {
  getCases: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/cases', {
      params: filters,
    });
    return data;
  },

  getCaseById: async (caseId: string) => {
    const { data } = await client.get(`/cases/${caseId}`);
    return data;
  },

  createCase: async (caseData: Record<string, any>) => {
    const { data } = await client.post('/cases', caseData);
    return data;
  },

  updateCase: async (caseId: string, caseData: Record<string, any>) => {
    const { data } = await client.put(`/cases/${caseId}`, caseData);
    return data;
  },

  deleteCase: async (caseId: string) => {
    const { data } = await client.delete(`/cases/${caseId}`);
    return data;
  },

  getCaseDocuments: async (caseId: string) => {
    const { data } = await client.get(
      `/cases/${caseId}/documents`
    );
    return data;
  },

  getCaseActions: async (caseId: string) => {
    const { data } = await client.get(
      `/cases/${caseId}/actions`
    );
    return data;
  },
};

// ==================== Review Service ====================
export const reviewService = {
  getReviews: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/reviews', {
      params: filters,
    });
    return data;
  },

  getReviewById: async (reviewId: string) => {
    const { data } = await client.get(`/reviews/${reviewId}`);
    return data;
  },

  createReview: async (reviewData: Record<string, any>) => {
    const { data } = await client.post('/reviews', reviewData);
    return data;
  },

  updateReview: async (reviewId: string, reviewData: Record<string, any>) => {
    const { data } = await client.put(
      `/reviews/${reviewId}`,
      reviewData
    );
    return data;
  },

  submitReview: async (reviewId: string, decision: Record<string, any>) => {
    const { data } = await client.post(
      `/reviews/${reviewId}/submit`,
      decision
    );
    return data;
  },
};

// ==================== Action Service ====================
export const actionService = {
  getActions: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/actions', {
      params: filters,
    });
    return data;
  },

  getActionById: async (actionId: string) => {
    const { data } = await client.get(`/actions/${actionId}`);
    return data;
  },

  createAction: async (actionData: Record<string, any>) => {
    const { data } = await client.post('/actions', actionData);
    return data;
  },

  updateAction: async (actionId: string, actionData: Record<string, any>) => {
    const { data } = await client.put(
      `/actions/${actionId}`,
      actionData
    );
    return data;
  },

  deleteAction: async (actionId: string) => {
    const { data } = await client.delete(`/actions/${actionId}`);
    return data;
  },

  updateActionStatus: async (actionId: string, status: string) => {
    const { data } = await client.patch(
      `/actions/${actionId}/status`,
      { status }
    );
    return data;
  },
};

// ==================== Audit Service ====================
export const auditService = {
  getAuditTrail: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/audit-trail', {
      params: filters,
    });
    return data;
  },

  getAuditById: async (auditId: string) => {
    const { data } = await client.get(
      `/audit-trail/${auditId}`
    );
    return data;
  },

  getUserActivityLog: async (
    userId: string,
    filters?: Record<string, any>
  ) => {
    const { data } = await client.get(
      `/audit-trail/user/${userId}`,
      { params: filters }
    );
    return data;
  },
};

// ==================== Analytics Service ====================
export const analyticsService = {
  getDashboardStats: async () => {
    const { data } = await client.get('/analytics/dashboard');
    return data;
  },

  getCaseStats: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/analytics/cases', {
      params: filters,
    });
    return data;
  },

  getComplianceStats: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/analytics/compliance', {
      params: filters,
    });
    return data;
  },

  getActionStats: async (filters?: Record<string, any>) => {
    const { data } = await client.get('/api/analytics/actions', {
      params: filters,
    });
    return data;
  },
};

// ==================== Export ====================
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