import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Layout } from '../components/Layout';
import api from '../services/api';
import { FileText, Clock, CheckCircle2, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import { cn } from '../lib/utils';

export function Dashboard() {
    const navigate = useNavigate();

    const { data: papers, isLoading } = useQuery({
        queryKey: ['papers'],
        queryFn: async () => {
            const res = await api.get('/papers/');
            return res.data;
        }
    });

    return (
        <Layout>
            <div className="space-y-8 max-w-5xl mx-auto">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Research Dashboard</h1>
                        <p className="text-muted-foreground mt-1">Manage and view your analyzed papers.</p>
                    </div>
                    <button
                        onClick={() => navigate('/')}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
                    >
                        + New Analysis
                    </button>
                </div>

                {isLoading ? (
                    <div className="flex justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {papers?.length === 0 ? (
                            <div className="text-center py-12 border border-dashed border-border rounded-xl">
                                <p className="text-muted-foreground">No papers analyzed yet.</p>
                            </div>
                        ) : (
                            papers?.map((paper) => (
                                <div
                                    key={paper.id}
                                    onClick={() => navigate(`/report/${paper.id}`)}
                                    className="group flex items-center justify-between p-4 bg-card border border-border/50 rounded-xl hover:border-primary/50 cursor-pointer transition-all hover:bg-muted/30"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={cn(
                                            "p-2 rounded-lg",
                                            paper.status === 'completed' ? "bg-green-500/10 text-green-500" :
                                                paper.status === 'failed' ? "bg-red-500/10 text-red-500" :
                                                    "bg-blue-500/10 text-blue-500"
                                        )}>
                                            <FileText className="w-6 h-6" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-lg group-hover:text-primary transition-colors">
                                                {paper.title || "Untitled Paper"}
                                            </h3>
                                            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                                                <span>{paper.source_type}</span>
                                                <span>•</span>
                                                <span>{new Date(paper.created_at).toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2 text-sm">
                                            {paper.status === 'completed' ? (
                                                <span className="flex items-center gap-1 text-green-500">
                                                    <CheckCircle2 className="w-4 h-4" /> Completed
                                                </span>
                                            ) : paper.status === 'failed' ? (
                                                <span className="flex items-center gap-1 text-red-500">
                                                    <AlertCircle className="w-4 h-4" /> Failed
                                                </span>
                                            ) : (
                                                <span className="flex items-center gap-1 text-blue-500">
                                                    <Loader2 className="w-4 h-4 animate-spin" /> Processing
                                                </span>
                                            )}
                                        </div>
                                        <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}
            </div>
        </Layout>
    );
}
