import Link from "next/link";
import { ChevronDown } from "lucide-react";
import { listContracts } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { ProgressBar } from "@/components/ui/ProgressBar";

export const dynamic = "force-dynamic";

const FILTERS = [
  { label: "Project", value: "All" },
  { label: "Service Type", value: "All" },
  { label: "Vendor", value: "All" },
  { label: "Status", value: "All" },
  { label: "Expiry", value: "Any" },
];

export default async function ContractsPage() {
  const { items, count } = await listContracts();

  return (
    <div className="flex flex-col gap-[16px] max-w-[1320px]">
      <div className="flex gap-[10px] items-center flex-wrap">
        {FILTERS.map((f) => (
          <div
            key={f.label}
            className="flex items-center gap-[7px] bg-white border border-[#e6e8ec] rounded-[8px] px-[12px] py-[8px] text-[12.5px] text-[#475467] cursor-pointer"
          >
            <span className="text-[#98a2b3]">{f.label}:</span>
            <span className="font-semibold text-[#101828]">{f.value}</span>
            <ChevronDown size={12} color="#98a2b3" strokeWidth={2.4} />
          </div>
        ))}
        <div className="flex-1" />
        <span className="text-[12.5px] text-[#667085]">{count} contracts</span>
      </div>

      <Card padding="0" className="overflow-hidden">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="text-left text-[#667085] text-[11px] uppercase tracking-[.05em] bg-[#fafbfc]">
              <th className="px-[16px] py-[12px] font-semibold">Contract #</th>
              <th className="px-[16px] py-[12px] font-semibold">Vendor</th>
              <th className="px-[16px] py-[12px] font-semibold">Type</th>
              <th className="px-[16px] py-[12px] font-semibold">Project</th>
              <th className="px-[16px] py-[12px] font-semibold text-right">Value</th>
              <th className="px-[16px] py-[12px] font-semibold">Progress</th>
              <th className="px-[16px] py-[12px] font-semibold">Expiry</th>
              <th className="px-[16px] py-[12px] font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id} className="border-t border-[#f0f1f4] hover:bg-[#fafbfc]">
                <td className="p-0">
                  <Link
                    href={c.contractCategory === "manpower" ? `/contracts/${c.id}/manpower` : `/contracts/${c.id}`}
                    className="flex px-[16px] py-[13px] font-mono font-medium text-[#3a5bd9]"
                  >
                    {c.id}
                  </Link>
                </td>
                <td className="px-[16px] py-[13px] font-semibold">{c.vendor}</td>
                <td className="px-[16px] py-[13px]">
                  <span className="text-[11px] font-semibold px-[9px] py-[3px] rounded-[6px]" style={{ color: c.typeColor, background: c.typeBg }}>
                    {c.type}
                  </span>
                </td>
                <td className="px-[16px] py-[13px] text-[#475467]">{c.project}</td>
                <td className="px-[16px] py-[13px] text-right font-mono">{c.valueFmt}</td>
                <td className="px-[16px] py-[13px]">
                  <div className="flex items-center gap-[8px]">
                    <div className="w-[66px]">
                      <ProgressBar width={c.progressW} color={c.progressColor} height={6} />
                    </div>
                    <span className="font-mono text-[12px] text-[#475467]">{c.progress}</span>
                  </div>
                </td>
                <td className="px-[16px] py-[13px] text-[#475467] font-mono text-[12px]">{c.expiry}</td>
                <td className="px-[16px] py-[13px]">
                  <Pill color={c.statusColor} bg={c.statusBg}>
                    {c.status}
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
