"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { advanceContractStep } from "@/lib/api";

export function ContractAdvanceButton({ contractId, hasCurrentStep }: { contractId: string; hasCurrentStep: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  if (!hasCurrentStep) return null;

  async function onAdvance() {
    setBusy(true);
    try {
      await advanceContractStep(contractId);
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={onAdvance}
      disabled={busy}
      className="mt-[10px] w-full bg-[#3a5bd9] rounded-[8px] py-[9px] text-[12.5px] font-semibold text-white hover:brightness-[1.08] disabled:opacity-50"
    >
      {busy ? "Advancing…" : "Approve current step"}
    </button>
  );
}
