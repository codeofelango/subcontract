import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    backendToken?: string;
    user?: DefaultSession["user"] & {
      id?: number;
      role?: string | null;
    };
  }

  interface User {
    role?: string | null;
    accessToken?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    backendToken?: string;
    role?: string | null;
    userId?: number;
  }
}
