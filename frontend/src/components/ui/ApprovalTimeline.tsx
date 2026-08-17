import type { ApprovalStepOut } from "@/lib/types";

const STATE_STYLE: Record<ApprovalStepOut["state"], { dotBg: string; dotBorder: string; tickColor: string; lineColor: string; titleColor: string; metaColor: string }> = {
  done: { dotBg: "#12805c", dotBorder: "#12805c", tickColor: "#fff", lineColor: "#12805c", titleColor: "#101828", metaColor: "#12805c" },
  current: { dotBg: "rgba(58,91,217,.14)", dotBorder: "#3a5bd9", tickColor: "#3a5bd9", lineColor: "#e6e8ec", titleColor: "#3a5bd9", metaColor: "#3a5bd9" },
  pending: { dotBg: "#fff", dotBorder: "#d5d9e0", tickColor: "#98a2b3", lineColor: "#e6e8ec", titleColor: "#98a2b3", metaColor: "#98a2b3" },
  rejected: { dotBg: "#c0362c", dotBorder: "#c0362c", tickColor: "#fff", lineColor: "#e6e8ec", titleColor: "#c0362c", metaColor: "#c0362c" },
  skipped: { dotBg: "#f0f1f4", dotBorder: "#d5d9e0", tickColor: "#98a2b3", lineColor: "#e6e8ec", titleColor: "#98a2b3", metaColor: "#98a2b3" },
};

export function ApprovalTimeline({
  steps,
  size = "md",
  onRevise,
  canRevise,
}: {
  steps: ApprovalStepOut[];
  size?: "md" | "sm";
  onRevise?: (step: ApprovalStepOut) => void;
  canRevise?: (step: ApprovalStepOut, index: number, steps: ApprovalStepOut[]) => boolean;
}) {
  const dotSize = size === "md" ? 26 : 24;
  return (
    <div>
      {steps.map((step, i) => {
        const style = STATE_STYLE[step.state];
        const isLast = i === steps.length - 1;
        const showRevise = !!onRevise && !!canRevise?.(step, i, steps);
        return (
          <div key={step.seq} className="flex gap-[14px]" style={{ paddingBottom: isLast ? 0 : size === "md" ? 20 : 16 }}>
            <div className="flex flex-col items-center flex-none">
              <div
                className="rounded-full flex items-center justify-center flex-none"
                style={{
                  width: dotSize,
                  height: dotSize,
                  background: style.dotBg,
                  border: `2px solid ${style.dotBorder}`,
                }}
              >
                {step.state === "done" && <span style={{ color: style.tickColor, fontSize: 13, fontWeight: 700 }}>✓</span>}
                {step.state === "rejected" && <span style={{ color: style.tickColor, fontSize: 13, fontWeight: 700 }}>✕</span>}
              </div>
              {!isLast && (
                <div
                  className="w-[2px] flex-1 mt-[3px]"
                  style={{ background: isLast ? "transparent" : style.lineColor, minHeight: size === "md" ? 14 : 12 }}
                />
              )}
            </div>
            <div className="pt-[1px]">
              <div className="font-semibold" style={{ fontSize: size === "md" ? 13 : 12.5, color: style.titleColor }}>
                {step.role}
              </div>
              <div className="text-[#667085]" style={{ fontSize: size === "md" ? 12 : 11.5 }}>
                {step.name}
              </div>
              <div className="font-medium mt-[3px]" style={{ fontSize: 11, color: style.metaColor }}>
                {step.meta}
              </div>
              {step.actedBy && (
                <div className="text-[#98a2b3] mt-[2px]" style={{ fontSize: 10.5 }}>
                  {step.decision === "rejected" ? "Rejected" : "Approved"} by {step.actedBy}
                  {step.actedAt ? ` · ${new Date(step.actedAt).toLocaleDateString()}` : ""}
                </div>
              )}
              {showRevise && (
                <button
                  type="button"
                  onClick={() => onRevise?.(step)}
                  className="mt-[4px] text-[10.5px] font-semibold text-[#3a5bd9] hover:underline"
                >
                  Change decision
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
