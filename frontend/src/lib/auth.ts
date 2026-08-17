import type { NextAuthOptions } from "next-auth";
import AzureADProvider from "next-auth/providers/azure-ad";

type ExchangeUser = {
  id: number;
  name: string;
  email: string;
  role: string | null;
};

async function exchangeMicrosoftLogin(email: string): Promise<{ ok: boolean; user?: ExchangeUser; accessToken?: string }> {
  const res = await fetch(`${process.env.BACKEND_INTERNAL_URL}/auth/microsoft/exchange`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Secret": process.env.INTERNAL_AUTH_SECRET ?? "",
    },
    body: JSON.stringify({ email }),
    cache: "no-store",
  });
  if (!res.ok) return { ok: false };
  const data = await res.json();
  return { ok: true, user: data.user, accessToken: data.access_token };
}

export const authOptions: NextAuthOptions = {
  providers: [
    AzureADProvider({
      clientId: process.env.MICROSOFT_CLIENT_ID ?? "",
      clientSecret: process.env.MICROSOFT_CLIENT_SECRET ?? "",
      tenantId: process.env.MICROSOFT_TENANT_ID ?? "",
    }),
  ],
  pages: {
    signIn: "/login",
    error: "/login",
  },
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async signIn({ profile }) {
      if (!profile?.email) return false;
      const result = await exchangeMicrosoftLogin(profile.email);
      return result.ok;
    },
    async jwt({ token, account, profile }) {
      if (account && profile?.email) {
        const result = await exchangeMicrosoftLogin(profile.email);
        if (result.ok && result.user && result.accessToken) {
          token.backendToken = result.accessToken;
          token.role = result.user.role;
          token.userId = result.user.id;
          token.name = result.user.name;
          token.email = result.user.email;
        }
      }
      return token;
    },
    async session({ session, token }) {
      session.backendToken = token.backendToken;
      if (session.user) {
        session.user.role = token.role ?? null;
        session.user.id = token.userId;
      }
      return session;
    },
  },
};
