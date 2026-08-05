export function Card({ children, className = "", padding = "18px" }: { children: React.ReactNode; className?: string; padding?: string }) {
  return (
    <div className={`bg-white border border-[#e6e8ec] rounded-[10px] ${className}`} style={{ padding }}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`px-[18px] py-[14px] border-b border-[#e6e8ec] flex items-center gap-[10px] ${className}`}>
      {children}
    </div>
  );
}
