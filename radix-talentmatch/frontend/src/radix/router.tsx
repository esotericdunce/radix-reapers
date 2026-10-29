/**
 * Thin compatibility layer: the RADIX screens were written against
 * react-router-dom. This maps the tiny API surface they use onto TanStack Router.
 */
import {
  Link as TLink,
  useLocation as useTLocation,
  useNavigate as useTNavigate,
} from "@tanstack/react-router";
import type { AnchorHTMLAttributes, ReactNode } from "react";

type LinkProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & {
  to: string;
  children?: ReactNode;
};

export function Link({ to, children, ...rest }: LinkProps) {
  return (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    <TLink to={to as any} {...(rest as any)}>
      {children}
    </TLink>
  );
}

export function useLocation() {
  const loc = useTLocation();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const state = (loc.state as any)?.__radix ?? null;
  return { pathname: loc.pathname, state };
}

export function useNavigate() {
  const navigate = useTNavigate();
  return (to: string, opts?: { replace?: boolean; state?: unknown }) =>
    navigate({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      to: to as any,
      replace: opts?.replace ?? false,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      state: ((prev: any) => ({ ...prev, __radix: opts?.state ?? null })) as any,
    });
}
