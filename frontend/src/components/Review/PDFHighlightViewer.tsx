/**
 * PDFHighlightViewer Component
 *
 * Loads PDF page images from backend and overlays highlight rectangles
 * where source quotes appear. Supports zoom, navigation, and field details.
 */

import React, { useState, useEffect } from "react";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Search,
} from "lucide-react";

interface Highlight {
  id: string;
  fieldType: string;
  sourceQuote: string;
  bbox: { x: number; y: number; width: number; height: number };
  color: string;
  confidence: number;
}

interface PDFHighlightViewerProps {
  documentId: string;
  pageNumber: number;
  totalPages: number;
  highlights: Highlight[];
  onHighlightClick: (highlightId: string) => void;
  onPageChange: (page: number) => void;
}

export const PDFHighlightViewer: React.FC<PDFHighlightViewerProps> = ({
  documentId,
  pageNumber,
  totalPages,
  highlights,
  onHighlightClick,
  onPageChange,
}) => {
  const [zoom, setZoom] = useState(100);
  const [pageImage, setPageImage] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [selectedHighlight, setSelectedHighlight] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState(true);

  // Load page image
  useEffect(() => {
    const loadPage = async () => {
      setLoading(true);
      try {
        // In a real app, this would fetch the page image from the backend
        // For now, we'll use a placeholder
        setPageImage(`/api/documents/${documentId}/pages/${pageNumber}/image`);
        setLoading(false);
      } catch (error) {
        console.error("Failed to load page:", error);
        setLoading(false);
      }
    };

    loadPage();
  }, [documentId, pageNumber]);

  const handleHighlightClick = (highlightId: string) => {
    setSelectedHighlight(highlightId);
    onHighlightClick(highlightId);
  };

  const handleZoomIn = () => {
    setZoom(Math.min(zoom + 20, 200));
  };

  const handleZoomOut = () => {
    setZoom(Math.max(zoom - 20, 50));
  };

  const handlePrevPage = () => {
    if (pageNumber > 1) {
      onPageChange(pageNumber - 1);
    }
  };

  const handleNextPage = () => {
    if (pageNumber < totalPages) {
      onPageChange(pageNumber + 1);
    }
  };

  // Calculate highlight positions based on zoom
  const scaledHighlights = highlights.map((h) => ({
    ...h,
    bbox: {
      x: h.bbox.x * (zoom / 100),
      y: h.bbox.y * (zoom / 100),
      width: h.bbox.width * (zoom / 100),
      height: h.bbox.height * (zoom / 100),
    },
  }));

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">
            Page {pageNumber} of {totalPages}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevPage}
            disabled={pageNumber === 1}
            className="p-2 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed rounded"
            title="Previous page"
          >
            <ChevronLeft size={20} />
          </button>

          <button
            onClick={handleNextPage}
            disabled={pageNumber === totalPages}
            className="p-2 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed rounded"
            title="Next page"
          >
            <ChevronRight size={20} />
          </button>

          <div className="w-px h-6 bg-gray-300"></div>

          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 rounded"
            title="Zoom out"
          >
            <ZoomOut size={20} />
          </button>

          <span className="text-sm font-medium w-12 text-center">{zoom}%</span>

          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 rounded"
            title="Zoom in"
          >
            <ZoomIn size={20} />
          </button>

          <div className="w-px h-6 bg-gray-300"></div>

          <div className="text-sm text-gray-600">
            {highlights.length} highlight{highlights.length !== 1 ? "s" : ""}
          </div>
        </div>
      </div>

      {/* PDF Display Area */}
      <div className="flex-1 overflow-auto bg-gray-50 p-6">
        <div className="flex justify-center">
          <div
            className="relative bg-white shadow-lg"
            style={{
              width: `${imageSize.width * (zoom / 100)}px`,
              height: `${imageSize.height * (zoom / 100)}px`,
              transform: `scale(${zoom / 100})`,
              transformOrigin: "top center",
            }}
          >
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
                <div className="text-gray-600">Loading page...</div>
              </div>
            ) : (
              <>
                {/* Page Image */}
                <img
                  src={pageImage || ""}
                  alt={`Page ${pageNumber}`}
                  onLoad={(e) => {
                    const img = e.target as HTMLImageElement;
                    setImageSize({
                      width: img.naturalWidth,
                      height: img.naturalHeight,
                    });
                  }}
                  className="w-full h-full"
                />

                {/* Highlight Overlays */}
                <svg
                  className="absolute inset-0 w-full h-full"
                  style={{ pointerEvents: "auto" }}
                >
                  {scaledHighlights.map((highlight) => (
                    <g key={highlight.id}>
                      {/* Semi-transparent background */}
                      <rect
                        x={highlight.bbox.x}
                        y={highlight.bbox.y}
                        width={highlight.bbox.width}
                        height={highlight.bbox.height}
                        fill={highlight.color}
                        opacity={0.3}
                        className="cursor-pointer"
                        onClick={() => handleHighlightClick(highlight.id)}
                      />

                      {/* Border */}
                      <rect
                        x={highlight.bbox.x}
                        y={highlight.bbox.y}
                        width={highlight.bbox.width}
                        height={highlight.bbox.height}
                        fill="none"
                        stroke={highlight.color}
                        strokeWidth={2}
                        className={`cursor-pointer ${
                          selectedHighlight === highlight.id
                            ? "opacity-100"
                            : "opacity-70"
                        }`}
                        onClick={() => handleHighlightClick(highlight.id)}
                      />

                      {/* Hover label */}
                      <title>{highlight.fieldType}</title>
                    </g>
                  ))}
                </svg>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Highlights Legend */}
      <div className="border-t border-gray-200 p-4 bg-gray-50 max-h-32 overflow-y-auto">
        <div className="text-xs font-semibold text-gray-700 mb-2">
          Highlights on this page:
        </div>
        <div className="space-y-1">
          {scaledHighlights.length === 0 ? (
            <div className="text-xs text-gray-500">
              No highlights on this page
            </div>
          ) : (
            scaledHighlights.map((highlight) => (
              <div
                key={highlight.id}
                onClick={() => handleHighlightClick(highlight.id)}
                className={`text-xs p-1 rounded cursor-pointer ${
                  selectedHighlight === highlight.id
                    ? "bg-white border-l-4"
                    : "hover:bg-white"
                }`}
                style={{
                  borderLeftColor: highlight.color,
                  paddingLeft:
                    selectedHighlight === highlight.id
                      ? "calc(0.25rem - 4px)"
                      : "0.25rem",
                }}
              >
                <span className="font-medium">{highlight.fieldType}</span>
                <span className="text-gray-600 ml-1">
                  (confidence: {(highlight.confidence * 100).toFixed(0)}%)
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFHighlightViewer;
