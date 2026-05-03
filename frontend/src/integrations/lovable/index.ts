// This file is for compatibility only
// The application uses JWT-based authentication instead
// Do not use - use the API client in lib/api-client.ts instead

type SignInOptions = {
  redirect_uri?: string;
  extraParams?: Record<string, string>;
};

export const lovable = {
  auth: {
    signInWithOAuth: async (provider: "google" | "apple" | "microsoft" | "lovable", opts?: SignInOptions) => {
      return { error: new Error("OAuth is not supported. Use email/password authentication instead.") };
    },
  },
};
