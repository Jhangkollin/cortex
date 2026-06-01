import { expect, test } from "vitest";

import { BASE_DATA } from "../mock";

test("BASE_DATA shape", () => {
  expect(BASE_DATA.alerts).toHaveLength(3);
  expect(BASE_DATA.minis).toHaveLength(3);
  expect(BASE_DATA.funnel.blocks).toHaveLength(5);
  expect(BASE_DATA.funnel.arrows).toHaveLength(4);
  expect(BASE_DATA.minis[0].lab).toBe("Brand-cited answers");
  expect(BASE_DATA.minis[0].v).toBe("94"); // v1 bug fixed: not 284
  expect(BASE_DATA.funnel.blocks.filter((b) => b.here)).toHaveLength(1);
});
