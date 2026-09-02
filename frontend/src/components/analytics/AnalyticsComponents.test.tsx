import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { KpiCard, AnalyticsSection, ChartContainer, EmptyState, ErrorState, LoadingState } from "./AnalyticsComponents";

describe("KpiCard", () => {
  it("renders label and value", () => {
    render(<KpiCard label="Cash" value="$100,000" />);
    expect(screen.getByText("Cash")).toBeInTheDocument();
    expect(screen.getByText("$100,000")).toBeInTheDocument();
  });

  it("renders subtitle when provided", () => {
    render(<KpiCard label="Revenue" value="$50,000" subtitle="Monthly" />);
    expect(screen.getByText("Monthly")).toBeInTheDocument();
  });

  it("renders trend value when provided", () => {
    render(<KpiCard label="Growth" value="10%" trend="up" trendValue="5%" />);
    expect(screen.getByText("+5%")).toBeInTheDocument();
  });

  it("applies custom color class", () => {
    const { container } = render(<KpiCard label="Cash" value="$100" color="text-emerald-400" />);
    expect(container.querySelector(".text-emerald-400")).toBeInTheDocument();
  });
});

describe("AnalyticsSection", () => {
  it("renders title", () => {
    render(<AnalyticsSection title="Financials"><div>content</div></AnalyticsSection>);
    expect(screen.getByText("Financials")).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(<AnalyticsSection title="Financials" description="Revenue and expenses"><div>content</div></AnalyticsSection>);
    expect(screen.getByText("Revenue and expenses")).toBeInTheDocument();
  });

  it("renders children", () => {
    render(<AnalyticsSection title="Financials"><div data-testid="child">Chart</div></AnalyticsSection>);
    expect(screen.getByTestId("child")).toBeInTheDocument();
  });
});

describe("ChartContainer", () => {
  it("renders title", () => {
    render(<ChartContainer title="Revenue">chart content</ChartContainer>);
    expect(screen.getByText("Revenue")).toBeInTheDocument();
  });

  it("renders children when not loading/empty/error", () => {
    render(<ChartContainer title="Revenue"><div data-testid="chart">Chart</div></ChartContainer>);
    expect(screen.getByTestId("chart")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    render(<ChartContainer title="Revenue" loading={true}>chart</ChartContainer>);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<ChartContainer title="Revenue" empty={true}>chart</ChartContainer>);
    expect(screen.getByText("No data available")).toBeInTheDocument();
  });

  it("renders custom empty message", () => {
    render(<ChartContainer title="Revenue" empty={true} emptyMessage="No revenue yet">chart</ChartContainer>);
    expect(screen.getByText("No revenue yet")).toBeInTheDocument();
  });

  it("renders error state with retry button", () => {
    const onRetry = vi.fn();
    render(<ChartContainer title="Revenue" error="Failed to load" onRetry={onRetry}>chart</ChartContainer>);
    expect(screen.getByText("Failed to load")).toBeInTheDocument();
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("calls onRetry when retry button clicked", async () => {
    const onRetry = vi.fn();
    const userEvent = (await import("@testing-library/user-event")).default;
    render(<ChartContainer title="Revenue" error="Failed" onRetry={onRetry}>chart</ChartContainer>);
    await userEvent.click(screen.getByText("Retry"));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});

describe("EmptyState", () => {
  it("renders message", () => {
    render(<EmptyState message="No data" />);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(<EmptyState message="No data" description="Run simulation first" />);
    expect(screen.getByText("Run simulation first")).toBeInTheDocument();
  });
});

describe("ErrorState", () => {
  it("renders error message", () => {
    render(<ErrorState message="Failed to load" />);
    expect(screen.getByText("Failed to load")).toBeInTheDocument();
  });

  it("renders retry button when onRetry provided", () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Failed" onRetry={onRetry} />);
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("does not render retry button when onRetry not provided", () => {
    render(<ErrorState message="Failed" />);
    expect(screen.queryByText("Retry")).not.toBeInTheDocument();
  });
});

describe("LoadingState", () => {
  it("renders default message", () => {
    render(<LoadingState />);
    expect(screen.getByText("Loading analytics...")).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<LoadingState message="Fetching data..." />);
    expect(screen.getByText("Fetching data...")).toBeInTheDocument();
  });
});
