import { describe, it, expect, vi, afterEach } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import App from "./App";
import { api, formatSeconds } from "./api";
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
describe("units and API", () => {
  it("formats seconds without invented accuracy", () => {
    expect(formatSeconds(120)).toBe("2.0 min");
    expect(formatSeconds(null)).toBe("Unavailable");
    expect(formatSeconds(3600)).toBe("1.0 hr");
  });
  it("shows server validation errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({
          ok: false,
          json: async () => ({ detail: "Clock must be monotonic" }),
        }),
    );
    await expect(api("simulator/clock", "POST", { time: 0 })).rejects.toThrow(
      "Clock must be monotonic",
    );
  });
});
describe("functional screens", () => {
  it("loads overview and switches to backend prediction", async () => {
    const fetcher = vi
      .fn()
      .mockImplementation(async (url: string) => ({
        ok: true,
        json: async () =>
          url.includes("/predict")
            ? {
                predicted_duration: 120,
                model_status: "trained",
                model_version: "test-v1",
                fallback_information: ["No history"],
              }
            : {
                dataset: "verified real dataset",
                model_status: "trained",
                model: { model: "ridge" },
                audit: {
                  raw_rows: 176195,
                  usable_samples: 10,
                  participants: 14,
                  endpoints: [],
                },
              },
      }));
    vi.stubGlobal("fetch", fetcher);
    render(<App />);
    await screen.findByText("176,195");
    fireEvent.click(screen.getByRole("button", { name: /Prediction$/ }));
    await screen.findByRole("button", {
      name: "Predict recorded removal duration",
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Predict recorded removal duration" }),
    );
    await screen.findByText("2.0 min");
    expect(fetcher.mock.calls.some((c) => c[0] === "/api/predict")).toBe(true);
  });
  it("shows retryable error on backend failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("offline");
    expect(screen.getByRole("button", { name: "Refresh" })).toBeEnabled();
  });
  it("keeps reserved interfaces absent", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({
          ok: true,
          json: async () => ({ model_status: "unavailable" }),
        }),
    );
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Model · unavailable")).toBeInTheDocument(),
    );
    expect(screen.queryByText(/what-if explorer/i)).toBeNull();
  });
});
