import { motion } from 'framer-motion';
import { BookOpen, FileCode, Lightbulb, Link as LinkIcon, ListChecks } from 'lucide-react';
import { cn } from '../lib/utils';

export function KnowledgeCard({ data }) {
    if (!data) return null;
    return (
        <div className="bg-card border border-border/50 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
                <h3 className="text-lg font-semibold">Key Insights</h3>
            </div>
            <div className="prose prose-invert prose-sm max-w-none">
                {/* Render markdown or structured data here. For now assuming simple text/list */}
                <div className="whitespace-pre-wrap text-muted-foreground">
                    {typeof data === 'string' ? data : JSON.stringify(data, null, 2)}
                </div>
            </div>
        </div>
    );
}

export function Explanation({ data }) {
    if (!data) return null;
    return (
        <div className="bg-card border border-border/50 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2 mb-2">
                <BookOpen className="w-5 h-5 text-blue-500" />
                <h3 className="text-lg font-semibold">Simplified Explanation</h3>
            </div>
            <div className="text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {typeof data === 'string' ? data : JSON.stringify(data, null, 2)}
            </div>
        </div>
    );
}

export function CodePrototype({ data }) {
    if (!data) return null;
    return (
        <div className="bg-card border border-border/50 rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 p-4 bg-muted/30 border-b border-border/50">
                <FileCode className="w-5 h-5 text-green-500" />
                <h3 className="text-lg font-semibold">Code Prototype</h3>
            </div>
            <div className="p-4 bg-slate-950 overflow-x-auto">
                <pre className="text-sm font-mono text-slate-300">
                    <code>
                        {typeof data === 'string' ? data : (data.code || JSON.stringify(data, null, 2))}
                    </code>
                </pre>
            </div>
        </div>
    );
}

export function RelatedPapers({ data }) {
    if (!data || !Array.isArray(data) || data.length === 0) return null;
    return (
        <div className="bg-card border border-border/50 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2 mb-2">
                <LinkIcon className="w-5 h-5 text-purple-500" />
                <h3 className="text-lg font-semibold">Related Research</h3>
            </div>
            <ul className="space-y-3">
                {data.map((paper, i) => (
                    <li key={i} className="group flex flex-col gap-1 p-3 rounded-lg hover:bg-muted/50 transition-colors">
                        <a href={paper.url} target="_blank" rel="noopener noreferrer" className="font-medium text-primary hover:underline underline-offset-4">
                            {paper.title}
                        </a>
                        <span className="text-xs text-muted-foreground">{paper.authors} • {paper.year}</span>
                    </li>
                ))}
            </ul>
        </div>
    );
}
