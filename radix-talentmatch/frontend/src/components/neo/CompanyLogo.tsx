import { useState } from 'react';
import { cn } from '../../lib/utils';

const SIZES = { sm: 'h-8 w-8 text-sm', md: 'h-11 w-11 text-lg', lg: 'h-14 w-14 text-2xl', xl: 'h-20 w-20 text-4xl' };

export function CompanyLogo({
  name,
  logoUrl,
  websiteUrl,
  size = 'md',
  className,
}: {
  name: string;
  logoUrl?: string;
  websiteUrl?: string;
  size?: keyof typeof SIZES;
  className?: string;
}) {
  const [stage, setStage] = useState(0);
  let domain = '';
  if (websiteUrl) {
    try {
      domain = new URL(websiteUrl.startsWith('http') ? websiteUrl : `https://${websiteUrl}`).hostname.replace(/^www\./, '');
    } catch {
      /* ignore */
    }
  }
  const key = import.meta.env.VITE_LOGO_DEV_PUBLISHABLE_KEY as string | undefined;
  const sources = [
    key && domain ? `https://img.logo.dev/${domain}?token=${key}&size=128&format=png` : '',
    logoUrl || '',
    domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=128` : '',
  ].filter(Boolean);
  const src = sources[stage];

  return (
    <div
      className={cn(
        'flex shrink-0 items-center justify-center overflow-hidden border border-border-strong bg-primary',
        SIZES[size],
        className,
      )}
      style={{ borderRadius: 'var(--radius)' }}
    >
      {src ? (
        <img
          src={src}
          alt={`${name} logo`}
          loading="lazy"
          className="h-full w-full object-contain p-1.5"
          onError={() => setStage((s) => s + 1)}
        />
      ) : (
        <span className="font-display text-primary-foreground">{(name || 'C').charAt(0)}</span>
      )}
    </div>
  );
}
