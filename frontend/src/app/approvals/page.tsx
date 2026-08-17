import Link from "next/link";
import { getApprovals } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";

export const dynamic = "force-dynamic";

// Change Orders and Penalties don't have per-record routes yet (single hardcoded-record
// prototype pages - see ARCHITECTURE notes), so those link to their shared list page for now.
const LINK_BY_ITEM: Record<string, (ref: string) => string> = {
  "New contract approval": (ref) => `/contracts/${ref}`,
  "Change order approval": () => "/change-orders",
  "Penalty approval": () => "/penalties",
  "Progress payment": () => "/contracts",
};

export default async function ApprovalsPage() {
  const items = await getApprovals();

  return (
    <div className="flex flex-col gap-[16px] max-w-[1100px]">
      <div className="text-[13px] text-[#667085]">
        Items currently awaiting your decision, across contracts, change orders, and penalties.
      </div>
      <Card padding="0" className="overflow-hidden">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="text-left text-[#667085] text-[11px] uppercase tracking-[.05em] bg-[#fafbfc]">
              <th className="px-[18px] py-[12px] font-semibold">Reference</th>
              <th className="px-[18px] py-[12px] font-semibold">Item</th>
              <th className="px-[18px] py-[12px] font-semibold">Vendor</th>
              <th className="px-[18px] py-[12px] font-semibold">Stage</th>
              <th className="px-[18px] py-[12px] font-semibold text-right">Amount</th>
              <th className="px-[18px] py-[12px] font-semibold">Waiting</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-[18px] py-[20px] text-[13px] text-[#667085]">
                  Nothing pending your action right now.
                </td>
              </tr>
            )}
            {items.map((p, i) => (
              <tr key={i} className="border-t border-[#f0f1f4] hover:bg-[#fafbfc]">
                <td className="px-[18px] py-[12px] font-mono font-medium">
                  <Link href={(LINK_BY_ITEM[p.item] ?? (() => "/dashboard"))(p.ref)} className="text-[#3a5bd9]">
                    {p.ref}
                  </Link>
                </td>
                <td className="px-[18px] py-[12px]">{p.item}</td>
                <td className="px-[18px] py-[12px] text-[#475467]">{p.vendor}</td>
                <td className="px-[18px] py-[12px] text-[#475467]">{p.stage}</td>
                <td className="px-[18px] py-[12px] text-right font-mono">{p.amount}</td>
                <td className="px-[18px] py-[12px]">
                  <Pill color={p.color} bg={p.bg}>
                    {p.age}
                  </Pill>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
