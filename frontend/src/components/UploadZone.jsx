import { useState, useCallback } from 'react';
import { UploadCloud, Link as LinkIcon, FileText, Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

export function UploadZone() {
    const [isDragOver, setIsDragOver] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [inputType, setInputType] = useState('file'); // 'file' | 'url' | 'arxiv'
    const [inputValue, setInputValue] = useState('');
    const navigate = useNavigate();

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setIsDragOver(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        setIsDragOver(false);
    }, []);

    const handleDrop = useCallback(async (e) => {
        e.preventDefault();
        setIsDragOver(false);
        const files = e.dataTransfer.files;
        if (files?.length) {
            await handleFileUpload(files[0]);
        }
    }, []);

    const handleFileUpload = async (file) => {
        if (file.type !== 'application/pdf') {
            alert('Only PDF files are supported');
            return;
        }

        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const { data } = await api.post('/papers/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            navigate(`/report/${data.paper_id}`);
        } catch (error) {
            console.error('Upload failed', error);
            alert('Upload failed. Please try again.');
        } finally {
            setIsUploading(false);
        }
    };

    const handleInputSubmit = async (e) => {
        e.preventDefault();
        if (!inputValue) return;

        setIsUploading(true);
        const formData = new FormData();

        if (inputType === 'url') {
            formData.append('url', inputValue);
        } else if (inputType === 'arxiv') {
            formData.append('arxiv_id', inputValue);
        }

        try {
            const { data } = await api.post('/papers/', formData);
            navigate(`/report/${data.paper_id}`);
        } catch (error) {
            console.error('Submission failed', error);
            alert('Submission failed. Please try again.');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="w-full max-w-2xl mx-auto space-y-8">
            <div className="flex justify-center space-x-4 mb-6">
                <button
                    onClick={() => setInputType('file')}
                    className={cn(
                        "px-4 py-2 rounded-full text-sm font-medium transition-colors",
                        inputType === 'file'
                            ? "bg-primary text-primary-foreground"
                            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                    )}
                >
                    Upload PDF
                </button>
                <button
                    onClick={() => setInputType('url')}
                    className={cn(
                        "px-4 py-2 rounded-full text-sm font-medium transition-colors",
                        inputType === 'url'
                            ? "bg-primary text-primary-foreground"
                            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                    )}
                >
                    URL
                </button>
                <button
                    onClick={() => setInputType('arxiv')}
                    className={cn(
                        "px-4 py-2 rounded-full text-sm font-medium transition-colors",
                        inputType === 'arxiv'
                            ? "bg-primary text-primary-foreground"
                            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                    )}
                >
                    ArXiv ID
                </button>
            </div>

            {inputType === 'file' ? (
                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                        "relative flex flex-col items-center justify-center w-full h-64 rounded-xl border-2 border-dashed transition-all duration-300 ease-in-out cursor-pointer overflow-hidden group",
                        isDragOver ? "border-primary bg-primary/5 scale-[1.02]" : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50",
                        isUploading && "pointer-events-none opacity-50"
                    )}
                >
                    <input
                        type="file"
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        accept=".pdf"
                        onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                        disabled={isUploading}
                    />
                    <div className="flex flex-col items-center justify-center space-y-4 text-center p-6">
                        <div className={cn(
                            "p-4 rounded-full bg-secondary transition-transform duration-300 group-hover:scale-110",
                            isDragOver && "bg-primary/20"
                        )}>
                            {isUploading ? (
                                <Loader2 className="w-8 h-8 text-primary animate-spin" />
                            ) : (
                                <UploadCloud className="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" />
                            )}
                        </div>
                        <div className="space-y-1">
                            <p className="text-lg font-semibold text-foreground">
                                {isUploading ? "Uploading & Analyzing..." : "Drop your research paper here"}
                            </p>
                            <p className="text-sm text-muted-foreground">
                                Supports PDF up to 50MB
                            </p>
                        </div>
                    </div>
                </div>
            ) : (
                <form onSubmit={handleInputSubmit} className="relative group">
                    <div className="relative flex items-center">
                        <div className="absolute left-4 text-muted-foreground">
                            {inputType === 'url' ? <LinkIcon className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
                        </div>
                        <input
                            type="text"
                            placeholder={inputType === 'url' ? "https://example.com/paper.pdf" : "2310.12345"}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            className="w-full pl-12 pr-4 py-4 rounded-xl border border-muted-foreground/25 bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm"
                            disabled={isUploading}
                        />
                        <button
                            type="submit"
                            disabled={isUploading || !inputValue}
                            className="absolute right-2 px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Analyze"}
                        </button>
                    </div>
                </form>
            )}
        </div>
    );
}
