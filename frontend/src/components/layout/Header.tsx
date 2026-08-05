"use client";

import { Menu, Plus, Search } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSidebar } from "./SidebarContext";

const PAGE_META: Array<{ match: (p: string) => boolean; title: string; subtitle: string }> = [
  { match: (p) => p === "/dashboard" || p === "/", title: "Portfolio Dashboard", subtitle: "Overview of subcontracts, spend, retention and alerts" },
  { match: (p) => p === "/contracts", title: "Contracts", subtitle: "All subcontracts across projects and service types" },
  { match: (p) => p.startsWith("/contracts/new"), title: "New Subcontract", subtitle: "Create a Scope/Works or Manpower Supply subcontract" },
  { match: (p) => p.endsWith("/manpower") && p.startsWith("/contracts/"), title: "Manpower Contract", subtitle: "Contractor detail and position rate card" },
  { match: (p) => p.startsWith("/contracts/") && !p.startsWith("/contracts/new"), title: "Contract Tracking", subtitle: "Progress-linked payments, retention and advance recovery" },
  { match: (p) => p === "/manpower", title: "Manpower Reconciliation", subtitle: "Timesheet vs contract rates vs vendor invoice" },
  { match: (p) => p === "/change-orders", title: "Change Orders", subtitle: "Vary contract quantities and revise the Oracle PO" },
  { match: (p) => p === "/penalties", title: "Apply Penalty", subtitle: "Raise and route a penalty for approval" },
  { match: (p) => p === "/evaluations", title: "Subcontractor Evaluation", subtitle: "Performance scorecards and ratings" },
  { match: (p) => p === "/assistant", title: "Activity Assistant", subtitle: "Ask about any action taken across contracts" },
  { match: (p) => p === "/users", title: "User Management", subtitle: "Directory of people assignable as named approvers" },
  { match: (p) => p === "/approval-flows", title: "Approval Flows", subtitle: "Configure dynamic approval routing per entity type" },
  { match: (p) => p.startsWith("/approval-flows/"), title: "Approval Flow Builder", subtitle: "Design a linear approval chain and assign approvers" },
];

export function Header() {
  const pathname = usePathname();
  const { toggle } = useSidebar();
  const meta = PAGE_META.find((m) => m.match(pathname)) ?? PAGE_META[0];

  return (
    <header className="print:hidden h-[64px] flex-none bg-white border-b border-[#e6e8ec] flex items-center gap-[10px] sm:gap-[16px] px-[14px] lg:px-[26px] sticky top-0 z-20">
      <button
        type="button"
        onClick={toggle}
        aria-label="Toggle navigation"
        className="lg:hidden flex-none w-[34px] h-[34px] rounded-[8px] flex items-center justify-center text-[#475467] hover:bg-[#f4f5f7]"
      >
        <Menu size={19} strokeWidth={2} />
      </button>
      <div className="min-w-0">
        <div className="text-[14.5px] sm:text-[16.5px] font-semibold tracking-[-0.01em] truncate">{meta.title}</div>
        <div className="text-[11.5px] sm:text-[12px] text-[#667085] truncate hidden sm:block">{meta.subtitle}</div>
      </div>
      <div className="flex-1" />
      <div className="hidden md:flex items-center gap-[9px] bg-[#f4f5f7] border border-[#e6e8ec] rounded-[8px] px-[11px] py-[7px] w-[230px]">
        <Search size={15} color="#98a2b3" strokeWidth={2} />
        <span className="text-[12.5px] text-[#98a2b3]">Search contracts, vendors…</span>
      </div>
      <Link
        href="/contracts/new"
        className="flex items-center gap-[7px] bg-[#3a5bd9] text-white rounded-[8px] px-[10px] sm:px-[14px] py-[9px] text-[13px] font-semibold hover:brightness-[1.08] flex-none"
      >
        <Plus size={15} strokeWidth={2.2} />
        <span className="hidden sm:inline">New Contract</span>
      </Link>
      <div className="w-[36px] h-[36px] rounded-full bg-[#3a5bd9]/[.15] text-[#3a5bd9] flex items-center justify-center font-semibold text-[13px] flex-none hidden sm:flex">
        RM
      </div>
    </header>
  );
}
