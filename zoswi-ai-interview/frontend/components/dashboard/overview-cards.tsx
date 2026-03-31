import { Card } from "@/components/ui/card";

type OverviewCardsProps = {
  items: Array<{ label: string; value: string | number; note?: string }>;
};

export function OverviewCards({ items }: OverviewCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <p className="text-sm text-slate-400">{item.label}</p>
          <p className="mt-2 text-2xl font-semibold text-white">{item.value}</p>
          {item.note ? <p className="mt-1 text-xs text-slate-500">{item.note}</p> : null}
        </Card>
      ))}
    </div>
  );
}

