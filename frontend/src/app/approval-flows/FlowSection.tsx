"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Plus, Workflow } from "lucide-react";
import { createWorkflow } from "@/lib/api";
import { Card, CardHeader } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import type { WorkflowAppliesTo, WorkflowSummary } from "@/lib/types";

export function FlowSection({
  appliesTo,
  title,
  subtitle,
  flows,
}: {
  appliesTo: WorkflowAppliesTo;
  title: string;
  subtitle: string;
  flows: WorkflowSummary[];
}) {
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const flow = await createWorkflow(name.trim(), appliesTo);
      router.push(`/approval-flows/${flow.id}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card padding="0" className="overflow-hidden">
      <CardHeader className="justify-start">
        <div className="w-[30px] h-[30px] rounded-[8px] bg-[#3a5bd9]/[.1] flex items-center justify-center flex-none">
          <Workflow size={15} color="#3a5bd9" strokeWidth={2} />
        </div>
        <div>
          <div className="font-semibold text-[14px]">{title}</div>
          <div className="text-[11px] text-[#98a2b3]">{subtitle}</div>
        </div>
        <div className="flex-1" />
        {!creating && (
          <button
            type="button"
            onClick={() => setCreating(true)}
            className="flex items-center gap-[5px] text-[12px] font-semibold text-[#3a5bd9]"
          >
            <Plus size={13} strokeWidth={2.5} />
            New Flow
          </button>
        )}
      </CardHeader>

      {creating && (
        <div className="px-[18px] py-[12px] border-b border-[#e6e8ec] bg-[#fafbfc] flex items-center gap-[10px]">
          <input
            autoFocus
            placeholder={'Flow name, e.g. "Standard Penalty Approval"'}
            className="flex-1 border border-[#e6e8ec] rounded-[7px] px-[10px] py-[7px] text-[12.5px] focus:outline-none focus:border-[#3a5bd9]"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
          <button type="button" onClick={submit} disabled={busy || !name.trim()} className="text-[12px] font-semibold text-[#3a5bd9] disabled:opacity-40">
            Create
          </button>
          <button type="button" onClick={() => setCreating(false)} className="text-[12px] text-[#98a2b3]">
            Cancel
          </button>
        </div>
      )}

      {flows.length === 0 ? (
        <div className="px-[18px] py-[16px] text-[12.5px] text-[#98a2b3]">
          No flows configured yet — falls back to the built-in default routing.
        </div>
      ) : (
        <div>
          {flows.map((f) => (
            <Link
              key={f.id}
              href={`/approval-flows/${f.id}`}
              className="flex items-center gap-[12px] px-[18px] py-[12px] border-t border-[#f0f1f4] hover:bg-[#fafbfc]"
            >
              <div className="flex-1">
                <div className="font-medium text-[13px]">{f.name}</div>
                <div className="text-[11px] text-[#98a2b3]">{f.stepCount} step(s) · created {f.createdAt}</div>
              </div>
              {f.isActive ? (
                <Pill color="#12805c" bg="#e6f4ee">
                  Active
                </Pill>
              ) : (
                <Pill color="#667085" bg="#f0f1f4">
                  Draft
                </Pill>
              )}
            </Link>
          ))}
        </div>
      )}
    </Card>
  );
}
