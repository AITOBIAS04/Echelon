import React from "react";

type Props = { children: React.ReactNode; name?: string };

type State = { hasError: boolean; message: string };

export class LocalErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return { hasError: true, message };
  }

  componentDidCatch(err: unknown) {
    // Keep console useful during demo dev
    // eslint-disable-next-line no-console
    console.error(`[LocalErrorBoundary${this.props.name ? `:${this.props.name}` : ""}]`, err);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="p-6">
        <div className="bg-terminal-card border border-status-danger/30 rounded-lg p-4">
          <div className="text-sm font-semibold text-terminal-text mb-1">
            Panel crashed{this.props.name ? `: ${this.props.name}` : ""}
          </div>
          <div className="text-xs text-terminal-text-secondary font-mono whitespace-pre-wrap">
            {this.state.message}
          </div>
        </div>
      </div>
    );
  }
}
