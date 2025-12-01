'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import axios from 'axios';
import Card from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { getAnnouncements, triggerAnnouncementsScrape } from '@/lib/api/announcements';
import type { Announcement, UserProfileResponse } from '@/types/api';
import BookmarkButton from '@/components/common/BookmarkButton';
import { useQuery } from '@tanstack/react-query';
import { getMyBookmarks } from '@/lib/api/bookmarks';
import { fetchUserProfile } from '@/lib/api/users';

type SortOption = 'latest' | 'dday' | 'deposit' | 'rent';

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedHousingType, setSelectedHousingType] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('latest');
  const [maxDepositFilter, setMaxDepositFilter] = useState<number | null>(null);
  const [maxRentFilter, setMaxRentFilter] = useState<number | null>(null);
  const [preferenceApplied, setPreferenceApplied] = useState(false);
  const [preferenceEnabled, setPreferenceEnabled] = useState(true);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPast, setShowPast] = useState(false);
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeMessage, setScrapeMessage] = useState('');

  // 내 관심 공고 목록 불러오기 (하트 초기 상태 반영)
  const { data: myBookmarks } = useQuery<Announcement[]>({
    queryKey: ['bookmarks', 'me'],
    queryFn: getMyBookmarks,
    staleTime: 30_000,
  });
  const bookmarkedIds = useMemo(
    () => new Set((myBookmarks ?? []).map((announcement: Announcement) => announcement.announcement_id)),
    [myBookmarks],
  );

  const fetchAnnouncements = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError('');

    const PAGE_SIZE = 100;
    const aggregated: Announcement[] = [];
    const seen = new Set<number>();

    try {
      let page = 1;
      let hasMore = true;

      while (hasMore) {
        if (signal?.aborted) {
          return;
        }

        const response = await getAnnouncements(
          {
            page,
            size: PAGE_SIZE,
            order_by: 'post_date',
            order: 'desc',
          },
          { signal },
        );

        for (const item of response.items) {
          if (!seen.has(item.announcement_id)) {
            seen.add(item.announcement_id);
            aggregated.push(item);
          }
        }

        const total = typeof response.total === 'number' ? response.total : null;
        const fetchedAll = total ? aggregated.length >= total : response.items.length < PAGE_SIZE;

        hasMore = !fetchedAll;
        page += 1;
      }

      if (!signal?.aborted) {
        setAnnouncements(aggregated);
      }
    } catch (err: unknown) {
      const error = err as {
        name?: string;
        code?: string;
        message?: string;
      };
      const message = typeof error?.message === 'string' ? error.message : '';
      const isCanceled =
        axios.isCancel?.(err) ||
        error?.name === 'CanceledError' ||
        error?.code === 'ERR_CANCELED' ||
        message.includes('aborted without reason');
      if (isCanceled) {
        return;
      }
      console.error(err);
      setError('공고 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchAnnouncements(controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchAnnouncements]);

  useEffect(() => {
    const loadPreference = async () => {
      try {
        const profile: UserProfileResponse = await fetchUserProfile();
        if (profile.preference && !preferenceApplied && preferenceEnabled) {
          applyPreferenceFilters(profile.preference);
          setPreferenceApplied(true);
        } else if (!preferenceEnabled) {
          clearPreferenceFilters();
          setPreferenceApplied(false);
        }
      } catch (err) {
        console.error('Failed to load preference info', err);
      }
    };
    loadPreference();
  }, [preferenceApplied]);

  const handleScrapeAnnouncements = async () => {
    if (isScraping) return;
    
    setIsScraping(true);
    setScrapeMessage('공고 목록을 업데이트 중입니다...');
    
    try {
      // 기본값: board_id 7000부터 7일치 스크랩
      await triggerAnnouncementsScrape({ start_board_id: 7000, days_limit: 7 });
      setScrapeMessage('업데이트 요청이 전송되었습니다. 잠시 후 새로고침 됩니다.');
      
      // 스크래핑 요청 후 잠시 대기했다가 목록 새로고침
      setTimeout(() => {
        fetchAnnouncements();
        setScrapeMessage('');
        setIsScraping(false);
      }, 3000);
      
    } catch (err) {
      console.error('Scrape failed:', err);
      setScrapeMessage('업데이트 요청 실패. 잠시 후 다시 시도해주세요.');
      setIsScraping(false);
    }
  };

  const regions = useMemo(() => {
    const uniqueRegions = new Set<string>();
    announcements.forEach((announcement) => {
      if (announcement.region) {
        uniqueRegions.add(announcement.region.split(' ')[0] ?? announcement.region);
      }
    });
    const regionList = ['전체', ...Array.from(uniqueRegions)];
    if (selectedRegion && !uniqueRegions.has(selectedRegion) && selectedRegion !== '') {
      regionList.push(selectedRegion);
    }
    return regionList;
  }, [announcements, selectedRegion]);

  const housingTypes = useMemo(() => {
    const uniqueTypes = new Set<string>();
    announcements.forEach((announcement) => {
      if (announcement.housing_type) {
        uniqueTypes.add(announcement.housing_type);
      }
    });
    const typeList = ['전체', ...Array.from(uniqueTypes)];
    if (selectedHousingType && !uniqueTypes.has(selectedHousingType) && selectedHousingType !== '') {
      typeList.push(selectedHousingType);
    }
    return typeList;
  }, [announcements, selectedHousingType]);

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

    if (maxDepositFilter !== null) {
      result = result.filter((announcement) => {
        const deposit = announcement.min_deposit ?? announcement.max_deposit;
        if (deposit === null || deposit === undefined) return false;
        return deposit <= maxDepositFilter;
      });
    }

    if (maxRentFilter !== null) {
      result = result.filter((announcement) => {
        if (announcement.monthly_rent === null || announcement.monthly_rent === undefined) {
          return false;
        }
        return announcement.monthly_rent <= maxRentFilter;
      });
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
        default: {
          // Post_Date 우선 정렬(내림차순), 없으면 scraped_at → application_end_date
          const getDate = (announcement: Announcement) =>
            new Date(
              announcement.post_date ?? announcement.scraped_at ?? announcement.application_end_date ?? 0,
            ).getTime();
          return getDate(b) - getDate(a);
        }
      }
    });

    return result;
  }, [
    announcements,
    searchQuery,
    selectedRegion,
    selectedHousingType,
    sortBy,
    showPast,
    maxDepositFilter,
    maxRentFilter,
  ]);

  const applyPreferenceFilters = useCallback((pref: UserProfileResponse['preference']) => {
    if (!pref) return;
    const firstLocation =
      pref.locations && pref.locations.length > 0 ? pref.locations[0] ?? '' : '';
    if (firstLocation) {
      setSelectedRegion(firstLocation);
    } else {
      setSelectedRegion('');
    }
    if (pref.housing_types && pref.housing_types.length > 0) {
      setSelectedHousingType(pref.housing_types[0] ?? '');
    } else {
      setSelectedHousingType('');
    }
    if (pref.max_deposit !== undefined && pref.max_deposit !== null) {
      setMaxDepositFilter(pref.max_deposit);
    } else {
      setMaxDepositFilter(null);
    }
    if (pref.max_monthly_rent !== undefined && pref.max_monthly_rent !== null) {
      setMaxRentFilter(pref.max_monthly_rent);
    } else {
      setMaxRentFilter(null);
    }
  }, []);

  const clearPreferenceFilters = useCallback(() => {
    setSelectedRegion('');
    setSelectedHousingType('');
    setMaxDepositFilter(null);
    setMaxRentFilter(null);
  }, []);

  const resetAllFilters = useCallback(() => {
    setSearchQuery('');
    setSortBy('latest');
    setShowPast(true);
    clearPreferenceFilters();
    setPreferenceApplied(false);
  }, [clearPreferenceFilters]);

  const handleResetPreferenceFilters = () => {
    setPreferenceEnabled(false);
    resetAllFilters();
  };

  const handlePreferenceToggle = async () => {
    const newEnabled = !preferenceEnabled;
    setPreferenceEnabled(newEnabled);
    if (newEnabled) {
      try {
        const profile = await fetchUserProfile();
        if (profile.preference) {
          applyPreferenceFilters(profile.preference);
          setPreferenceApplied(true);
        }
      } catch (err) {
        console.error('Failed to reload preferences', err);
      }
    } else {
      resetAllFilters();
    }
  };

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

            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-gray-200">
              {/* 자주 검색하는 키워드 */}
              <div className="flex items-center gap-2">
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

              <div className="flex flex-1 flex-wrap items-center justify-end gap-3">
                <div className="flex flex-col gap-2 rounded-xl border border-gray-200/80 bg-gray-50 px-4 py-2 min-w-[260px]">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-sm font-semibold text-gray-900 flex items-center gap-1">
                      <span>🎯</span> 개인 맞춤형 공고
                    </span>
                    <button
                      onClick={handlePreferenceToggle}
                      className={`w-12 h-6 rounded-full relative transition-colors ${
                        preferenceEnabled ? 'bg-blue-600' : 'bg-gray-300'
                      }`}
                      aria-pressed={preferenceEnabled}
                      aria-label="개인 맞춤형 공고 토글"
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                          preferenceEnabled ? 'translate-x-6' : 'translate-x-0'
                        }`}
                      />
                    </button>
                    <span className="text-xs text-gray-600">
                      {preferenceEnabled ? '희망 조건 기반 추천 사용 중' : '비활성화됨'}
                    </span>
                  </div>
                  {(preferenceApplied ||
                    maxDepositFilter !== null ||
                    maxRentFilter !== null ||
                    selectedRegion ||
                    selectedHousingType) && (
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      {selectedRegion && <Badge variant="default">지역: {selectedRegion}</Badge>}
                      {selectedHousingType && <Badge variant="info">주택 유형: {selectedHousingType}</Badge>}
                      {maxDepositFilter !== null && (
                        <Badge variant="warning">보증금 ≤ {maxDepositFilter.toLocaleString()}만원</Badge>
                      )}
                      {maxRentFilter !== null && (
                        <Badge variant="success">월세 ≤ {maxRentFilter.toLocaleString()}만원</Badge>
                      )}
                      <button
                        onClick={handleResetPreferenceFilters}
                        className="text-blue-600 hover:text-blue-800 font-medium underline-offset-4 hover:underline"
                      >
                        조건 초기화
                      </button>
                    </div>
                  )}
                </div>
                <button
                  onClick={handleScrapeAnnouncements}
                  disabled={isScraping}
                  className={`px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2 ${
                    isScraping
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'
                  }`}
                >
                  {isScraping ? (
                    <>
                      <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      업데이트 중...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      공고 업데이트
                    </>
                  )}
                </button>
              </div>
            </div>
            
            {/* 스크랩 메시지 */}
            {scrapeMessage && (
               <div className="mt-2 text-sm text-blue-600 text-right font-medium animate-pulse">
                 {scrapeMessage}
               </div>
            )}
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
                        {announcement.dday !== undefined && (
                          <Badge variant={announcement.dday !== null && announcement.dday >= 0 ? "danger" : "default"} icon="⏰">
                            {announcement.dday !== null && announcement.dday >= 0 ? `D-${announcement.dday}` : '종료됨'}
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
