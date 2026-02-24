import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, CheckCircle2, AlertCircle, BrainCircuit } from 'lucide-react';
import { cn } from '../lib/utils';

export function ThinkingProcess({ events }) {
    // Sort events by timestamp or just display latest relevant ones
    // We want to show a live feed of what the agents are doing

    return (
        <div className="w-full bg-card/50 backdrop-blur border border-border/50 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-3 mb-4">
                <BrainCircuit className="w-6 h-6 text-primary animate-pulse" />
                <h3 className="text-lg font-semibold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
                    AI Analysis in Progress
                </h3>
            </div>

            <div className="space-y-3 max-h-[300px] overflow-y-auto custom-scrollbar pr-2">
                <AnimatePresence initial={false}>
                    {events.map((event, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10, x: -10 }}
                            animate={{ opacity: 1, y: 0, x: 0 }}
                            className={cn(
                                "flex items-start gap-3 p-3 rounded-lg text-sm border",
                                event.status === 'done' ? "bg-green-500/10 border-green-500/20 text-green-400" :
                                    event.status === 'failed' ? "bg-red-500/10 border-red-500/20 text-red-400" :
                                        "bg-secondary/50 border-border/50 text-muted-foreground"
                            )}
                        >
                            <div className="mt-0.5">
                                {event.status === 'done' ? (
                                    <CheckCircle2 className="w-4 h-4" />
                                ) : event.status === 'failed' ? (
                                    <AlertCircle className="w-4 h-4" />
                                ) : (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                )}
                            </div>
                            <div className="flex-1">
                                <p className="font-medium text-foreground/90">
                                    {event.agent ? `Agent: ${event.agent}` : 'System'}
                                </p>
                                <p>{event.message || event.detail || "Processing..."}</p>
                            </div>
                            {event.timestamp && (
                                <span className="text-xs text-muted-foreground/50 tabular-nums">
                                    {new Date(event.timestamp).toLocaleTimeString()}
                                </span>
                            )}
                        </motion.div>
                    ))}
                </AnimatePresence>

                {events.length === 0 && (
                    <div className="text-center text-muted-foreground py-8">
                        Waiting for analysis to start...
                    </div>
                )}
            </div>
        </div>
    );
}
