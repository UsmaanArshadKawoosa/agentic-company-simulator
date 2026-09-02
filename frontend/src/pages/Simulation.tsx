import { CommandCenter } from "./CommandCenter";

export function Simulation({
  companyId,
  onOpenAnalytics,
  onOpenTimeline,
}: {
  companyId: number;
  onOpenAnalytics: (id: number) => void;
  onOpenTimeline: (id: number) => void;
}) {
  return (
    <CommandCenter
      companyId={companyId}
      onOpenAnalytics={() => onOpenAnalytics(companyId)}
      onOpenTimeline={() => onOpenTimeline(companyId)}
    />
  );
}
