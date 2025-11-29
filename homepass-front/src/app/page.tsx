'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import axios from 'axios';
import Card from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { getAnnouncements } from '@/lib/api/announcements';
import type { Announcement } from '@/types/api';
import BookmarkButton from '@/components/common/BookmarkButton';
import { useQuery } from '@tanstack/react-query';
import { getMyBookmarks } from '@/lib/api/bookmarks';

type SortOption = 'latest' | 'dday' | 'deposit' | 'rent';

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedHousingType, setSelectedHousingType] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('latest');
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPast, setShowPast] = useState(false);

  // 내 관심 공고 목록 불러오기 (하트 초기 상태 반영)
  const { data: myBookmarks } = useQuery<Announcement[]>({
    queryKey: ['bookmarks', 'me'],
    queryFn: getMyBookmarks,
    staleTime: 30_000,
  });
  const bookmarkedIds = useMemo(() => new Set((myBookmarks ?? []).map((a) => a.announcement_id)), [myBookmarks]);

  useEffect(() => {
    const controller = new AbortController();
    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await getAnnouncements(
          {
            size: 50,
            exclude_past: !showPast,
            within_days: !showPast ? 30 : undefined,
            order_by: 'post_date',
            order: 'desc',
          },
          { signal: controller.signal },
        );
        setAnnouncements(response.items);
      } catch (err: any) {
        // 요청 취소는 오류로 처리하지 않음
        const isCanceled =
          axios.isCancel?.(err) ||
          err?.name === 'CanceledError' ||
          err?.code === 'ERR_CANCELED' ||
          err?.message?.includes?.('aborted without reason');
        if (isCanceled) {
          return;
        }
        console.error(err);
        setError('공고 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    return () => {
      controller.abort();
    };
  }, [showPast]);

  const regions = useMemo(() => {
    const uniqueRegions = new Set<string>();
    announcements.forEach((announcement) => {
      if (announcement.region) {
        uniqueRegions.add(announcement.region.split(' ')[0] ?? announcement.region);
      }
    });
    return ['전체', ...Array.from(uniqueRegions)];
  }, [announcements]);

  const housingTypes = useMemo(() => {
    const uniqueTypes = new Set<string>();
    announcements.forEach((announcement) => {
      if (announcement.housing_type) {
        uniqueTypes.add(announcement.housing_type);
      }
    });
    return ['전체', ...Array.from(uniqueTypes)];
  }, [announcements]);

  const filteredAnnouncements = useMemo(() => {
    let result = [...announcements];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (announcement) =>
          announcement.title.toLowerCase().includes(query) ||
          (announcement.region?.toLowerCase().includes(query) ?? false) ||
          (announcement.housing_type?.toLowerCase().includes(query) ?? false),
      );
    }

    if (selectedRegion) {
      result = result.filter((announcement) =>
        (announcement.region ?? '').includes(selectedRegion),
      );
    }

    if (selectedHousingType) {
      result = result.filter(
        (announcement) => announcement.housing_type === selectedHousingType,
      );
    }

    if (!showPast) {
      const now = new Date();
      const oneMonthLater = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
      result = result.filter((a) => {
        // dday가 있으면 0~30일 사이만 표시
        if (a.dday !== undefined && a.dday !== null) {
          return a.dday >= 0 && a.dday <= 30;
        }
        // 아니면 application_end_date가 오늘~30일 이내만 표시
        if (a.application_end_date) {
          const end = new Date(a.application_end_date);
          return end >= now && end <= oneMonthLater;
        }
        // 판단 불가 데이터는 기본 제외
        return false;
      });
    }

    result.sort((a, b) => {
      switch (sortBy) {
        case 'dday':
          return (a.dday ?? Infinity) - (b.dday ?? Infinity);
        case 'deposit':
          return (a.min_deposit ?? Infinity) - (b.min_deposit ?? Infinity);
        case 'rent':
          return (a.monthly_rent ?? Infinity) - (b.monthly_rent ?? Infinity);
        case 'latest':
        default:
          // Post_Date 우선 정렬(내림차순), 없으면 scraped_at → application_end_date
          const getDate = (x: any) =>
            new Date(x?.post_date ?? x?.scraped_at ?? x?.application_end_date ?? 0).getTime();
          return getDate(b) - getDate(a);
      }
    });

    return result;
  }, [announcements, searchQuery, selectedRegion, selectedHousingType, sortBy]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-indigo-50/30">
      <div className="container mx-auto px-4 py-8">
        {/* 헤더 섹션 */}
        <div className="mb-8 text-center animate-fade-in">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
            청약 공고를 한눈에
          </h1>
          <p className="text-gray-900 text-lg">맞춤형 청약 공고를 찾아보세요</p>
        </div>

        {/* 필터 섹션 */}
        <Card className="mb-8 p-6 shadow-lg animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              {/* 검색 바 */}
              <div className="flex-1 relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg className="w-5 h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder="공고명 또는 지역으로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all"
                />
              </div>

              {/* 필터 그룹 */}
              <div className="flex flex-col sm:flex-row gap-2">
                {/* 지역 필터 */}
                <div className="relative">
                  <select
                    value={selectedRegion}
                    onChange={(e) => setSelectedRegion(e.target.value)}
                    className="px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 bg-white appearance-none cursor-pointer transition-all min-w-[140px]"
                  >
                    {regions.map((region) => (
                      <option key={region} value={region === '전체' ? '' : region}>
                        {region}
                      </option>
                    ))}
                  </select>
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <svg className="w-5 h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                {/* 주택 유형 필터 */}
                <div className="relative">
                  <select
                    value={selectedHousingType}
                    onChange={(e) => setSelectedHousingType(e.target.value)}
                    className="px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 bg-white appearance-none cursor-pointer transition-all min-w-[120px]"
                  >
                    {housingTypes.map((type) => (
                      <option key={type} value={type === '전체' ? '' : type}>
                        {type}
                      </option>
                    ))}
                  </select>
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <svg className="w-5 h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                {/* 정렬 */}
                <div className="relative">
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as SortOption)}
                    className="px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 bg-white appearance-none cursor-pointer transition-all min-w-[130px]"
                  >
                    <option value="latest">최신순</option>
                    <option value="dday">마감 임박순</option>
                    <option value="deposit">보증금 낮은순</option>
                    <option value="rent">월 임대료 낮은순</option>
                  </select>
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <svg className="w-5 h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                {/* 지난 공고 포함 토글 */}
                <div className="flex items-center gap-2 px-2">
                  <span className="text-sm text-gray-900">지난 공고 포함</span>
                  <button
                    onClick={() => setShowPast((v) => !v)}
                    className={`w-10 h-6 rounded-full relative transition-colors ${
                      showPast ? 'bg-blue-600' : 'bg-gray-300'
                    }`}
                    aria-pressed={showPast}
                    aria-label="지난 공고 포함 토글"
                  >
                    <span
                      className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                        showPast ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>

            {/* 자주 검색하는 키워드 */}
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gray-200">
              <span className="text-sm text-gray-900 font-medium flex items-center gap-1">
                <span>🔥</span> 자주 검색:
              </span>
              {['강남구', '행복주택', '국민임대', '서울'].map((keyword) => (
                <button
                  key={keyword}
                  onClick={() => setSearchQuery(keyword)}
                  className="px-3 py-1.5 text-sm bg-gradient-to-r from-gray-50 to-gray-100 text-gray-800 rounded-full hover:from-blue-50 hover:to-indigo-50 hover:text-blue-600 hover:shadow-md transition-all duration-200 font-medium border border-gray-200/50 hover:border-blue-200"
                >
                  {keyword}
                </button>
              ))}
            </div>
          </div>
        </Card>

        {/* 로딩 / 에러 상태 */}
        {loading && (
          <div className="py-16 text-center text-gray-900 animate-pulse">
            공고를 불러오는 중입니다...
          </div>
        )}
        {error && (
          <Card className="mb-6 border-red-200 bg-red-50 text-red-700">
            <div className="p-6 text-center font-medium">{error}</div>
          </Card>
        )}

        {/* 공고 카드 리스트 */}
        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAnnouncements.map((announcement, idx) => (
              <Link
                key={announcement.announcement_id}
                href={`/announcements/${announcement.announcement_id}`}
                className="animate-fade-in"
                style={{ animationDelay: `${(idx + 1) * 0.05}s` }}
              >
                <Card hover gradient className="h-full overflow-hidden">
                  {announcement.is_customized && (
                    <div className="h-1.5 bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400"></div>
                  )}

                  <div className="p-6 relative">
                    <div className="absolute top-4 right-4 z-10">
                      <BookmarkButton
                        announcementId={announcement.announcement_id}
                        initialIsBookmarked={bookmarkedIds.has(announcement.announcement_id)}
                        size={22}
                      />
                    </div>
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex flex-wrap gap-2">
                        {announcement.is_customized && (
                          <Badge variant="success" icon="⭐">
                            맞춤
                          </Badge>
                        )}
                        {announcement.dday !== undefined && (
                          <Badge variant="danger" icon="⏰">
                            D-{announcement.dday}
                          </Badge>
                        )}
                      </div>
                      {announcement.housing_type && (
                        <Badge variant="info" icon="🏠">
                          {announcement.housing_type}
                        </Badge>
                      )}
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
                        <span className="text-sm text-gray-900 flex items-center gap-1">
                          💰 보증금
                        </span>
                        <span className="font-bold text-gray-900 text-sm">
                          {announcement.min_deposit !== undefined && announcement.min_deposit !== null
                            ? `${announcement.min_deposit.toLocaleString()}만원`
                            : '정보 없음'}
                          {' ~ '}
                          {announcement.max_deposit !== undefined && announcement.max_deposit !== null
                            ? `${announcement.max_deposit.toLocaleString()}만원`
                            : '정보 없음'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-900 flex items-center gap-1">
                          💵 월 임대료
                        </span>
                        <span className="font-bold text-gray-900 text-sm">
                          {announcement.monthly_rent !== undefined && announcement.monthly_rent !== null
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

        {!loading && !error && filteredAnnouncements.length === 0 && (
          <Card className="mt-12">
            <div className="p-12 text-center text-gray-900">
              조건에 맞는 공고가 없습니다.
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
