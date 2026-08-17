import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    backendToken?: string;
    user?: DefaultSession["user"] & {
      id?: number;
      role?: string | null;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    backendToken?: string;
    role?: string | null;
    userId?: number;
  }
}
