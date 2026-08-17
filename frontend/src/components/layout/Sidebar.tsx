"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "next-auth/react";
import { useSidebar } from "./SidebarContext";
import { isPathAllowed } from "@/lib/roles";
import type { AccessRole } from "@/lib/types";

interface NavItem {
  isGroup?: boolean;
  label: string;
  href?: string;
  match?: (pathname: string) => boolean;
}

const NAV_ITEMS: NavItem[] = [
  { isGroup: true, label: "Overview" },
  { label: "Portfolio Dashboard", href: "/dashboard" },
  { label: "Contracts", href: "/contracts", match: (p) => p === "/contracts" },
  { isGroup: true, label: "My Approvals" },
  { label: "Approvals Inbox", href: "/approvals" },
  { isGroup: true, label: "Manage" },
  { label: "New Contract", href: "/contracts/new" },
  { label: "Contract Tracking", href: "/contracts/SC-2024-0142", match: (p) => p.startsWith("/contracts/") && p !== "/contracts/new" },
  { label: "Manpower Reconciliation", href: "/manpower" },
  { label: "Change Orders", href: "/change-orders" },
  { isGroup: true, label: "Governance" },
  { label: "Apply Penalty", href: "/penalties" },
  { label: "Evaluations", href: "/evaluations" },
  { isGroup: true, label: "Insights" },
  { label: "Activity Assistant", href: "/assistant" },
  { isGroup: true, label: "Administration" },
  { label: "User Management", href: "/users" },
  { label: "Approval Flows", href: "/approval-flows", match: (p) => p.startsWith("/approval-flows") },
];

function visibleNavItems(role: AccessRole): NavItem[] {
  const withAccess = NAV_ITEMS.filter((item) => item.isGroup || isPathAllowed(role, item.href!));
  return withAccess.filter((item, i) => {
    if (!item.isGroup) return true;
    const next = withAccess[i + 1];
    return !!next && !next.isGroup;
  });
}

export function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const { isOpen, close } = useSidebar();

  if (pathname === "/login") return null;

  const role = (session?.user?.role ?? null) as AccessRole;
  const items = visibleNavItems(role);

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 bg-black/40 z-30 lg:hidden" onClick={close} aria-hidden="true" />
      )}
      <aside
        className={
          "print:hidden w-[248px] flex-none bg-[#0f1523] text-[#c3cad9] flex flex-col fixed inset-y-0 left-0 z-40 h-screen transition-transform duration-200 lg:sticky lg:top-0 lg:translate-x-0 " +
          (isOpen ? "translate-x-0" : "-translate-x-full")
        }
      >
        <div className="px-[20px] pt-[20px] pb-[16px] flex items-center gap-[11px] border-b border-white/[.07]">
          <div className="w-[34px] h-[34px] rounded-[9px] bg-[#3a5bd9] flex items-center justify-center flex-none">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
              <path d="M4 7h16M4 12h16M4 17h10" />
            </svg>
          </div>
          <div className="leading-[1.15]">
            <div className="font-bold text-white text-[14.5px] tracking-[-0.01em]">Subcontract</div>
            <div className="text-[11px] text-[#7a869c] font-medium">Vendor & Manpower Control</div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto px-[12px] py-[14px]">
          {items.map((item, i) => {
            if (item.isGroup) {
              return (
                <div key={i} className="text-[10px] font-semibold tracking-[.09em] uppercase text-[#5b667e] px-[12px] pt-[16px] pb-[7px]">
                  {item.label}
                </div>
              );
            }
            const active = item.match ? item.match(pathname) : pathname === item.href;
            return (
              <Link
                key={i}
                href={item.href!}
                onClick={close}
                className="flex items-center gap-[11px] w-full px-[12px] py-[9px] mb-[2px] rounded-[8px] text-[13px] text-left hover:bg-white/[.05] hover:text-white transition-colors"
                style={{
                  fontWeight: active ? 600 : 500,
                  background: active ? "rgba(255,255,255,.09)" : "transparent",
                  color: active ? "#fff" : "#c3cad9",
                }}
              >
                <span className="w-[6px] h-[6px] rounded-full flex-none" style={{ background: active ? "#fff" : "#5b667e" }} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
