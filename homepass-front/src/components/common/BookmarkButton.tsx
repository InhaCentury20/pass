'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { toggleBookmark } from '@/lib/api/bookmarks';

interface BookmarkButtonProps {
  announcementId: number;
  initialIsBookmarked: boolean;
  size?: number;
}

export default function BookmarkButton({ announcementId, initialIsBookmarked, size = 22 }: BookmarkButtonProps) {
  const queryClient = useQueryClient();
  const [isBookmarked, setIsBookmarked] = useState<boolean>(initialIsBookmarked);

  const mutation = useMutation({
    mutationFn: async () => {
      return toggleBookmark(announcementId);
    },
    onMutate: async () => {
      // 낙관적 업데이트
      setIsBookmarked((prev) => !prev);
      return { previous: !isBookmarked };
    },
    onError: (_error, _variables, context) => {
      // 롤백
      if (context?.previous !== undefined) {
        setIsBookmarked(context.previous);
      } else {
        setIsBookmarked(initialIsBookmarked);
      }
    },
    onSettled: async () => {
      // 내 북마크 목록 갱신
      await queryClient.invalidateQueries({ queryKey: ['bookmarks', 'me'] });
    },
  });

  const handleClick = () => {
    if (mutation.isPending) return;
    mutation.mutate();
  };

  return (
    <button
      aria-label={isBookmarked ? '관심 공고 해제' : '관심 공고 등록'}
      onClick={handleClick}
      className={`inline-flex items-center justify-center rounded-full transition-all ${
        isBookmarked
          ? 'text-pink-600 hover:text-pink-700 bg-pink-50 hover:bg-pink-100'
          : 'text-gray-400 hover:text-gray-600 bg-white/80 hover:bg-white'
      } border border-gray-200 shadow-sm`}
      style={{ width: size + 8, height: size + 8 }}
    >
      {/* 하트 아이콘 (SVG) */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill={isBookmarked ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth={1.8}
        className="transition-colors"
        style={{ width: size, height: size }}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
        />
      </svg>
    </button>
  );
}


