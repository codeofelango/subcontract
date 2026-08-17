"use client";

import { Suspense, useEffect, useState } from "react";
import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { getQuickLoginOptions } from "@/lib/api";
import type { QuickLoginOption, QuickLoginSlot } from "@/lib/types";

function QuickLoginRow() {
  const [options, setOptions] = useState<QuickLoginOption[] | null>(null);
  const [pending, setPending] = useState<QuickLoginSlot | null>(null);

  useEffect(() => {
    getQuickLoginOptions()
      .then((res) => setOptions(res.enabled ? res.options : []))
      .catch(() => setOptions([]));
  }, []);

  if (!options || options.length === 0) return null;

  async function quickSignIn(slot: QuickLoginSlot) {
    setPending(slot);
    await signIn("quick-login", { slot, callbackUrl: "/dashboard" });
  }

  return (
    <div className="mt-[20px] pt-[18px] border-t border-[#f0f1f4]">
      <p className="text-[11.5px] font-semibold text-[#98a2b3] uppercase tracking-[.04em] mb-[10px]">Quick login for testing</p>
      <div className="flex flex-col gap-[8px]">
        {options.map((opt) => (
          <button
            key={opt.slot}
            type="button"
            disabled={!opt.user || pending !== null}
            onClick={() => quickSignIn(opt.slot)}
            className="w-full flex items-center justify-between gap-[10px] bg-white border border-[#e6e8ec] rounded-[8px] px-[12px] py-[9px] text-left text-[12.5px] hover:border-[#3a5bd9] disabled:opacity-40 disabled:hover:border-[#e6e8ec]"
          >
            <span>
              <span className="font-semibold text-[#101828]">{opt.label}</span>
              <span className="text-[#98a2b3]"> — {opt.user ? opt.user.name : "not set"}</span>
            </span>
            {pending === opt.slot && <span className="text-[#98a2b3] text-[11px]">Signing in…</span>}
          </button>
        ))}
      </div>
      <p className="text-[11px] text-[#98a2b3] mt-[8px]">Set on the Users page — an Admin can move which account backs each button.</p>
    </div>
  );
}

function LoginCard() {
  const params = useSearchParams();
  const hasError = !!params.get("error");

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="w-full max-w-[380px] bg-white border border-[#e6e8ec] rounded-[10px] p-[28px]">
        <div className="w-[40px] h-[40px] rounded-[9px] bg-[#3a5bd9] flex items-center justify-center mb-[16px]">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
            <path d="M4 7h16M4 12h16M4 17h10" />
          </svg>
        </div>
        <h1 className="text-[18px] font-bold tracking-[-0.01em] text-[#101828]">Subcontract Management Module</h1>
        <p className="text-[13px] text-[#667085] mt-[4px] mb-[20px]">Sign in with your Microsoft work account to continue.</p>

        {hasError && (
          <div className="mb-[16px] text-[12.5px] text-[#c0362c] bg-[#fbeceb] border border-[#f3d4d1] rounded-[8px] px-[12px] py-[9px]">
            Your account isn&apos;t set up yet, or sign-in failed. Contact an Admin to be added to the User Master with a role.
          </div>
        )}

        <button
          type="button"
          onClick={() => signIn("azure-ad", { callbackUrl: "/dashboard" })}
          className="w-full flex items-center justify-center gap-[10px] bg-[#3a5bd9] text-white rounded-[8px] px-[14px] py-[11px] text-[13.5px] font-semibold hover:brightness-[1.08]"
        >
          <svg width="16" height="16" viewBox="0 0 23 23" aria-hidden="true">
            <path fill="#f25022" d="M1 1h10v10H1z" />
            <path fill="#00a4ef" d="M1 12h10v10H1z" />
            <path fill="#7fba00" d="M12 1h10v10H12z" />
            <path fill="#ffb900" d="M12 12h10v10H12z" />
          </svg>
          Sign in with Microsoft
        </button>

        <QuickLoginRow />
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginCard />
    </Suspense>
  );
}
