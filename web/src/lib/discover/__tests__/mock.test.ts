import { expect, test } from "vitest";

import { BASE_DATA } from "../mock";

test("BASE_DATA shape", () => {
  expect(BASE_DATA.alerts).toHaveLength(3);
  expect(BASE_DATA.kpis).toHaveLength(4);
  expect(BASE_DATA.funnel.blocks).toHaveLength(5);
  expect(BASE_DATA.funnel.arrows).toHaveLength(4);
  expect(BASE_DATA.kpis[0].lab).toBe("相關問題數 (TOP 500 樣樣)");
  expect(BASE_DATA.kpis[0].v).toBe("48");
  expect(BASE_DATA.funnel.blocks.filter((b) => b.here)).toHaveLength(1);
  expect(BASE_DATA.questions).toHaveLength(10);
  expect(BASE_DATA.intent.rows).toHaveLength(10);
});
