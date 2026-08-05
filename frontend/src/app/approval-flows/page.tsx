import { listWorkflows } from "@/lib/api";
import type { WorkflowAppliesTo } from "@/lib/types";
import { FlowSection } from "./FlowSection";

export const dynamic = "force-dynamic";

const SECTIONS: Array<{ appliesTo: WorkflowAppliesTo; title: string; subtitle: string }> = [
  { appliesTo: "contract_scope", title: "Scope / Works Contract", subtitle: "Approval routing when a Scope/Works contract is submitted" },
  { appliesTo: "contract_manpower", title: "Manpower Supply Contract", subtitle: "Approval routing when a Manpower Supply contract is submitted" },
  { appliesTo: "change_order", title: "Change Order", subtitle: "Approval routing for quantity change orders" },
  { appliesTo: "penalty", title: "Penalty", subtitle: "Approval routing for subcontractor penalties" },
];

export default async function ApprovalFlowsPage() {
  const all = await listWorkflows();

  return (
    <div className="flex flex-col gap-[18px] max-w-[1100px]">
      <div className="text-[13px] text-[#667085]">
        Each entity type below can have any number of drafted flows, but only one can be <b>Active</b> at a time — that's
        the one used when a new record of that type is created. Editing a flow updates its draft only; nothing changes
        for live records until you press Activate.
      </div>
      {SECTIONS.map((s) => (
        <FlowSection key={s.appliesTo} appliesTo={s.appliesTo} title={s.title} subtitle={s.subtitle} flows={all.filter((f) => f.appliesTo === s.appliesTo)} />
      ))}
    </div>
  );
}
