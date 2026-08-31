import { CommandCenter } from "./CommandCenter";

export function Simulation({ companyId }: { companyId: number }) {
  return <CommandCenter companyId={companyId} />;
}
