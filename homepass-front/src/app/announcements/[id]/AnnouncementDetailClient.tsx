'use client';

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Card from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import type { Announcement, AnnouncementDetail, PriceOption } from '@/types/api';
import BookmarkButton from '@/components/common/BookmarkButton';
import { getMyBookmarks } from '@/lib/api/bookmarks';
import { getNearbyPlaces } from '@/lib/api/places';
import { createApplication } from '@/lib/api/applications';
import { getCommuteInfo } from '@/lib/api/announcements';
import dynamic from 'next/dynamic';

// 네이버 지도 컴포넌트를 동적 임포트 (SSR 방지)
const NaverMap = dynamic(() => import('@/components/common/NaverMap'), {
  ssr: false,
  loading: () => (
    <div className="aspect-video bg-gray-100 rounded-xl flex items-center justify-center">
      <div className="text-gray-500">지도 로딩 중...</div>
    </div>
  ),
});

type TabType = 'info' | 'commute';

const scheduleColorPalette = ['bg-blue-500', 'bg-indigo-500', 'bg-purple-500', 'bg-rose-500', 'bg-emerald-500'];

type NormalizedScheduleItem = {
  id: string;
  title: string;
  displayDate: string;
  rawDate?: string;
  startText?: string;
  endText?: string;
  isRange: boolean;
};

interface Props {
  announcement: AnnouncementDetail;
}

