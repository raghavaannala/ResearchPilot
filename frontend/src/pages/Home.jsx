import { Layout } from '../components/Layout';
import { UploadZone } from '../components/UploadZone';
import { motion } from 'framer-motion';

export function Home() {
    return (
        <Layout>
            <div className="flex flex-col items-center justify-center min-h-[80vh] space-y-12 text-center">
                <div className="space-y-6 max-w-3xl">
                    <h1 className="text-5xl md:text-7xl font-bold tracking-tight bg-gradient-to-r from-white via-white/80 to-white/60 bg-clip-text text-transparent">
                        Research Intelligence <br />
                        <span className="text-primary">Redefined.</span>
                    </h1>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                        Upload any research paper and let our multi-agent AI system break it down into insights, code prototypes, and simplified explanations.
                    </p>
                </div>

                <div className="w-full max-w-3xl animate-in fade-in slide-in-from-bottom-8 duration-1000">
                    <div className="p-1 rounded-2xl bg-gradient-to-b from-white/10 to-transparent">
                        <div className="bg-card/50 backdrop-blur-sm border border-white/5 rounded-xl p-8 shadow-2xl ring-1 ring-white/5">
                            <UploadZone />
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left max-w-5xl w-full pt-12 border-t border-white/5">
                    <div className="space-y-2">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-4">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold">Instant Analysis</h3>
                        <p className="text-sm text-muted-foreground">
                            Get comprehensive breakdowns of methodology, results, and gaps in seconds.
                        </p>
                    </div>
                    <div className="space-y-2">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-4">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold">Code Generation</h3>
                        <p className="text-sm text-muted-foreground">
                            Automatically generate Python prototypes based on the paper's algorithms.
                        </p>
                    </div>
                    <div className="space-y-2">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-4">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold">Simplified Explanations</h3>
                        <p className="text-sm text-muted-foreground">
                            Understand complex concepts with ELI5 style breakdowns and key takeaways.
                        </p>
                    </div>
                </div>
            </div>
        </Layout>
    );
}
