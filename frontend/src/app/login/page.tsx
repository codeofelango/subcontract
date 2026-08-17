"use client";

import { Suspense } from "react";
import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";

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
