import { NextAuthOptions } from 'next-auth';
import AzureADProvider from 'next-auth/providers/azure-ad';

// Extend profile type for Azure AD
interface AzureADProfile {
  roles?: string[];
  [key: string]: unknown;
}

export const authOptions: NextAuthOptions = {
  providers: [
    AzureADProvider({
      clientId: process.env.AZURE_AD_CLIENT_ID || '',
      clientSecret: process.env.AZURE_AD_CLIENT_SECRET || '',
      tenantId: process.env.AZURE_AD_TENANT_ID || '',
      authorization: {
        params: {
          scope: 'openid profile email User.Read',
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account) {
        token.accessToken = account.access_token;
        token.idToken = account.id_token;
        // Extract roles from the profile if available
        const azureProfile = profile as AzureADProfile | undefined;
        if (azureProfile?.roles) {
          token.roles = azureProfile.roles;
        }
      }
      return token;
    },
    async session({ session, token }) {
      // Use type assertion with proper typing
      session.accessToken = token.accessToken;
      session.user.roles = token.roles || [];
      session.user.id = token.sub || '';
      return session;
    },
  },
  pages: {
    signIn: '/signin',
    error: '/signin',
  },
  session: {
    strategy: 'jwt',
    maxAge: 24 * 60 * 60, // 24 hours
  },
};
