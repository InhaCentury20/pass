'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import Card from '@/components/common/Card';
import { getMyBookmarks } from '@/lib/api/bookmarks';
import type { Announcement } from '@/types/api';
import BookmarkButton from '@/components/common/BookmarkButton';

function BookmarkSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="p-6 space-y-4 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3" />
        <div className="h-6 bg-gray-200 rounded w-2/3" />
        <div className="space-y-2">
          <div className="h-3 bg-gray-200 rounded w-1/2" />
          <div className="h-3 bg-gray-200 rounded w-1/3" />
        </div>
        <div className="h-8 bg-gray-200 rounded w-full" />
      </div>
    </Card>
  );
}

export default function MyBookmarksPage() {
  const { data, isLoading, isError } = useQuery<Announcement[]>({
    queryKey: ['bookmarks', 'me'],
    queryFn: getMyBookmarks,
  });

  const bookmarks = data ?? [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-indigo-50/30">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900">내 관심 공고</h1>
          <p className="text-gray-900 mt-2">하트로 저장한 공고들을 모아서 볼 수 있어요.</p>
        </div>

        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, idx) => (
              <BookmarkSkeleton key={idx} />
            ))}
          </div>
        )}

        {isError && (
          <Card className="mb-6 border-red-200 bg-red-50 text-red-700">
            <div className="p-6 text-center font-medium">관심 공고를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.</div>
          </Card>
        )}

        {!isLoading && !isError && (
          <>
            {bookmarks.length === 0 ? (
              <Card className="mt-6">
                <div className="p-12 text-center text-gray-900">저장한 관심 공고가 없습니다.</div>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {bookmarks.map((announcement) => (
                  <Link
                    key={announcement.announcement_id}
                    href={`/announcements/${announcement.announcement_id}`}
                    className="animate-fade-in"
                  >
                    <Card hover gradient className="h-full overflow-hidden">
                      <div className="p-6 relative">
                        <div className="absolute top-4 right-4 z-10">
                          <BookmarkButton announcementId={announcement.announcement_id} initialIsBookmarked={true} size={22} />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 mb-3 line-clamp-2 hover:text-blue-600 transition-colors">
                          {announcement.title}
                        </h3>
                        <div className="flex items-center gap-1.5 mb-5 text-sm text-gray-900">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          {announcement.region ?? '지역 정보 없음'}
                        </div>
                        <div className="space-y-3 mb-5 p-4 bg-gradient-to-br from-blue-50/50 to-indigo-50/50 rounded-xl border border-blue-100/50">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-900 flex items-center gap-1">💰 보증금</span>
                            <span className="font-bold text-gray-900 text-sm">
                              {announcement.min_deposit !== undefined
                                ? `${announcement.min_deposit.toLocaleString()}만원`
                                : '정보 없음'}
                              {' ~ '}
                              {announcement.max_deposit !== undefined
                                ? `${announcement.max_deposit.toLocaleString()}만원`
                                : '정보 없음'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-900 flex items-center gap-1">💵 월 임대료</span>
                            <span className="font-bold text-gray-900 text-sm">
                              {announcement.monthly_rent !== undefined
                                ? `${announcement.monthly_rent.toLocaleString()}만원`
                                : '정보 없음'}
                            </span>
                          </div>
                        </div>
                        <div className="pt-4 border-t border-gray-200 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <p className="text-xs text-gray-900">
                              마감일: {announcement.application_end_date?.slice(0, 10) ?? '미정'}
                            </p>
                          </div>
                          <span className="text-blue-600 text-xs font-semibold flex items-center gap-1">
                            자세히 보기
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </span>
                        </div>
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}


