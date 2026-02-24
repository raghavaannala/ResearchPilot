import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Layout } from '../components/Layout';
import { ThinkingProcess } from '../components/ThinkingProcess';
import { KnowledgeCard, Explanation, CodePrototype, RelatedPapers } from '../components/AnalysisSections';
import api from '../services/api';
import { AlertCircle, FileText, ArrowLeft, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

export function Report() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [pipelineEvents, setPipelineEvents] = useState([]);
    const [streamStatus, setStreamStatus] = useState('connecting'); // connecting, active, done, failed

    // Fetch Paper Details
    const { data: paper, isLoading: isPaperLoading, error: paperError } = useQuery({
        queryKey: ['paper', id],
        queryFn: async () => {
            const res = await api.get(`/papers/${id}`);
            return res.data;
        }
    });

    // Fetch Analysis Results (enabled only if status is completed or we get a done signal)
    const { data: analysis, refetch: refetchAnalysis } = useQuery({
        queryKey: ['analysis', id],
        queryFn: async () => {
            const res = await api.get(`/papers/${id}/analysis`);
            return res.data;
        },
        enabled: paper?.status === 'completed' || streamStatus === 'done',
        retry: false
    });

    // SSE Effect
    useEffect(() => {
        if (!id || paper?.status === 'completed') {
            setStreamStatus('done');
            return;
        }

        const eventSource = new EventSource(`http://localhost:8000/api/v1/papers/${id}/stream`);

        eventSource.onopen = () => {
            setStreamStatus('active');
        };

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // Check for completion signals
                if (data.stage === 'complete') {
                    setStreamStatus(data.status); // 'done' or 'failed'
                    eventSource.close();
                    if (data.status === 'done') {
                        refetchAnalysis();
                    }
                    return;
                }

                // Add to events list
                setPipelineEvents((prev) => [...prev, { ...data, timestamp: new Date() }]);

            } catch (err) {
                console.error('Error parsing SSE data', err);
            }
        };

        eventSource.onerror = (err) => {
            console.error('SSE Error', err);
            eventSource.close();
            setStreamStatus('failed'); // Or just disconnected
        };

        return () => {
            eventSource.close();
        };
    }, [id, paper?.status, refetchAnalysis]);


    if (isPaperLoading) {
        return (
            <Layout>
                <div className="flex items-center justify-center min-h-[50vh]">
                    <RefreshCw className="w-8 h-8 animate-spin text-primary" />
                </div>
            </Layout>
        );
    }

    if (paperError) {
        return (
            <Layout>
                <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-4">
                    <AlertCircle className="w-12 h-12 text-destructive" />
                    <h2 className="text-2xl font-bold">Paper Not Found</h2>
                    <p className="text-muted-foreground">The paper you are looking for does not exist or an error occurred.</p>
                    <button
                        onClick={() => navigate('/')}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
                    >
                        Go Home
                    </button>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <div className="space-y-4">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4 mr-1" /> Back to Dashboard
                    </button>

                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <h1 className="text-3xl font-bold">{paper.title || "Processing Paper..."}</h1>
                            <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                                <FileText className="w-4 h-4" />
                                <span>{paper.source_type?.toUpperCase()}</span>
                                <span>•</span>
                                <span>{new Date(paper.created_at).toLocaleDateString()}</span>
                                <span>•</span>
                                <span className={cn(
                                    "px-2 py-0.5 rounded-full text-xs font-medium capitalize",
                                    paper.status === 'completed' ? "bg-green-500/10 text-green-500" :
                                        paper.status === 'failed' ? "bg-red-500/10 text-red-500" :
                                            "bg-blue-500/10 text-blue-500"
                                )}>
                                    {streamStatus === 'done' ? 'Completed' : paper.status}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Live Thinking Process (Visible while processing) */}
                {streamStatus !== 'done' && streamStatus !== 'failed' && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="mb-8"
                    >
                        <ThinkingProcess events={pipelineEvents} />
                    </motion.div>
                )}

                {/* Results Grid */}
                {analysis ? (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="grid grid-cols-1 md:grid-cols-2 gap-6"
                    >
                        <div className="space-y-6">
                            <KnowledgeCard data={analysis.knowledge_card} />
                            <Explanation data={analysis.explanations} />
                            <div className="p-6 bg-card border border-border/50 rounded-xl space-y-4">
                                <h3 className="text-lg font-semibold flex items-center gap-2">
                                    <ListChecks className="w-5 h-5 text-orange-500" />
                                    Gap Analysis
                                </h3>
                                <div className="prose prose-invert prose-sm max-w-none text-muted-foreground">
                                    {typeof analysis.gap_analysis === 'string' ? analysis.gap_analysis : JSON.stringify(analysis.gap_analysis)}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-6">
                            <CodePrototype data={analysis.code_prototype} />
                            <div className="p-6 bg-card border border-border/50 rounded-xl space-y-4">
                                <h3 className="text-lg font-semibold flex items-center gap-2">
                                    <BookOpen className="w-5 h-5 text-indigo-500" />
                                    Literature Review
                                </h3>
                                <div className="prose prose-invert prose-sm max-w-none text-muted-foreground">
                                    {typeof analysis.literature_review === 'string' ? analysis.literature_review : JSON.stringify(analysis.literature_review)}
                                </div>
                            </div>
                            <RelatedPapers data={analysis.related_papers} />
                        </div>
                    </motion.div>
                ) : (
                    streamStatus === 'done' && (
                        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                            <p>Analysis complete. Rendering results...</p>
                            <button onClick={() => refetchAnalysis()} className="mt-4 text-primary hover:underline">
                                Click here if results don't appear
                            </button>
                        </div>
                    )
                )}
            </div>
        </Layout>
    );
}
