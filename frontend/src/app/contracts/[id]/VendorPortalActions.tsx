"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { certifyVendorSubmission } from "@/lib/api";

export function CertifyButton({ contractId, submissionId }: { contractId: string; submissionId: number }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function onCertify() {
    setBusy(true);
    try {
      await certifyVendorSubmission(contractId, submissionId);
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={onCertify}
      disabled={busy}
      className="bg-[#3a5bd9] rounded-[7px] px-[12px] py-[6px] text-[12px] font-semibold text-white hover:brightness-[1.08] disabled:opacity-50"
    >
      {busy ? "Certifying…" : "Certify → Create IPC"}
    </button>
  );
}
