import type { ApprovalStepOut } from "@/lib/types";

const STATE_STYLE: Record<ApprovalStepOut["state"], { dotBg: string; dotBorder: string; tickColor: string; lineColor: string; titleColor: string; metaColor: string }> = {
  done: { dotBg: "#12805c", dotBorder: "#12805c", tickColor: "#fff", lineColor: "#12805c", titleColor: "#101828", metaColor: "#12805c" },
  current: { dotBg: "rgba(58,91,217,.14)", dotBorder: "#3a5bd9", tickColor: "#3a5bd9", lineColor: "#e6e8ec", titleColor: "#3a5bd9", metaColor: "#3a5bd9" },
  pending: { dotBg: "#fff", dotBorder: "#d5d9e0", tickColor: "#98a2b3", lineColor: "#e6e8ec", titleColor: "#98a2b3", metaColor: "#98a2b3" },
};

export function ApprovalTimeline({ steps, size = "md" }: { steps: ApprovalStepOut[]; size?: "md" | "sm" }) {
  const dotSize = size === "md" ? 26 : 24;
  return (
    <div>
      {steps.map((step, i) => {
        const style = STATE_STYLE[step.state];
        const isLast = i === steps.length - 1;
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
            </div>
          </div>
        );
      })}
    </div>
  );
}
