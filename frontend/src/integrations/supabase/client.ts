// This file is for compatibility only
// The application uses JWT-based authentication instead
// Do not use - use the API client in lib/api-client.ts instead

export const supabase = {
  auth: {
    getSession: async () => ({ data: { session: null } }),
    onAuthStateChange: () => ({ subscription: { unsubscribe: () => {} } }),
    signInWithPassword: async () => ({ error: { message: "Use authService.login() instead" } }),
    signUp: async () => ({ error: { message: "Use authService.register() instead" } }),
    signOut: async () => ({}),
  },
};