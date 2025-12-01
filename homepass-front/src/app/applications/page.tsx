'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import Card from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { getApplications } from '@/lib/api/applications';
import type { ApplicationItem } from '@/types/api';

type StatusType = 'all' | 'applied' | 'document_review' | 'won' | 'failed';

const statusLabels: Record<StatusType, { label: string; icon: string; color: string }> = {
  all: { label: '전체', icon: '📋', color: 'from-gray-500 to-gray-600' },
  applied: { label: '신청 완료', icon: '✅', color: 'from-blue-500 to-blue-600' },
  document_review: { label: '서류 심사', icon: '📄', color: 'from-amber-500 to-amber-600' },
  won: { label: '당첨', icon: '🎉', color: 'from-emerald-500 to-emerald-600' },
  failed: { label: '미당첨', icon: '❌', color: 'from-red-500 to-red-600' },
};

export default function ApplicationsPage() {
  const [selectedStatus, setSelectedStatus] = useState<StatusType>('all');
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getApplications();
        setApplications(data.items);
      } catch (err) {
        console.error(err);
        setError('신청 내역을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredApplications = useMemo(() => {
    if (selectedStatus === 'all') {
      return applications;
    }
    return applications.filter((app) => app.status === selectedStatus);
  }, [applications, selectedStatus]);

  const statusCounts = useMemo(() => {
    const counts: Record<StatusType, number> = {
      all: applications.length,
      applied: 0,
      document_review: 0,
      won: 0,
      failed: 0,
    };

    applications.forEach((app) => {
      counts[app.status] = (counts[app.status] ?? 0) + 1;
    });

    return counts;
  }, [applications]);

  const getStatusBadge = (status: string) => {
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
    if (!value) return '미정';
    return value.slice(0, 10);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-indigo-50/30">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            신청 내역
          </h1>
          <p className="text-gray-600">청약 신청 현황을 확인하세요</p>
        </div>

        <Card className="mb-8 p-4 shadow-lg animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div className="flex flex-wrap gap-3">
            {(Object.keys(statusLabels) as StatusType[]).map((status) => {
              const statusInfo = statusLabels[status];
              const isActive = selectedStatus === status;

              return (
                <button
                  key={status}
                  onClick={() => setSelectedStatus(status)}
                  className={`relative px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 ${
                    isActive
                      ? `bg-gradient-to-r ${statusInfo.color} text-white shadow-lg transform scale-105`
                      : 'bg-white text-gray-700 hover:bg-gray-50 border-2 border-gray-200 hover:border-gray-300 shadow-sm'
                  }`}
                >
                  <span className="mr-2">{statusInfo.icon}</span>
                  {statusInfo.label}
                  <span
                    className={`ml-2 inline-flex items-center justify-center rounded-full px-2 py-0.5 text-xs font-bold ${
                      isActive ? 'bg-white/90 text-gray-900' : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {status === 'all' ? applications.length : statusCounts[status] ?? 0}
                  </span>
                  {isActive && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-white rounded-full animate-pulse"></span>
                  )}
                </button>
              );
            })}
          </div>
        </Card>

        {loading && (
          <div className="py-16 text-center text-gray-500 animate-pulse">
            신청 내역을 불러오는 중입니다...
          </div>
        )}

        {!loading && error && (
          <Card className="mb-6 border-red-200 bg-red-50 text-red-700">
            <div className="p-6 text-center font-medium">{error}</div>
          </Card>
        )}

        {!loading && !error && (
          <div className="space-y-4">
            {filteredApplications.length === 0 ? (
              <Card className="animate-fade-in">
                <div className="p-16 text-center">
                  <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-gray-500 text-lg font-medium">신청 내역이 없습니다</p>
                  <p className="text-gray-400 text-sm mt-2">새로운 공고에 신청해보세요!</p>
                </div>
              </Card>
            ) : (
              filteredApplications.map((application, idx) => (
                <Card
                  key={application.application_id}
                  hover
                  gradient
                  className="animate-fade-in"
                  style={{ animationDelay: `${idx * 0.1}s` }}
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-5 gap-4">
                      <div className="flex-1">
                        <h3 className="text-xl font-bold text-gray-900 mb-3 hover:text-blue-600 transition-colors">
                          {application.announcement_title}
                        </h3>
                        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                          <div className="flex items-center gap-1.5">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            신청일: {formatDate(application.applied_at)}
                          </div>
                          {application.dday !== undefined && (
                            <div className="flex items-center gap-1.5 text-red-500 font-medium">
                              ⏰ D-{application.dday}
                            </div>
                          )}
                          {application.region && (
                            <div className="flex items-center gap-1.5">
                              📍 {application.region}
                            </div>
                          )}
                          {application.housing_type && (
                            <div className="flex items-center gap-1.5">
                              🏠 {application.housing_type}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="ml-4">{getStatusBadge(application.status)}</div>
                    </div>

                    <div className="flex gap-3 pt-4 border-t border-gray-200">
                      {application.announcement_id !== undefined && (
                        <Link
                          href={`/announcements/${application.announcement_id}`}
                          className="flex-1 px-4 py-2.5 text-sm font-medium bg-gradient-to-r from-gray-50 to-gray-100 text-gray-700 rounded-lg hover:from-blue-50 hover:to-indigo-50 hover:text-blue-600 hover:shadow-md transition-all duration-200 text-center border border-gray-200 hover:border-blue-200"
                        >
                          공고 보기
                        </Link>
                      )}
                      <Link
                        href={`/applications/${application.application_id}`}
                        className="flex-1 px-4 py-2.5 text-sm font-medium bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 shadow-md hover:shadow-lg transition-all duration-200 text-center"
                      >
                        상세 보기
                      </Link>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
