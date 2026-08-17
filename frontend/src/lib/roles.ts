import type { AccessRole } from "./types";

// Per-role page gating, mirroring the backend's department/contract-type scoping (see
// backend/app/auth.py's require_roles()/assert_contract_visible()):
//  - procurement_requester and hr_requester are split by contract type (Scope/Works vs
//    Manpower Supply) - each only reaches the creation flow and detail screen for their own
//    department's contracts. Change Orders only ever apply to Scope contracts (no PO/BOQ on
//    Manpower), so hr_requester never sees /change-orders; Manpower Reconciliation is HR-only.
//  - approver never raises anything (no /contracts/new*, no /manpower actions) - they search
//    and decide, via the shared list/detail pages plus the dedicated /approvals inbox.
//  - admin sees everything, including User Management and Approval Flows.
const ADMIN_ONLY_PREFIXES = ["/users", "/approval-flows"];

const SHARED_PREFIXES = ["/dashboard", "/contracts", "/evaluations", "/assistant"];

const ROLE_PREFIXES: Record<Exclude<AccessRole, "admin" | null>, string[]> = {
  procurement_requester: [...SHARED_PREFIXES, "/contracts/new/work", "/change-orders", "/penalties"],
  hr_requester: [...SHARED_PREFIXES, "/contracts/new/manpower", "/manpower", "/penalties"],
  approver: [...SHARED_PREFIXES, "/change-orders", "/penalties", "/approvals"],
};

// `/contracts` is shared, so the creation sub-flows need an explicit deny per role rather than
// just being left out of ROLE_PREFIXES (they'd still match the broad `/contracts` prefix above).
const ROLE_DENY_PREFIXES: Record<Exclude<AccessRole, "admin" | null>, string[]> = {
  procurement_requester: ["/contracts/new/manpower"],
  hr_requester: ["/contracts/new/work"],
  approver: ["/contracts/new"],
};

export function allowedPrefixes(role: AccessRole): string[] {
  if (role === "admin") return ["*"];
  if (role === "procurement_requester" || role === "hr_requester" || role === "approver") {
    return ROLE_PREFIXES[role];
  }
  return [];
}

function matchesPrefix(pathname: string, prefix: string): boolean {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

export function isPathAllowed(role: AccessRole, pathname: string): boolean {
  if (role && role !== "admin" && ROLE_DENY_PREFIXES[role]?.some((p) => matchesPrefix(pathname, p))) {
    return false;
  }
  const prefixes = allowedPrefixes(role);
  if (prefixes.includes("*")) return true;
  return prefixes.some((p) => matchesPrefix(pathname, p));
}

export function isAdminOnlyPath(pathname: string): boolean {
  return ADMIN_ONLY_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}
