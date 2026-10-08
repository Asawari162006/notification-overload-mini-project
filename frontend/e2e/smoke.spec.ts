import { test, expect } from "@playwright/test";
test("production research screens, prediction, replay and grouping", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await expect(page.getByText("Local model · trained")).toBeVisible();
  await expect(page.getByText("176,195", { exact: true })).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "../artifacts/desktop-overview.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /Dataset audit$/ }).click();
  await expect(page.getByText("Provenance", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /Exploratory analysis$/ }).click();
  await expect(
    page.getByText("Observed duration distribution", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Model comparison$/ }).click();
  await expect(
    page.getByRole("heading", {
      name: "Baseline and model results · original seconds",
    }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Experiment", exact: true })
    .selectOption("B");
  await expect(page.getByText("global_median", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /Prediction$/ }).click();
  await page
    .getByRole("button", { name: "Predict recorded removal duration" })
    .click();
  await expect(page.getByText(/Version: mini-project-v1-B/)).toBeVisible();
  await page.getByRole("button", { name: /Historical replay$/ }).click();
  await expect(
    page.getByText("REAL HISTORICAL EVENTS · VIRTUAL CLOCK"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Next event", exact: true }).click();
  await page.getByRole("button", { name: /Load analysis$/ }).click();
  await expect(
    page.getByText("Unusual periods · first 100 posting cutoffs"),
  ).toBeVisible();
  await page.getByRole("button", { name: /Management simulator$/ }).click();
  await page
    .getByRole("button", { name: "Reset + seed synthetic demo" })
    .click();
  await expect(
    page.getByText("Synthetic demonstration 1", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Advance 5 minutes" }).click();
  await expect(
    page.getByText("synthetic:digest:300", { exact: true }),
  ).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "../artifacts/desktop-simulator.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /Preferences$/ }).click();
  await expect(
    page.getByRole("button", { name: "Save persistent preferences" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Model card$/ }).click();
  await expect(
    page.getByText("Removal does not prove reading, attention or importance.", {
      exact: true,
    }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
test("narrow layout remains readable and navigable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText("Local model · trained")).toBeVisible();
  expect(
    await page.locator("body").evaluate((el) => el.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "../artifacts/narrow-overview.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /Prediction$/ }).click();
  await page
    .getByRole("button", { name: "Predict recorded removal duration" })
    .click();
  await expect(page.getByText(/Version: mini-project-v1-B/)).toBeVisible();
  expect(
    await page.locator("body").evaluate((el) => el.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "../artifacts/narrow-prediction.png",
    fullPage: true,
  });
});
