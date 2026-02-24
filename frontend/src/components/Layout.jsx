import { Header } from './Header';

export function Layout({ children }) {
    return (
        <div className="min-h-screen bg-background font-sans antialiased text-foreground">
            <Header />
            <main className="container pt-24 pb-12 px-4 md:px-6 mx-auto">
                {children}
            </main>
        </div>
    );
}
