import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/**
 * Agent card — one tile in the "Agents tuned for you" 6-up grid.
 *
 * Three variants, all the same width:
 *   • real        — amber-50 → white gradient, REAL chip top-right, KB/Context tags
 *   • placeholder — opacity 0.7, neutral icon well, plain tags ("Skill", "Prompt")
 *   • custom      — dashed border, "Build your own" tile
 *
 * The REAL chip explicitly NOT a generic Badge — it's a tighter, square
 * marker used only here per handoff §06 ("REAL DATA" badges pattern).
 */

export type AgentTag = "KB" | "Context" | "Skill" | "Prompt";

const TAG_STYLE: Record<AgentTag, string> = {
  KB: "bg-purple-bg text-purple-fg",
  Context: "bg-ink-100 text-ink-500",
  Skill: "bg-ink-100 text-ink-500",
  Prompt: "bg-ink-100 text-ink-500",
};

function TagChip({ tag }: { tag: AgentTag }) {
  return (
    <span
      className={cn(
        "rounded-[3px] px-1.5 py-px text-[9px] font-medium",
        TAG_STYLE[tag],
      )}
    >
      {tag}
    </span>
  );
}

interface BaseAgent {
  icon: string;
  title: string;
  caption: string;
  value: string;
  tags: AgentTag[];
}

export interface RealAgentProps extends BaseAgent {
  variant: "real";
}

export interface PlaceholderAgentProps extends BaseAgent {
  variant: "placeholder";
}

export interface CustomAgentProps {
  variant: "custom";
  title: string;
  caption: string;
}

export type AgentCardProps =
  | RealAgentProps
  | PlaceholderAgentProps
  | CustomAgentProps;

export function AgentCard(props: AgentCardProps) {
  if (props.variant === "custom") {
    return (
      <Card
        data-state="custom"
        className="flex flex-col items-center justify-center gap-1.5 border-dashed border-ink-300 bg-ink-25 p-3.5 text-center"
      >
        <div
          aria-hidden
          className="grid h-8 w-8 place-items-center rounded-sm border border-dashed border-ink-300 bg-white"
        >
          <span
            className="material-icons-outlined text-brand-700"
            style={{ fontSize: 18 }}
          >
            add
          </span>
        </div>
        <div className="text-sm font-bold text-ink-900">{props.title}</div>
        <div className="text-[11px] text-ink-500">{props.caption}</div>
      </Card>
    );
  }

  const isReal = props.variant === "real";
  return (
    <Card
      data-state={props.variant}
      className={cn(
        "relative p-3.5",
        isReal
          ? "border-amber-200 bg-gradient-to-b from-amber-50 to-white from-0% to-30%"
          : "opacity-70",
      )}
    >
      {isReal ? (
        <span className="absolute right-2 top-2 rounded-[3px] bg-amber-500 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.05em] text-ink-900">
          REAL
        </span>
      ) : null}

      <div
        aria-hidden
        className={cn(
          "grid h-8 w-8 place-items-center rounded-sm",
          isReal ? "border border-ink-200 bg-white" : "bg-ink-50",
        )}
      >
        <span
          className={cn(
            "material-icons-outlined",
            isReal ? "text-brand-700" : "text-ink-500",
          )}
          style={{ fontSize: 16 }}
        >
          {props.icon}
        </span>
      </div>

      <div className="mt-2 text-[15px] font-bold text-ink-900">
        {props.title}
      </div>
      <div className="font-mono text-[11px] leading-snug text-ink-500">
        {props.caption}
        <br />
        <strong className="text-sm text-ink-900">{props.value}</strong>
      </div>

      {props.tags.length > 0 ? (
        <div className="mt-2 flex gap-1">
          {props.tags.map((tag) => (
            <TagChip key={tag} tag={tag} />
          ))}
        </div>
      ) : null}
    </Card>
  );
}
