// Stub for Lovable integration - using backend auth instead
// This app uses FastAPI backend authentication, not Lovable cloud auth

type SignInOptions = {
  redirect_uri?: string;
  extraParams?: Record<string, string>;
};

export const lovable = {
  auth: {
    signInWithOAuth: async (provider: "google" | "apple" | "microsoft" | "lovable", opts?: SignInOptions) => {
      // OAuth via backend is not yet implemented
      // For now, throw an error directing users to email/password login
      console.warn(`OAuth provider ${provider} not yet configured`);
      throw new Error(`OAuth provider ${provider} is not configured. Please use email/password login.`);
    },
  },
};
