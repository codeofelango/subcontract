"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { approveMatched, raiseDispute } from "@/lib/api";

export function ManpowerActions({ contractId, period, matchedTotal }: { contractId: string; period: string; matchedTotal: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function onApprove() {
    setBusy(true);
    try {
      const res = await approveMatched(contractId, period);
      setMessage(`Approved matched lines — ${res.amountPaid} paid.`);
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  async function onDispute() {
    setBusy(true);
    try {
      await raiseDispute(contractId, period);
      setMessage("Dispute raised for variance lines.");
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex gap-[12px] items-center">
      {message && <span className="text-[12.5px] text-[#12805c] font-medium">{message}</span>}
      <div className="flex-1" />
      <button
        type="button"
        onClick={onDispute}
        disabled={busy}
        className="bg-white border border-[#e6e8ec] rounded-[8px] px-[16px] py-[11px] text-[13px] font-semibold text-[#475467] disabled:opacity-50"
      >
        Raise Dispute
      </button>
      <button
        type="button"
        onClick={onApprove}
        disabled={busy}
        className="bg-[#3a5bd9] rounded-[8px] px-[16px] py-[11px] text-[13px] font-semibold text-white hover:brightness-[1.08] disabled:opacity-50"
      >
        Approve Matched ({matchedTotal})
      </button>
    </div>
  );
}
