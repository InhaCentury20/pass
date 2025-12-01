'use client';

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Card from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import type { Announcement, AnnouncementDetail } from '@/types/api';
import BookmarkButton from '@/components/common/BookmarkButton';
import { getMyBookmarks } from '@/lib/api/bookmarks';
import { getNearbyPlaces } from '@/lib/api/places';
import { createApplication } from '@/lib/api/applications';
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

type TabType = 'info' | 'commute' | 'qa';

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
    { id: 'qa', label: 'Q&A', icon: '💬' },
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
          <div className="flex items-center gap-2 text-gray-600">
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

        <Card className="mb-6 shadow-lg animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <nav className="flex space-x-2 p-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm transition-all duration-200 ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg scale-105'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6 animate-fade-in" style={{ animationDelay: '0.2s' }}>
            {activeTab === 'info' && <InfoSection announcement={announcement} />}
            {activeTab === 'commute' && <CommuteSection announcement={announcement} />}
            {activeTab === 'qa' && <QATab />}
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

type EligibilityValue = string | Record<string, string | number | boolean>;

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

      <Card gradient className="shadow-lg">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 text-gray-900">
            <span>📅</span> 주요 일정
          </h2>
          <div className="space-y-3">
            {announcement.schedules.length > 0 ? (
              announcement.schedules.map((schedule, idx) => (
                <div
                  key={`${schedule.event}-${idx}`}
                  className="flex justify-between items-center p-4 bg-gradient-to-r from-gray-50 to-blue-50/30 rounded-xl border border-gray-200 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                        idx === 0 ? 'bg-blue-500' : idx === 1 ? 'bg-indigo-500' : 'bg-purple-500'
                      }`}
                    >
                      {idx + 1}
                    </div>
                    <span className="text-gray-700 font-medium">{schedule.event}</span>
                  </div>
                  <span className="font-bold text-gray-900">{schedule.date}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">등록된 일정이 없습니다.</p>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}

function CommuteSection({ announcement }: { announcement: AnnouncementDetail }) {
  const [selectedCategory, setSelectedCategory] = useState('subway');

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
            />
          ) : (
            <div className="aspect-video bg-gradient-to-br from-blue-100 via-indigo-100 to-purple-100 rounded-xl flex items-center justify-center border-2 border-dashed border-blue-300 text-gray-600">
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
          <InfoRow
            label="기준 주소"
            value={announcement.commute_base_address ?? '정보 없음'}
            emoji="📍"
          />
          <InfoRow
            label="평균 이동 시간"
            value={
              announcement.commute_time !== undefined && announcement.commute_time !== null
                ? `${announcement.commute_time}분`
                : '정보 없음'
            }
            emoji="⏱️"
          />
        </div>
      </Card>

      <Card gradient className="shadow-lg">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <span>🏪</span> 주변 시설
          </h2>
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

function QATab() {
  const [question, setQuestion] = useState('');

  return (
    <Card gradient className="shadow-lg">
      <div className="p-6 space-y-4">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <span>💬</span> AI 챗봇에게 질문하기
        </h2>
        <div className="h-48 bg-gradient-to-br from-gray-50 to-blue-50/30 rounded-xl p-6 border border-gray-200 flex items-center justify-center text-gray-400">
          곧 AI 챗봇과의 대화를 제공할 예정입니다.
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="질문을 입력하세요..."
            className="flex-1 px-5 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all text-base"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                setQuestion('');
              }
            }}
          />
          <button className="px-8 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-indigo-700 shadow-lg hover:shadow-xl transition-all duration-200">
            전송
          </button>
        </div>
      </div>
    </Card>
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
    <div className="space-y-6 animate-fade-in" style={{ animationDelay: '0.3s' }}>
      <Card gradient className="shadow-xl sticky top-24">
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
            <p className="text-sm text-gray-500 mb-2 font-medium">예상 평균 금액</p>
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
      <span className="text-gray-600 font-medium flex items-center gap-2">
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
      if (result && typeof result === 'object') {
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
                <div key={groupName} className="rounded-xl bg-white border border-gray-200 p-4 shadow-sm">
                  <p className="font-semibold text-gray-900 mb-2">{groupName}</p>
                  {renderEligibilityDetails(groupValue)}
                </div>
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

function renderEligibilityDetails(value: EligibilityValue) {
  if (typeof value === 'string') {
    return <p className="text-sm text-gray-600 whitespace-pre-line">{value || '정보 없음'}</p>;
  }

  const entries = Object.entries(value ?? {});
  return (
    <div className="space-y-2 text-sm text-gray-700">
      {entries.map(([key, detail]) => (
        <div key={key} className="flex flex-col gap-1 rounded-lg bg-gray-50 p-3 border border-gray-100">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">{key}</span>
          {typeof detail === 'object' && detail !== null ? (
            <div className="space-y-1">
              {Object.entries(detail as Record<string, string>).map(([innerKey, innerVal]) => (
                <div key={innerKey} className="flex justify-between gap-2">
                  <span className="text-xs text-gray-500">{innerKey}</span>
                  <span className="flex-1 text-right text-sm text-gray-700">{innerVal || '정보 없음'}</span>
                </div>
              ))}
            </div>
          ) : (
            <span className="text-sm text-gray-800">{String(detail || '정보 없음')}</span>
          )}
        </div>
      ))}
    </div>
  );
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
        <div className="text-sm text-gray-600">주변 시설 검색 중...</div>
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
        <div className="text-sm text-gray-600">주변에서 해당 시설을 찾을 수 없습니다.</div>
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
          <p className="text-sm text-gray-600 mb-1">📍 {place.address}</p>
          {place.telephone && <p className="text-sm text-gray-600">☎️ {place.telephone}</p>}
        </div>
      ))}
    </div>
  );
}

