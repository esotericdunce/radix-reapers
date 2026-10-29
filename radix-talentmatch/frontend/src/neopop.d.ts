declare module '@cred/neopop-web/lib/components' {
  import type { ComponentType, ReactNode, CSSProperties } from 'react';

  export type EdgeColors = { top?: string; left?: string; right?: string; bottom?: string; topRight?: string; bottomRight?: string; bottomLeft?: string; topLeft?: string };

  export type ElevatedCardProps = {
    backgroundColor?: string;
    edgeColors?: EdgeColors;
    lineWidth?: string;
    fullWidth?: boolean;
    style?: CSSProperties;
    className?: string;
    children?: ReactNode;
  };
  export const ElevatedCard: ComponentType<ElevatedCardProps>;

  export type ColorConfig = {
    backgroundColor?: string;
    color?: string;
    borderColor?: string;
    edgeColors?: EdgeColors;
  };

  export type NeoButtonProps = {
    label?: string;
    kind?: 'elevated' | 'flat' | 'link';
    tone?: string;
    variant?: 'primary' | 'secondary';
    colorMode?: 'dark' | 'light';
    size?: 'big' | 'medium' | 'small';
    showArrow?: boolean;
    disabled?: boolean;
    fullWidth?: boolean;
    colorConfig?: ColorConfig;
    onClick?: () => void;
    className?: string;
    style?: CSSProperties;
    'aria-label'?: string;
    children?: ReactNode;
  };
  export const Button: ComponentType<NeoButtonProps>;
}
