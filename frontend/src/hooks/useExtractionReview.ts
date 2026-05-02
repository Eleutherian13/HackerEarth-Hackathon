import { useEffect, useMemo, useState } from 'react';

export interface ReviewConflictDetails {
  last_modified_by?: string | null;
  last_modified_at?: string | null;
}

export interface StaleReviewErrorPayload {
  error: string;
  message: string;
  current_version: number;
  details?: ReviewConflictDetails;
}

export class ReviewApiError extends Error {
  status: number;
  payload?: StaleReviewErrorPayload;

  constructor(message: string, status: number, payload?: StaleReviewErrorPayload) {
    super(message);
    this.name = 'ReviewApiError';
    this.status = status;
    this.payload = payload;
  }
}

export interface VersionedReviewItem {
  id: string;
  version: number;
  verified_at?: string | null;
  reviewer_info?: { full_name: string } | null;
}

const RECENT_WINDOW_MS = 5 * 60 * 1000;

export function isRecentlyReviewed(verifiedAt?: string | null): boolean {
  if (!verifiedAt) {
    return false;
  }

  const reviewedAt = new Date(verifiedAt).getTime();
  if (Number.isNaN(reviewedAt)) {
    return false;
  }

  return Date.now() - reviewedAt < RECENT_WINDOW_MS;
}

export function useVersionTracker<T extends VersionedReviewItem>(items: T[] | undefined) {
  const [versionById, setVersionById] = useState<Record<string, number>>({});
  const [changedIds, setChangedIds] = useState<Record<string, boolean>>({});
  const [recentReviewById, setRecentReviewById] = useState<Record<string, { reviewerName: string; verifiedAt: string }>>({});

  useEffect(() => {
    if (!items) {
      return;
    }

    setVersionById((current) => {
      const next = { ...current };
      for (const item of items) {
        next[item.id] = item.version;
      }
      return next;
    });

    setRecentReviewById((current) => {
      const next = { ...current };
      for (const item of items) {
        const reviewerName = item.reviewer_info?.full_name ?? current[item.id]?.reviewerName;
        if (isRecentlyReviewed(item.verified_at) && reviewerName) {
          next[item.id] = { reviewerName, verifiedAt: item.verified_at as string };
        }
      }
      return next;
    });
  }, [items]);

  const recentlyReviewedItems = useMemo(() => recentReviewById, [recentReviewById]);

  const markConflict = (itemId: string, reviewerName?: string | null, verifiedAt?: string | null, currentVersion?: number) => {
    setChangedIds((current) => ({ ...current, [itemId]: true }));
    if (currentVersion) {
      setVersionById((current) => ({ ...current, [itemId]: currentVersion }));
    }
    if (reviewerName && verifiedAt) {
      setRecentReviewById((current) => ({
        ...current,
        [itemId]: { reviewerName, verifiedAt },
      }));
    }
  };

  const clearChanged = (itemId: string) => {
    setChangedIds((current) => {
      const next = { ...current };
      delete next[itemId];
      return next;
    });
  };

  const setItemVersion = (itemId: string, version: number) => {
    setVersionById((current) => ({ ...current, [itemId]: version }));
  };

  return {
    versionById,
    changedIds,
    recentlyReviewedItems,
    setItemVersion,
    markConflict,
    clearChanged,
  };
}
