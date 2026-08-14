"use client";

import { useState, useCallback } from "react";
import { Upload, FileUp, Loader2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { uploadCSV } from "@/lib/api";
import { UploadResponse } from "@/lib/types";

interface Props {
  onUploadComplete: (response: UploadResponse) => void;
}

export function CSVUpload({ onUploadComplete }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploaded, setUploaded] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.endsWith(".csv")) {
        alert("Please upload a CSV file");
        return;
      }
      setIsUploading(true);
      try {
        const response = await uploadCSV(file);
        setUploaded(file.name);
        onUploadComplete(response);
      } catch (e) {
        alert(`Upload failed: ${e}`);
      } finally {
        setIsUploading(false);
      }
    },
    [onUploadComplete]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
        isDragging
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary/50"
      }`}
    >
      {isUploading ? (
        <div className="flex items-center justify-center gap-2 py-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Uploading...</span>
        </div>
      ) : uploaded ? (
        <div className="flex items-center justify-center gap-2 py-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          <span className="text-sm text-emerald-600">{uploaded}</span>
        </div>
      ) : (
        <>
          <FileUp className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
          <p className="text-xs text-muted-foreground mb-2">
            Drop a CSV file here or
          </p>
          <Button
            variant="outline"
            size="sm"
            className="text-xs"
            onClick={() => {
              const input = document.createElement("input");
              input.type = "file";
              input.accept = ".csv";
              input.onchange = (e) => {
                const file = (e.target as HTMLInputElement).files?.[0];
                if (file) handleFile(file);
              };
              input.click();
            }}
          >
            <Upload className="h-3 w-3 mr-1" />
            Browse
          </Button>
        </>
      )}
    </div>
  );
}
