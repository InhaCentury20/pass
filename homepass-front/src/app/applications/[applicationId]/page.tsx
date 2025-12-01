'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import Card from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { getApplicationDetail } from '@/lib/api/applications';
import type { ApplicationDetail } from '@/types/api';

const statusBadge = (status: string) => {
  switch (status) {
    case 'applied':
      return <Badge variant="info" icon="✅">신청 완료</Badge>;
    case 'document_review':
      return <Badge variant="warning" icon="📄">서류 심사</Badge>;
    case 'won':
      return <Badge variant="success" icon="🎉">당첨</Badge>;
    case 'failed':
      return <Badge variant="danger" icon="❌">미당첨</Badge>;
    default:
      return <Badge>{status}</Badge>;
  }
};

const formatDate = (value?: string) => {
  if (!value) return '정보 없음';
  return new Date(value).toLocaleDateString('ko-KR');
};

const formatCurrency = (value?: number) => {
  if (value === undefined || value === null) return '정보 없음';
  return new Intl.NumberFormat('ko-KR').format(value) + '원';
};

export default function ApplicationDetailPage() {
  const params = useParams<{ applicationId: string }>();
  const applicationId = Number(params?.applicationId);
  const [detail, setDetail] = useState<ApplicationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!applicationId) {
      setError('올바르지 않은 신청 ID 입니다.');
      setLoading(false);
      return;
    }

    const fetchDetail = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getApplicationDetail(applicationId);
        setDetail(data);
      } catch (err) {
        console.error(err);
        setError('신청 상세 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.');
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [applicationId]);

  const heroImage = useMemo(() => detail?.announcement_detail?.image_urls?.[0], [detail]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-indigo-50/30">
      <div className="container mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center gap-3 text-sm text-gray-600">
          <Link href="/applications" className="text-blue-600 hover:underline">
            ← 신청 내역으로 돌아가기
          </Link>
          {detail && (
            <span className="text-gray-400">
              신청 ID #{detail.application_id}
            </span>
          )}
        </div>

        {loading && (
          <Card className="p-10 text-center text-gray-500 animate-pulse">
            신청 상세 정보를 불러오는 중입니다...
          </Card>
        )}

        {!loading && error && (
          <Card className="p-8 border border-red-200 bg-red-50 text-red-700 text-center font-medium">
            {error}
          </Card>
        )}

        {!loading && !error && detail && (
          <div className="space-y-6">
            <Card gradient className="p-6 md:p-8">
              <div className="flex flex-col gap-6">
                {heroImage && (
                  <div
                    className="h-48 rounded-2xl bg-cover bg-center shadow-inner"
                    style={{ backgroundImage: `url(${heroImage})` }}
                  />
                )}

                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                      {detail.announcement_title}
                    </h1>
                    {statusBadge(detail.status)}
                  </div>
                  <div className="text-sm text-gray-600 flex flex-wrap gap-4">
                    <span>신청일: {formatDate(detail.applied_at)}</span>
                    <span>상태 업데이트: {formatDate(detail.status_updated_at)}</span>
                    {typeof detail.dday === 'number' && (
                      <span className="text-red-500 font-semibold">D-{detail.dday}</span>
                    )}
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  {detail.announcement_id && (
                    <Link
                      href={`/announcements/${detail.announcement_id}`}
                      className="inline-flex items-center justify-center rounded-xl border border-gray-200 bg-white px-4 py-3 font-medium text-gray-700 hover:border-blue-300 hover:text-blue-600 transition-colors"
                    >
                      공고 상세 보기
                    </Link>
                  )}
                  {detail.announcement_detail?.source_url ? (
                    <a
                      href={detail.announcement_detail.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 px-4 py-3 font-semibold text-white shadow hover:from-blue-600 hover:to-indigo-700"
                    >
                      원문 보기
                    </a>
                  ) : (
                    <div className="inline-flex items-center justify-center rounded-xl bg-gray-100 px-4 py-3 text-sm text-gray-500">
                      원문 링크 없음
                    </div>
                  )}
                </div>
              </div>
            </Card>

            <div className="grid gap-6 md:grid-cols-2">
              <Card className="p-6 space-y-4">
                <h2 className="text-lg font-semibold text-gray-900">신청 정보</h2>
                <dl className="space-y-3 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <dt className="text-gray-500">신청 상태</dt>
                    <dd className="font-medium">{statusBadge(detail.status)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">신청일</dt>
                    <dd className="font-medium">{formatDate(detail.applied_at)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">최종 갱신</dt>
                    <dd className="font-medium">{formatDate(detail.status_updated_at)}</dd>
                  </div>
                </dl>
              </Card>

              <Card className="p-6 space-y-4">
                <h2 className="text-lg font-semibold text-gray-900">공고 요약</h2>
                {detail.announcement_detail ? (
                  <div className="space-y-3 text-sm text-gray-600">
                    <div className="flex justify-between">
                      <span className="text-gray-500">주택 유형</span>
                      <span className="font-medium">{detail.announcement_detail.housing_type ?? '정보 없음'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">지역</span>
                      <span className="font-medium">{detail.announcement_detail.region ?? '정보 없음'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">마감일</span>
                      <span className="font-medium">
                        {formatDate(detail.announcement_detail.application_end_date)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">보증금(최소/최대)</span>
                      <span className="font-medium">
                        {formatCurrency(detail.announcement_detail.min_deposit)} /{' '}
                        {formatCurrency(detail.announcement_detail.max_deposit)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">월 임대료</span>
                      <span className="font-medium">{formatCurrency(detail.announcement_detail.monthly_rent)}</span>
                    </div>
                    {detail.announcement_detail.eligibility && (
                      <div>
                        <span className="text-gray-500 block mb-1">신청 자격</span>
                        <p className="text-gray-700 whitespace-pre-line">
                          {detail.announcement_detail.eligibility}
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500">연결된 공고 정보를 찾을 수 없습니다.</p>
                )}
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

