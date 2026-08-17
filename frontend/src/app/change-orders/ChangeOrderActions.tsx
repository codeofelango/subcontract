"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { decideChangeOrderStep, reviseChangeOrderStep } from "@/lib/api";
import { ApprovalTimeline } from "@/components/ui/ApprovalTimeline";
import type { ApprovalStepOut } from "@/lib/types";

function ReviseModal({
  coId, step, onClose,
}: { coId: string; step: ApprovalStepOut; onClose: () => void }) {
  const router = useRouter();
  const [decision, setDecision] = useState<"approved" | "rejected">(step.decision === "approved" ? "rejected" : "approved");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!step.id) return;
    setBusy(true);
    setError(null);
    try {
      await reviseChangeOrderStep(coId, step.id, decision, reason);
      onClose();
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Revision failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-[16px]" onClick={onClose}>
      <div className="bg-white rounded-[10px] p-[18px] w-full max-w-[380px]" onClick={(e) => e.stopPropagation()}>
        <div className="text-[14px] font-semibold mb-[10px]">Change decision — {step.role}</div>
        {error && <div className="mb-[8px] text-[11.5px] text-[#c0362c]">{error}</div>}
        <div className="flex gap-[8px] mb-[10px]">
          <button
            type="button"
            onClick={() => setDecision("approved")}
            className="flex-1 rounded-[8px] py-[8px] text-[12.5px] font-semibold border"
            style={{
              background: decision === "approved" ? "#e6f4ee" : "#fff",
              color: decision === "approved" ? "#12805c" : "#475467",
              borderColor: decision === "approved" ? "#12805c" : "#e6e8ec",
            }}
          >
            Approve
          </button>
          <button
            type="button"
            onClick={() => setDecision("rejected")}
            className="flex-1 rounded-[8px] py-[8px] text-[12.5px] font-semibold border"
            style={{
              background: decision === "rejected" ? "#fbeceb" : "#fff",
              color: decision === "rejected" ? "#c0362c" : "#475467",
              borderColor: decision === "rejected" ? "#c0362c" : "#e6e8ec",
            }}
          >
            Reject
          </button>
        </div>
        <textarea
          className="w-full border border-[#e6e8ec] rounded-[8px] px-[10px] py-[8px] text-[12.5px] mb-[10px]"
          rows={2}
          placeholder="Reason for the change (required)"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <div className="flex gap-[8px]">
          <button
            type="button"
            disabled={busy || !reason.trim()}
            onClick={submit}
            className="flex-1 bg-[#3a5bd9] rounded-[8px] py-[9px] text-[12.5px] font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Saving…" : "Save"}
          </button>
          <button type="button" onClick={onClose} className="flex-1 border border-[#e6e8ec] rounded-[8px] py-[9px] text-[12.5px] font-semibold text-[#475467]">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export function ChangeOrderApprovalPanel({ coId, steps }: { coId: string; steps: ApprovalStepOut[] }) {
  const router = useRouter();
  const { data: session } = useSession();
  const [busy, setBusy] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [reviseTarget, setReviseTarget] = useState<ApprovalStepOut | null>(null);

  const currentStep = steps.find((s) => s.state === "current");
  const canAct = !!currentStep && (session?.user?.role === "admin" || currentStep.name === session?.user?.name);

  async function decide(decision: "approved" | "rejected") {
    setBusy(true);
    setError(null);
    try {
      await decideChangeOrderStep(coId, decision, comment || undefined);
      setRejecting(false);
      setComment("");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <ApprovalTimeline
        steps={steps}
        size="sm"
        onRevise={(step) => setReviseTarget(step)}
        canRevise={(step, i, all) => step.decision !== null && !all[i + 1]?.decision && (session?.user?.role === "admin" || step.actedBy === session?.user?.name)}
      />
      {currentStep && (
        <div className="mt-[10px]">
          {error && <div className="mb-[8px] text-[11.5px] text-[#c0362c]">{error}</div>}
          {!canAct && <div className="mb-[8px] text-[11px] text-[#98a2b3]">Only {currentStep.name} (or an Admin) can act on this step.</div>}
          {rejecting ? (
            <div className="space-y-[8px]">
              <textarea
                className="w-full border border-[#e6e8ec] rounded-[8px] px-[10px] py-[8px] text-[12.5px]"
                placeholder="Reason for rejection (required)"
                rows={2}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
              <div className="flex gap-[8px]">
                <button
                  type="button"
                  disabled={busy || !comment.trim() || !canAct}
                  onClick={() => decide("rejected")}
                  className="flex-1 bg-[#c0362c] rounded-[8px] py-[9px] text-[12.5px] font-semibold text-white hover:brightness-[1.08] disabled:opacity-50"
                >
                  {busy ? "Rejecting…" : "Confirm reject"}
                </button>
                <button type="button" onClick={() => setRejecting(false)} className="flex-1 border border-[#e6e8ec] rounded-[8px] py-[9px] text-[12.5px] font-semibold text-[#475467]">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="flex gap-[8px]">
              <button
                type="button"
                disabled={busy || !canAct}
                onClick={() => decide("approved")}
                className="flex-1 bg-[#3a5bd9] rounded-[8px] py-[9px] text-[12.5px] font-semibold text-white hover:brightness-[1.08] disabled:opacity-50"
              >
                {busy ? "Approving…" : "Approve current step"}
              </button>
              <button
                type="button"
                disabled={busy || !canAct}
                onClick={() => setRejecting(true)}
                className="flex-1 border border-[#c0362c] text-[#c0362c] rounded-[8px] py-[9px] text-[12.5px] font-semibold hover:bg-[#fbeceb] disabled:opacity-50"
              >
                Reject
              </button>
            </div>
          )}
        </div>
      )}
      {reviseTarget && <ReviseModal coId={coId} step={reviseTarget} onClose={() => setReviseTarget(null)} />}
    </div>
  );
}