export function AnnouncementDetailClient({ announcement }: Props) {
  const [activeTab, setActiveTab] = useState<TabType>('info');
  const [isApplying, setIsApplying] = useState(false);
  const [hasApplied, setHasApplied] = useState(false);

  const tabs: Array<{ id: TabType; label: string; icon: string }> = [
    { id: 'info', label: '핵심 정보', icon: '📋' },
    { id: 'commute', label: '출퇴근/주변', icon: '🚇' },
  ];

  const ddayText =
    announcement.dday !== undefined && announcement.dday !== null
      ? `D-${announcement.dday}`
      : '마감 일정 미정';

  const handleApply = async () => {
    if (isApplying || hasApplied) {
      return;
    }
    setIsApplying(true);
    try {
      await createApplication(announcement.announcement_id);
      setHasApplied(true);
      window.alert('신청 완료되었습니다!');
    } catch (error) {
      console.error('Failed to create application', error);
      window.alert('신청에 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-indigo-50/30">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center gap-3 mb-4 flex-wrap">
            <Badge variant="danger" icon="⏰">
              {ddayText}
            </Badge>
            {announcement.housing_type && (
              <Badge variant="info" icon="🏠">
                {announcement.housing_type}
              </Badge>
            )}
            {announcement.region && (
              <Badge variant="default" icon="📍">
                {announcement.region}
              </Badge>
            )}
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-3 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            {announcement.title}
          </h1>
          <div className="flex items-center gap-2 text-gray-900">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <span className="text-lg">
              {announcement.address_detail ?? '상세 주소가 등록되지 않았습니다.'}
            </span>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
          <nav className="flex space-x-2 p-2 bg-white/80 rounded-2xl shadow animate-fade-in" style={{ animationDelay: '0.1s' }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm transition-all duration-200 ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg scale-105'
                    : 'text-gray-900 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
          {(announcement.source_url || announcement.original_pdf_url) && (
            <div className="flex flex-wrap gap-3 justify-end w-full lg:w-auto animate-fade-in" style={{ animationDelay: '0.15s' }}>
              {announcement.source_url && (
                <a
                  href={announcement.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold shadow hover:from-blue-600 hover:to-indigo-700 transition-all duration-200"
                >
                  공고 보러 가기
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 3h7v7m0-7L10 14m0 0v7m0-7H3" />
                  </svg>
                </a>
              )}
              {announcement.original_pdf_url && (
                <a
                  href={announcement.original_pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  download
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-gray-200 bg-white text-gray-800 font-semibold shadow hover:border-gray-300 hover:shadow-md transition-all duration-200"
                >
                  PDF 다운로드
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4" />
                  </svg>
                </a>
              )}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6 animate-fade-in" style={{ animationDelay: '0.2s' }}>
            {activeTab === 'info' && <InfoSection announcement={announcement} />}
            {activeTab === 'commute' && <CommuteSection announcement={announcement} />}
          </div>
          <div className="lg:col-span-1">
            <Sidebar
              announcement={announcement}
              onApply={handleApply}
              isApplying={isApplying}
              hasApplied={hasApplied}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

type EligibilityJson =
  | string
  | number
  | boolean
  | null
  | { [key: string]: EligibilityJson }
  | EligibilityJson[];

type EligibilityValue = EligibilityJson;

function InfoSection({ announcement }: { announcement: AnnouncementDetail }) {
  const imageUrls =
    announcement.image_urls.length > 0
      ? announcement.image_urls
      : ['https://homepass-mock.s3.amazonaws.com/announcements/placeholder.jpg'];
  const hasDepositRange =
    announcement.min_deposit != null && announcement.max_deposit != null;
  const formattedDepositRange = hasDepositRange
    ? `${announcement.min_deposit!.toLocaleString()}만원 ~ ${announcement.max_deposit!.toLocaleString()}만원`
    : '정보 없음';
  const formattedMonthlyRent =
    announcement.monthly_rent != null ? `${announcement.monthly_rent.toLocaleString()}만원` : '정보 없음';
  const scheduleItems = useMemo(
    () => normalizeSchedules(announcement.schedules),
    [announcement.schedules],
  );
  const priceGroups = useMemo<Array<[string, PriceOption[]]>>(() => {
    if (!announcement.price || announcement.price.length === 0) {
      return [];
    }
    const groups = new Map<string, PriceOption[]>();
    announcement.price.forEach((option) => {
      if (!option) return;
      const key = option.supply_type_primary || '기타 공급';
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(option);
    });
    return Array.from(groups.entries());
  }, [announcement.price]);
  const formatAmount = (value?: number | null) => {
    if (value === undefined || value === null || Number.isNaN(value)) {
      return '정보 없음';
    }
    return `${value.toLocaleString()}만원`;
  };

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden shadow-lg">
        <div className="p-4">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-900">
            <span>🖼️</span> 이미지 갤러리
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {imageUrls.map((img, idx) => (
              <div
                key={`${img}-${idx}`}
                className="aspect-video bg-gray-100 rounded-xl overflow-hidden border border-gray-200 flex items-center justify-center"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={img}
                  alt={`${announcement.title} 이미지 ${idx + 1}`}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card gradient className="shadow-lg">
        <div className="p-6 space-y-4">
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2 text-gray-900">
            <span>📊</span> 신청 자격 및 모집 정보
          </h2>
          <InfoRow
            label="모집 세대수"
            value={
              announcement.total_households !== undefined && announcement.total_households !== null
                ? `${announcement.total_households}세대`
                : '정보 없음'
            }
            emoji="🏘️"
          />
          <EligibilitySection eligibility={announcement.eligibility} />
          <InfoRow
            label="보증금"
            value={formattedDepositRange}
            emoji="💵"
          />
          <InfoRow
            label="월 임대료"
            value={formattedMonthlyRent}
            emoji="📅"
          />
        </div>
      </Card>

      {priceGroups.length > 0 && (
        <Card gradient className="shadow-lg">
          <div className="p-6 space-y-6">
            <div>
              <h2 className="text-2xl font-bold mb-2 flex items-center gap-2 text-gray-900">
                <span>💰</span> 상세 금액 구성
              </h2>
              <p className="text-sm text-gray-600">
                공급 유형과 타입별 보증금·임대료 정보를 확인하세요.
              </p>
            </div>
            <div className="space-y-6">
              {priceGroups.map(([groupName, items]) => (
                <div key={groupName} className="space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <p className="text-lg font-semibold text-gray-900">{groupName}</p>
                    <span className="text-xs text-gray-500">구성 {items.length}개</span>
                  </div>
                  <div className="overflow-x-auto rounded-2xl border border-gray-100">
                    <table className="min-w-full divide-y divide-gray-100 text-sm text-gray-900">
                      <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
                        <tr>
                          <th className="px-4 py-3 text-left">타입</th>
                          <th className="px-4 py-3 text-left">보증금 비율</th>
                          <th className="px-4 py-3 text-left">공급 구분</th>
                          <th className="px-4 py-3 text-right">보증금</th>
                          <th className="px-4 py-3 text-right">임대료</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 bg-white">
                        {items.map((option, index) => (
                          <tr
                            key={`${groupName}-${option.type ?? 'type'}-${option.deposit_ratio ?? index}`}
                            className="hover:bg-gray-50/70 transition-colors"
                          >
                            <td className="px-4 py-3 font-medium">{option.type ?? '정보 없음'}</td>
                            <td className="px-4 py-3">{option.deposit_ratio ?? '정보 없음'}</td>
                            <td className="px-4 py-3">{option.supply_type_secondary ?? '정보 없음'}</td>
                            <td className="px-4 py-3 text-right">{formatAmount(option.deposit_amount)}</td>
                            <td className="px-4 py-3 text-right">{formatAmount(option.rent_amount)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      <Card gradient className="shadow-lg">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 text-gray-900">
            <span>📅</span> 주요 일정
          </h2>
          {scheduleItems.length > 0 ? (
            <div className="relative">
              <div className="space-y-6">
                {scheduleItems.map((item, idx) => (
                  <div key={item.id} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow ${getScheduleColorClass(
                          idx,
                        )}`}
                      >
                        {idx + 1}
                      </div>
                      {idx < scheduleItems.length - 1 && (
                        <div className="mt-1 mb-1 w-px flex-1 bg-gradient-to-b from-blue-200 via-indigo-200 to-purple-200"></div>
                      )}
                    </div>
                    <div className="flex-1 rounded-2xl border border-gray-200/80 bg-white/90 p-4 shadow-sm">
                      <p className="text-sm font-semibold text-gray-900">{item.title}</p>
                      <p className="text-sm text-gray-900 mt-1">{item.displayDate}</p>
                      {item.isRange && item.startText && item.endText && (
                        <p className="text-xs text-gray-500 mt-2">
                          시작 {item.startText} · 종료 {item.endText}
                        </p>
                      )}
                      {!item.isRange && item.startText && (
                        <p className="text-xs text-gray-500 mt-2">예정일 {item.startText}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">등록된 일정이 없습니다.</p>
          )}
        </div>
      </Card>
    </div>
  );
}

function CommuteSection({ announcement }: { announcement: AnnouncementDetail }) {
  const [selectedCategory, setSelectedCategory] = useState('subway');

  const { data: commuteInfo, isLoading: isLoadingCommute, error: commuteError } = useQuery({
    queryKey: ['commute-info', announcement.announcement_id],
    queryFn: () => getCommuteInfo(announcement.announcement_id),
    enabled: !!announcement.latitude && !!announcement.longitude,
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="space-y-6">
      <Card className="shadow-lg overflow-hidden">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <span>🗺️</span> 위치
          </h2>
          {announcement.latitude && announcement.longitude ? (
            <NaverMap
              latitude={announcement.latitude}
              longitude={announcement.longitude}
              selectedCategory={selectedCategory}
              commuteInfo={commuteInfo}
            />
          ) : (
            <div className="aspect-video bg-gradient-to-br from-blue-100 via-indigo-100 to-purple-100 rounded-xl flex items-center justify-center border-2 border-dashed border-blue-300 text-gray-900 font-semibold">
              위치 정보가 등록되지 않았습니다
            </div>
          )}
        </div>
      </Card>

      <Card gradient className="shadow-lg">
        <div className="p-6 space-y-4">
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
            <span>🚇</span> 출퇴근 정보
          </h2>

          {isLoadingCommute ? (
            <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
              <div className="animate-spin w-8 h-8 mx-auto mb-2 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              <div className="text-sm text-gray-900 font-semibold">출퇴근 정보 계산 중...</div>
            </div>
          ) : commuteError ? (
            <div className="p-6 bg-yellow-50 rounded-xl border border-yellow-200">
              <div className="text-sm text-yellow-700">출퇴근 정보를 불러올 수 없습니다.</div>
            </div>
          ) : commuteInfo ? (
            <>
              <InfoRow
                label="출발지"
                value={commuteInfo.start_address}
                emoji="🏠"
              />
              <InfoRow
                label="직장"
                value={commuteInfo.end_address}
                emoji="📍"
              />
              <InfoRow
                label="거리"
                value={`${(commuteInfo.distance / 1000).toFixed(1)} km`}
                emoji="📏"
              />
              <InfoRow
                label="소요 시간"
                value={`약 ${commuteInfo.duration_minutes}분`}
                emoji="⏱️"
              />
            </>
          ) : (
            <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
              <div className="text-sm text-gray-900 font-semibold">출퇴근 정보가 없습니다.</div>
            </div>
          )}
        </div>
      </Card>

      <Card gradient className="shadow-lg">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <span>🏪</span> 주변 시설
          </h2>
          <p className="text-sm font-semibold text-gray-900 mb-4">
            반경 10km 이내 시설을 가까운 순서대로 보여드립니다.
          </p>
          <div className="flex gap-2 mb-6 flex-wrap">
            {[
              { id: 'subway', label: '🚇 지하철역' },
              { id: 'school', label: '🏫 학교' },
              { id: 'store', label: '🏪 편의점' },
              { id: 'hospital', label: '🏥 병원' },
              { id: 'park', label: '🌳 공원' },
            ].map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  selectedCategory === category.id
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {category.label}
              </button>
            ))}
          </div>
          <NearbyPlacesPanel
            latitude={announcement.latitude}
            longitude={announcement.longitude}
            category={selectedCategory}
          />
        </div>
      </Card>
    </div>
  );
}

function Sidebar({
  announcement,
  onApply,
  isApplying,
  hasApplied,
}: {
  announcement: AnnouncementDetail;
  onApply: () => void;
  isApplying: boolean;
  hasApplied: boolean;
}) {
  const hasDepositRange =
    announcement.min_deposit != null && announcement.max_deposit != null;
  const averageDeposit = hasDepositRange
    ? Math.round((announcement.min_deposit! + announcement.max_deposit!) / 2)
    : undefined;
  const formattedDepositRange = hasDepositRange
    ? `${announcement.min_deposit!.toLocaleString()}만원 ~ ${announcement.max_deposit!.toLocaleString()}만원`
    : '정보 없음';
  const formattedMonthlyRent =
    announcement.monthly_rent != null ? `${announcement.monthly_rent.toLocaleString()}만원` : '정보 없음';
  const { data: myBookmarks } = useQuery<Announcement[]>({
    queryKey: ['bookmarks', 'me'],
    queryFn: getMyBookmarks,
    staleTime: 30_000,
  });
  const isInitiallyBookmarked =
    (myBookmarks ?? []).some((a) => a.announcement_id === announcement.announcement_id);

  return (
    <div className="space-y-6 animate-fade-in lg:sticky lg:top-24" style={{ animationDelay: '0.3s' }}>
      <Card gradient className="shadow-xl">
        <div className="p-6 space-y-4">
          <h3 className="text-xl font-bold flex items-center gap-2">
            <span>💰</span> 임대 금액
          </h3>
          <InfoRow
            label="보증금"
            value={formattedDepositRange}
            emoji="💵"
          />
          <InfoRow
            label="월 임대료"
            value={formattedMonthlyRent}
            emoji="📅"
          />
          <div className="pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-900 mb-2 font-semibold">예상 평균 금액</p>
            <div className="p-4 bg-gradient-to-r from-purple-100 to-pink-100 rounded-xl border border-purple-200 text-center">
              <p className="text-xl font-bold text-purple-700">
                {averageDeposit !== undefined ? `보증금 ${averageDeposit.toLocaleString()}만원` : '보증금 정보 없음'}
                <br />
                {announcement.monthly_rent != null
                  ? `+ 월 ${announcement.monthly_rent.toLocaleString()}만원`
                  : '+ 월 임대료 정보 없음'}
              </p>
            </div>
          </div>
        </div>
      </Card>

      <Card gradient className="shadow-xl">
        <div className="p-6 space-y-3">
          <button
            onClick={onApply}
            disabled={isApplying || hasApplied}
            className={`w-full px-6 py-4 rounded-xl font-bold text-lg transition-all duration-200 ${
              hasApplied
                ? 'bg-green-500 text-white cursor-default'
                : 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700'
            } shadow-lg hover:shadow-xl disabled:opacity-70 disabled:cursor-not-allowed`}
          >
            {hasApplied ? '✅ 신청 완료' : isApplying ? '신청 중...' : '✨ 신청하기'}
          </button>
          <div className="w-full flex justify-center">
            <BookmarkButton
              announcementId={announcement.announcement_id}
              initialIsBookmarked={isInitiallyBookmarked}
              size={28}
            />
          </div>
        </div>
      </Card>
    </div>
  );
}

function InfoRow({ label, value, emoji }: { label: string; value: string; emoji: string }) {
  return (
    <div className="flex justify-between items-center p-3 bg-gradient-to-r from-blue-50/50 to-indigo-50/50 rounded-lg border border-blue-100">
      <span className="text-gray-900 font-semibold flex items-center gap-2">
        <span>{emoji}</span> {label}
      </span>
      <span className="font-bold text-gray-900 text-sm">{value}</span>
    </div>
  );
}

function EligibilitySection({ eligibility }: { eligibility?: string | null }) {
  const parsed = useMemo(() => {
    if (!eligibility) return null;
    try {
      const result = JSON.parse(eligibility) as EligibilityValue;
      if (result && typeof result === 'object' && !Array.isArray(result)) {
        return result;
      }
    } catch {
      return null;
    }
    return null;
  }, [eligibility]);

  if (!parsed) {
    return (
      <InfoRow
        label="신청 자격"
        value={eligibility ?? '정보 없음'}
        emoji="🧾"
      />
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <span>🧾</span> 신청 자격
      </h3>
      {Object.entries(parsed).map(([supplyType, supplyValue]) => (
        <div key={supplyType} className="rounded-2xl border border-blue-100 bg-gradient-to-r from-blue-50/40 to-indigo-50/40 p-4 space-y-3">
          <p className="text-base font-bold text-blue-700">{supplyType}</p>
          {typeof supplyValue === 'object' && supplyValue !== null ? (
            <div className="space-y-3">
              {Object.entries(supplyValue as Record<string, EligibilityValue>).map(([groupName, groupValue]) => (
                <EligibilityGroupCard key={groupName} title={groupName} value={groupValue} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-600">{String(supplyValue)}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function EligibilityGroupCard({ title, value }: { title: string; value: EligibilityValue }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl bg-white border border-gray-200 shadow-sm overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-2 px-4 py-3"
      >
        <p className="font-semibold text-gray-900">{title}</p>
        <span className="text-xs text-gray-500 flex items-center gap-1">
          {open ? '접기' : '펼치기'}
          <span className={`transition-transform ${open ? 'rotate-180' : ''}`}>⌄</span>
        </span>
      </button>
      {open && (
        <div className="px-4 pb-4">
          {renderEligibilityDetails(value)}
        </div>
      )}
    </div>
  );
}

function renderEligibilityDetails(value: EligibilityValue) {
  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean' ||
    value === null
  ) {
    const displayValue =
      value === null ? '정보 없음' : `${value}`;
    return <p className="text-sm text-gray-600 whitespace-pre-line">{displayValue}</p>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <p className="text-sm text-gray-600">정보 없음</p>;
    }
    return (
      <div className="space-y-2">
        {value.map((item, index) => (
          <div key={index} className="rounded-lg bg-gray-50 p-3 border border-gray-100">
            {renderEligibilityDetails(item)}
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === 'object' && value !== null) {
    const entries = Object.entries(value as Record<string, EligibilityValue>);
    return (
      <div className="space-y-2 text-sm text-gray-700">
        {entries.map(([key, detail]) => (
          <div key={key} className="flex flex-col gap-1 rounded-lg bg-gray-50 p-3 border border-gray-100">
            <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">{key}</span>
            {typeof detail === 'object' && detail !== null ? (
              <div className="space-y-1">
                {Object.entries(detail as Record<string, EligibilityValue>).map(([innerKey, innerVal]) => (
                  <div key={innerKey} className="flex flex-col gap-1 rounded-md bg-white/70 p-2 border border-gray-100">
                    <span className="text-xs text-gray-500">{innerKey}</span>
                    {renderEligibilityDetails(innerVal)}
                  </div>
                ))}
              </div>
            ) : (
              <span className="text-sm text-gray-800">
                {typeof detail === 'string' || typeof detail === 'number' || typeof detail === 'boolean'
                  ? String(detail)
                  : '정보 없음'}
              </span>
            )}
          </div>
        ))}
      </div>
    );
  }

  return <p className="text-sm text-gray-600">정보 없음</p>;
}

function normalizeSchedules(raw: AnnouncementDetail['schedules']): NormalizedScheduleItem[] {
  if (!raw) {
    return [];
  }

  if (Array.isArray(raw)) {
    return raw
      .filter((item) => item && (item.event || item.date))
      .map((item, index) => createScheduleItem(item.event, item.date, index));
  }

  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw);
      return normalizeSchedules(parsed as AnnouncementDetail['schedules']);
    } catch {
      return [createScheduleItem('주요 일정', raw, 0)];
    }
  }

  if (typeof raw === 'object') {
    return Object.entries(raw as Record<string, string>).map(([event, date], index) =>
      createScheduleItem(event, typeof date === 'string' ? date : String(date ?? ''), index),
    );
  }

  return [];
}

function createScheduleItem(event?: string, dateText?: string, index = 0): NormalizedScheduleItem {
  const title = event?.trim() || `일정 ${index + 1}`;
  const formatted = formatScheduleDate(dateText);
  return {
    id: `${title}-${index}`,
    title,
    displayDate: formatted.display,
    rawDate: dateText,
    startText: formatted.startText,
    endText: formatted.endText,
    isRange: formatted.isRange,
  };
}

function formatScheduleDate(dateText?: string) {
  const fallback = {
    display: '일정 미정',
    startText: undefined as string | undefined,
    endText: undefined as string | undefined,
    isRange: false,
  };

  if (!dateText) {
    return fallback;
  }

  const cleaned = dateText.replace(/\s+/g, ' ').trim();
  if (!cleaned) {
    return fallback;
  }

  const parts = cleaned.split('~').map((part) => part.trim()).filter(Boolean);
  if (parts.length >= 2) {
    const startFormatted = formatSingleDate(parts[0]);
    const endFormatted = formatSingleDate(parts[1]);
    return {
      display: `${startFormatted} ~ ${endFormatted}`,
      startText: startFormatted,
      endText: endFormatted,
      isRange: true,
    };
  }

  const singleFormatted = formatSingleDate(parts[0] ?? cleaned);
  return {
    display: singleFormatted,
    startText: singleFormatted,
    endText: undefined,
    isRange: false,
  };
}

function formatSingleDate(value: string) {
  const date = new Date(value);
  if (!Number.isNaN(date.getTime())) {
    return new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      weekday: 'short',
    }).format(date);
  }
  return value;
}

function getScheduleColorClass(index: number) {
  return scheduleColorPalette[index % scheduleColorPalette.length];
}

function NearbyPlacesPanel({
  latitude,
  longitude,
  category,
}: {
  latitude?: number;
  longitude?: number;
  category: string;
}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['nearby-places-list', latitude, longitude, category],
    queryFn: () => getNearbyPlaces(latitude!, longitude!, category),
    enabled: !!latitude && !!longitude,
    staleTime: 5 * 60 * 1000,
  });

  if (!latitude || !longitude) {
    return (
      <div className="p-6 bg-yellow-50 rounded-xl border border-yellow-200 text-center">
        <div className="text-4xl mb-2">📍</div>
        <div className="text-sm text-yellow-600">위치 정보가 없어 주변 시설을 검색할 수 없습니다.</div>
      </div>
    );
  }

  if (isLoading) {
    return (
          <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
        <div className="animate-spin w-8 h-8 mx-auto mb-2 border-4 border-blue-500 border-t-transparent rounded-full"></div>
            <div className="text-sm text-gray-900 font-semibold">주변 시설 검색 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 rounded-xl border border-red-200 text-center">
        <div className="text-4xl mb-2">⚠️</div>
        <div className="text-sm text-red-600">주변 시설 검색 중 오류가 발생했습니다.</div>
      </div>
    );
  }

  if (!data || data.places.length === 0) {
    return (
      <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
        <div className="text-4xl mb-2">📍</div>
        <div className="text-sm text-gray-900 font-semibold">주변에서 해당 시설을 찾을 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {data.places.map((place, idx) => (
        <div
          key={`${place.name}-${idx}`}
          className="p-4 bg-white rounded-xl border border-gray-200 hover:shadow-md transition-all"
        >
          <div className="flex justify-between items-start mb-2">
            <h4 className="font-bold text-gray-900">{place.name}</h4>
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">#{idx + 1}</span>
          </div>
          <p className="text-sm text-gray-900 font-medium mb-1">📍 {place.address}</p>
          {place.telephone && <p className="text-sm text-gray-900 font-medium">☎️ {place.telephone}</p>}
        </div>
      ))}
    </div>
  );
}

