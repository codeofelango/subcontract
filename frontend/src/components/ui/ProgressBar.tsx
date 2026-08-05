export function ProgressBar({
  width,
  color,
  height = 8,
  track = "#f0f1f4",
}: {
  width: string;
  color: string;
  height?: number;
  track?: string;
}) {
  return (
    <div className="rounded-[6px] overflow-hidden" style={{ height, background: track }}>
      <div className="h-full rounded-[6px]" style={{ width, background: color }} />
    </div>
  );
}
