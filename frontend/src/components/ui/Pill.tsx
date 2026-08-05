export function Pill({ color, bg, children }: { color: string; bg: string; children: React.ReactNode }) {
  return (
    <span
      className="inline-flex items-center rounded-[20px] px-[9px] py-[3px] text-[11px] font-semibold"
      style={{ color, background: bg }}
    >
      {children}
    </span>
  );
}
