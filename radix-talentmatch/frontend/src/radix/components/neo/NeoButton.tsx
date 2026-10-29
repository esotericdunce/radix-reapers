import { Button } from '@cred/neopop-web/lib/components';
import type { ReactNode } from 'react';
import { neo } from '../../lib/neo-theme';
import { useTheme } from '../../hooks/use-theme';

type Tone = 'primary' | 'secondary' | 'signal';

interface Props {
  children: ReactNode;
  tone?: Tone;
  size?: 'big' | 'medium' | 'small';
  kind?: 'elevated' | 'flat' | 'link';
  fullWidth?: boolean;
  disabled?: boolean;
  showArrow?: boolean;
  onClick?: () => void;
  ariaLabel?: string;
}

/** Thin preset layer over NeoPOP's Button so every lifted button shares one look. */
export function NeoButton({
  children,
  tone = 'primary',
  size = 'medium',
  kind = 'elevated',
  fullWidth,
  disabled,
  showArrow,
  onClick,
  ariaLabel,
}: Props) {
  const { theme } = useTheme();
  const colorConfig =
    tone === 'signal'
      ? {
          backgroundColor: neo.signal,
          color: neo.bg,
          borderColor: neo.signal,
          edgeColors: { top: 'transparent', left: 'transparent', right: '#A6812C', bottom: '#6E5419' },
        }
      : undefined;

  return (
    <Button
      variant={tone === 'secondary' ? 'secondary' : 'primary'}
      kind={kind}
      size={size}
      colorMode={theme}
      fullWidth={!!fullWidth}
      disabled={!!disabled}
      showArrow={!!showArrow}
      {...(onClick ? { onClick } : {})}
      {...(ariaLabel ? { 'aria-label': ariaLabel } : {})}
      {...(colorConfig ? { colorConfig } : {})}
      style={{ fontFamily: 'var(--font-sans)', letterSpacing: '0.02em' }}
    >
      {children}
    </Button>
  );
}
