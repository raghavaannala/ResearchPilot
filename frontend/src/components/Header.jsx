import { Link } from 'react-router-dom';
import { Sparkles, FileText, LayoutDashboard } from 'lucide-react';

export function Header() {
    return (
        <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-16 items-center justify-between px-4 md:px-6">
                <Link to="/" className="flex items-center gap-2 font-semibold">
                    <Sparkles className="h-6 w-6 text-primary" />
                    <span className="bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent text-xl font-bold">
                        ResearchPilot
                    </span>
                </Link>
                <nav className="flex items-center gap-6 text-sm font-medium">
                    <Link
                        to="/"
                        className="transition-colors hover:text-foreground/80 text-foreground/60"
                    >
                        New Analysis
                    </Link>
                    <Link
                        to="/dashboard"
                        className="transition-colors hover:text-foreground/80 text-foreground/60"
                    >
                        Dashboard
                    </Link>
                </nav>
            </div>
        </header>
    );
}
