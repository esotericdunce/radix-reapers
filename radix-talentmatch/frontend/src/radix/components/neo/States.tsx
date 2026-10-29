import { useNavigate } from '../../router';
import { NeoButton } from './NeoButton';

export function SkeletonBlock({ className = '' }: { className?: string }) {
  return <div className={`skeleton-shimmer border border-border bg-surface ${className}`} />;
}

export function ErrorState({ message, onRetry }: { message?: string; onRetry: () => void }) {
  return (
    <div className="plinth mx-auto my-16 max-w-md p-8 text-center">
      <p className="eyebrow">Connection lost</p>
      <h2 className="mt-3 font-display text-3xl">Couldn't load this.</h2>
      <p className="mt-2 text-sm text-muted-foreground">{message || "The data source didn't respond."}</p>
      <div className="mt-6 flex justify-center">
        <NeoButton onClick={onRetry}>Try again</NeoButton>
      </div>
    </div>
  );
}

export function EmptyState({ eyebrow, title, detail, actionLabel }: { eyebrow: string; title: string; detail: string; actionLabel?: string }) {
  const navigate = useNavigate();
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center px-6 py-28 text-center">
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="mt-4 font-display text-5xl leading-none">{title}</h2>
      <p className="mt-4 text-muted-foreground">{detail}</p>
      {actionLabel && (
        <div className="mt-8">
          <NeoButton showArrow onClick={() => navigate('/')}>
            {actionLabel}
          </NeoButton>
        </div>
      )}
    </div>
  );
}
