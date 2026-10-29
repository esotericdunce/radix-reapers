import { cn } from '../../lib/utils';

/** 10-segment proficiency meter. */
export function Meter({ value, tone = 'bg-primary', className }: { value: number; tone?: string; className?: string }) {
  return (
    <div className={cn('flex gap-[3px]', className)} role="meter" aria-valuemin={0} aria-valuemax={10} aria-valuenow={value}>
      {Array.from({ length: 10 }).map((_, i) => (
        <span
          key={i}
          className={cn('h-3 flex-1 transition-colors', i < value ? tone : 'bg-surface-2')}
          style={{ transitionDelay: `${i * 25}ms` }}
        />
      ))}
    </div>
  );
}
