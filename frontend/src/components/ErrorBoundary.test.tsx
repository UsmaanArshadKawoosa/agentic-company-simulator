import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorBoundary } from "../components/ErrorBoundary";

function CrashingComponent() {
  throw new Error("Test crash");
  return null;
}

describe("ErrorBoundary", () => {
  it("renders children when no error occurs", () => {
    render(
      <ErrorBoundary>
        <div data-testid="child">OK</div>
      </ErrorBoundary>
    );
    expect(screen.getByTestId("child").textContent).toBe("OK");
  });

  it("renders error UI when a child throws", () => {
    render(
      <ErrorBoundary>
        <CrashingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText("Something went wrong")).toBeDefined();
    expect(screen.getByText("Reload")).toBeDefined();
  });
});
