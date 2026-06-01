import type { CSSProperties } from "react";

interface IconProps {
  name: string;
  size?: number;
  color?: string;
  style?: CSSProperties;
}

/**
 * Thin wrapper around Material Icons Outlined.
 * The icon font is loaded via tokens.css.
 */
export function Icon({ name, size = 16, color = "currentColor", style = {} }: IconProps) {
  return (
    <span
      className="material-icons-outlined"
      style={{ fontSize: size, color, lineHeight: 1, ...style }}
    >
      {name}
    </span>
  );
}
