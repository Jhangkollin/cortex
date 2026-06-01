import { Fragment, type ReactElement } from "react";

export type RichSpan = string | { b: string };
export type RichText = readonly RichSpan[];

export function Rich({ value }: { value: RichText }): ReactElement {
  return (
    <>
      {value.map((s, i) =>
        typeof s === "string" ? (
          <Fragment key={i}>{s}</Fragment>
        ) : (
          <b key={i}>{s.b}</b>
        ),
      )}
    </>
  );
}
