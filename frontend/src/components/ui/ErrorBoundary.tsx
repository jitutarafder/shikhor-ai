import { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "./Button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (process.env.NODE_ENV !== "production") {
      console.error("ErrorBoundary caught:", error, errorInfo);
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[300px] p-6 flex flex-col items-center justify-center text-center bg-red-50/50 rounded-2xl border border-red-200 m-4">
          <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center text-red-600 mb-4">
            <AlertTriangle className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-800 mb-2">
            কিছু একটা সমস্যা হয়েছে
          </h2>
          <p className="text-sm text-slate-600 max-w-md mb-6">
            পৃষ্ঠাটি লোড করতে অপ্রত্যাশিত ত্রুটি দেখা দিয়েছে। অনুগ্রহ করে পৃষ্ঠাটি পুনরায় লোড করুন।
          </p>
          <Button
            onClick={this.handleReset}
            className="flex items-center gap-2 bg-emerald-700 hover:bg-emerald-800 text-white"
          >
            <RefreshCw className="w-4 h-4" />
            পুনরায় চেষ্টা করুন
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
