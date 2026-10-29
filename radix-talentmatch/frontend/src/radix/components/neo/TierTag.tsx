import type { ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { tierClass } from '../../lib/tiers';

export function TierTag({ tier, className }: { tier?: string; className?: string }) {
  const t = tierClass(tier);
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center gap-1.5 border px-2 font-mono text-[0.65rem] uppercase tracking-[0.12em]',
        t.border,
        t.text,
        className,
      )}
    >
      <span className={cn('h-1.5 w-1.5', t.dot)} />
      {tier || 'Dream'}
    </span>
  );
}

export function MonoTag({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center border border-border-strong px-2 font-mono text-[0.65rem] uppercase tracking-[0.12em] text-muted-foreground',
        className,
      )}
    >
      {children}
    </span>
  );
}
