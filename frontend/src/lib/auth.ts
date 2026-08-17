import type { NextAuthOptions } from "next-auth";
import AzureADProvider from "next-auth/providers/azure-ad";
import CredentialsProvider from "next-auth/providers/credentials";

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

// Test-only sign-in that skips Microsoft entirely, calling the backend's /auth/quick-login
// directly with the chosen slot (admin|requester|approver). The backend itself is the one that
// refuses this when ENABLE_QUICK_LOGIN=false, so there's nothing further to gate here.
async function quickLoginExchange(slot: string): Promise<{ ok: boolean; user?: ExchangeUser; accessToken?: string }> {
  const res = await fetch(`${process.env.BACKEND_INTERNAL_URL}/auth/quick-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slot }),
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
    CredentialsProvider({
      id: "quick-login",
      name: "Quick Login",
      credentials: { slot: { label: "Slot", type: "text" } },
      async authorize(credentials) {
        const slot = credentials?.slot;
        if (!slot) return null;
        const result = await quickLoginExchange(slot);
        if (!result.ok || !result.user || !result.accessToken) return null;
        return {
          id: String(result.user.id),
          name: result.user.name,
          email: result.user.email,
          role: result.user.role,
          accessToken: result.accessToken,
        };
      },
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
    async signIn({ profile, account }) {
      if (account?.provider === "quick-login") return true;
      if (!profile?.email) return false;
      const result = await exchangeMicrosoftLogin(profile.email);
      return result.ok;
    },
    async jwt({ token, account, profile, user }) {
      if (account?.provider === "quick-login" && user) {
        token.backendToken = user.accessToken;
        token.role = user.role ?? null;
        token.userId = Number(user.id);
        token.name = user.name;
        token.email = user.email;
        return token;
      }
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
