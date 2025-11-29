'use client';

import { ChangeEvent, FormEvent, useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import Card from '@/components/common/Card';
import {
  fetchUserProfile,
  updateNotificationSettings,
  updatePersonalInfo,
  updatePreferences,
  updateSubscriptionInfo,
} from '@/lib/api/users';
import type {
  NotificationSettingPayload,
  Preference,
  PreferencePayload,
  SubscriptionInfo,
  SubscriptionInfoPayload,
  User,
  UserProfileResponse,
} from '@/types/api';

interface PersonalFormState {
  email: string;
  password: string;
  name: string;
  phone_number: string;
  address: string;
}

interface SubscriptionFormState {
  bank_name: string;
  join_date: string;
  is_household_head: string;
  payment_count: string;
  total_payment_amount: string;
  income_level_percent: string;
}

interface PreferenceFormState {
  locationsText: string;
  housingTypesText: string;
  min_area: string;
  max_area: string;
  max_deposit: string;
  max_monthly_rent: string;
  commute_base_address: string;
  max_commute_time_minutes: string;
  auto_apply_mode: Preference['auto_apply_mode'];
}

interface NotificationFormState {
  new_announcement: boolean;
  auto_apply_complete: boolean;
  dday: boolean;
  result: boolean;
}

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState('');

  const [personalForm, setPersonalForm] = useState<PersonalFormState>({
    email: '',
    password: '',
    name: '',
    phone_number: '',
    address: '',
  });
  const [subscriptionForm, setSubscriptionForm] = useState<SubscriptionFormState>({
    bank_name: '',
    join_date: '',
    is_household_head: '',
    payment_count: '',
    total_payment_amount: '',
    income_level_percent: '',
  });
  const [preferenceForm, setPreferenceForm] = useState<PreferenceFormState>({
    locationsText: '',
    housingTypesText: '',
    min_area: '',
    max_area: '',
    max_deposit: '',
    max_monthly_rent: '',
    commute_base_address: '',
    max_commute_time_minutes: '',
    auto_apply_mode: 'disabled',
  });
  const [notificationForm, setNotificationForm] = useState<NotificationFormState>({
    new_announcement: true,
    auto_apply_complete: true,
    dday: true,
    result: true,
  });

  const [personalStatus, setPersonalStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(
    null,
  );
  const [preferenceStatus, setPreferenceStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [notificationStatus, setNotificationStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(
    null,
  );

  const resetStatusMessages = () => {
    setPersonalStatus(null);
    setSubscriptionStatus(null);
    setPreferenceStatus(null);
    setNotificationStatus(null);
  };

  const populateForms = useCallback((profile: UserProfileResponse) => {
    setUser(profile.user);
    setPersonalForm({
      email: profile.user.email,
      password: '',
      name: profile.user.name ?? '',
      phone_number: profile.user.phone_number ?? '',
      address: profile.user.address ?? '',
    });

    const subscription: SubscriptionInfo | undefined = profile.subscription;
    setSubscriptionForm({
      bank_name: subscription?.bank_name ?? '',
      join_date: subscription?.join_date ? subscription.join_date.slice(0, 10) : '',
      is_household_head:
        subscription?.is_household_head === undefined || subscription.is_household_head === null
          ? ''
          : subscription.is_household_head
            ? 'yes'
            : 'no',
      payment_count: subscription?.payment_count !== undefined && subscription.payment_count !== null
        ? String(subscription.payment_count)
        : '',
      total_payment_amount:
        subscription?.total_payment_amount !== undefined && subscription.total_payment_amount !== null
          ? String(subscription.total_payment_amount)
          : '',
      income_level_percent:
        subscription?.income_level_percent !== undefined && subscription.income_level_percent !== null
          ? String(subscription.income_level_percent)
          : '',
    });

    const preference: Preference | undefined = profile.preference;
    setPreferenceForm({
      locationsText: preference?.locations?.join(', ') ?? '',
      housingTypesText: preference?.housing_types?.join(', ') ?? '',
      min_area: preference?.min_area !== undefined && preference?.min_area !== null ? String(preference.min_area) : '',
      max_area: preference?.max_area !== undefined && preference?.max_area !== null ? String(preference.max_area) : '',
      max_deposit:
        preference?.max_deposit !== undefined && preference?.max_deposit !== null
          ? String(preference.max_deposit)
          : '',
      max_monthly_rent:
        preference?.max_monthly_rent !== undefined && preference?.max_monthly_rent !== null
          ? String(preference.max_monthly_rent)
          : '',
      commute_base_address: preference?.commute_base_address ?? '',
      max_commute_time_minutes:
        preference?.max_commute_time_minutes !== undefined && preference?.max_commute_time_minutes !== null
          ? String(preference.max_commute_time_minutes)
          : '',
      auto_apply_mode: preference?.auto_apply_mode ?? 'disabled',
    });

    setNotificationForm({
      new_announcement: profile.notification?.new_announcement ?? true,
      auto_apply_complete: profile.notification?.auto_apply_complete ?? true,
      dday: profile.notification?.dday ?? true,
      result: profile.notification?.result ?? true,
    });
  }, []);

  const loadProfile = useCallback(async () => {
    setProfileLoading(true);
    setProfileError('');
    try {
      const profile = await fetchUserProfile();
      populateForms(profile);
    } catch (error) {
      console.error(error);
      setProfileError('사용자 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setProfileLoading(false);
    }
  }, [populateForms]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const handlePersonalSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    resetStatusMessages();
    try {
      const payload = {
        email: personalForm.email.trim() || undefined,
        password: personalForm.password ? personalForm.password : undefined,
        name: personalForm.name.trim() || undefined,
        phone_number: personalForm.phone_number.trim() || '',
        address: personalForm.address.trim() || '',
      };
      if (!payload.email) {
        delete payload.email;
      }
      const response = await updatePersonalInfo(payload);
      setUser(response.data);
      setPersonalForm((prev) => ({ ...prev, password: '', email: response.data.email }));
      setPersonalStatus({ type: 'success', message: response.message ?? '개인 정보를 저장했습니다.' });
      await loadProfile();
    } catch (error) {
      let message = '개인 정보 저장 중 오류가 발생했습니다.';
      if (axios.isAxiosError(error)) {
        message =
          (error.response?.data?.detail as string) ||
          (error.response?.data?.message as string) ||
          error.message ||
          message;
      }
      setPersonalStatus({ type: 'error', message });
    }
  };

  const handleSubscriptionSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    resetStatusMessages();
    const payload: SubscriptionInfoPayload = {
      bank_name: subscriptionForm.bank_name.trim() || undefined,
      join_date: subscriptionForm.join_date || undefined,
      payment_count: subscriptionForm.payment_count ? Number(subscriptionForm.payment_count) : undefined,
      total_payment_amount: subscriptionForm.total_payment_amount
        ? Number(subscriptionForm.total_payment_amount)
        : undefined,
      is_household_head:
        subscriptionForm.is_household_head === ''
          ? undefined
          : subscriptionForm.is_household_head === 'yes',
      income_level_percent: subscriptionForm.income_level_percent
        ? Number(subscriptionForm.income_level_percent)
        : undefined,
    };
    try {
      const updated = await updateSubscriptionInfo(payload);
      setSubscriptionStatus({ type: 'success', message: '청약 정보를 저장했습니다.' });
      setSubscriptionForm((prev) => ({
        ...prev,
        bank_name: updated.bank_name ?? '',
      }));
      await loadProfile();
    } catch (error) {
      let message = '청약 정보 저장 중 오류가 발생했습니다.';
      if (axios.isAxiosError(error)) {
        message =
          (error.response?.data?.detail as string) ||
          (error.response?.data?.message as string) ||
          error.message ||
          message;
      }
      setSubscriptionStatus({ type: 'error', message });
    }
  };

  const handlePreferenceSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    resetStatusMessages();
    const payload: PreferencePayload = {
      locations: preferenceForm.locationsText
        ? preferenceForm.locationsText.split(',').map((loc) => loc.trim()).filter(Boolean)
        : undefined,
      housing_types: preferenceForm.housingTypesText
        ? preferenceForm.housingTypesText.split(',').map((type) => type.trim()).filter(Boolean)
        : undefined,
      min_area: preferenceForm.min_area ? Number(preferenceForm.min_area) : undefined,
      max_area: preferenceForm.max_area ? Number(preferenceForm.max_area) : undefined,
      max_deposit: preferenceForm.max_deposit ? Number(preferenceForm.max_deposit) : undefined,
      max_monthly_rent: preferenceForm.max_monthly_rent ? Number(preferenceForm.max_monthly_rent) : undefined,
      commute_base_address: preferenceForm.commute_base_address.trim() || undefined,
      max_commute_time_minutes: preferenceForm.max_commute_time_minutes
        ? Number(preferenceForm.max_commute_time_minutes)
        : undefined,
      auto_apply_mode: preferenceForm.auto_apply_mode ?? undefined,
    };

    try {
      await updatePreferences(payload);
      setPreferenceStatus({ type: 'success', message: '희망 조건 및 자동 신청 설정을 저장했습니다.' });
      await loadProfile();
    } catch (error) {
      let message = '희망 조건 저장 중 오류가 발생했습니다.';
      if (axios.isAxiosError(error)) {
        message =
          (error.response?.data?.detail as string) ||
          (error.response?.data?.message as string) ||
          error.message ||
          message;
      }
      setPreferenceStatus({ type: 'error', message });
    }
  };

  const handleNotificationSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    resetStatusMessages();
    const payload: NotificationSettingPayload = {
      new_announcement: notificationForm.new_announcement,
      auto_apply_complete: notificationForm.auto_apply_complete,
      dday: notificationForm.dday,
      result: notificationForm.result,
    };
    try {
      await updateNotificationSettings(payload);
      setNotificationStatus({ type: 'success', message: '알림 설정을 저장했습니다.' });
      await loadProfile();
    } catch (error) {
      let message = '알림 설정 저장 중 오류가 발생했습니다.';
      if (axios.isAxiosError(error)) {
        message =
          (error.response?.data?.detail as string) ||
          (error.response?.data?.message as string) ||
          error.message ||
          message;
      }
      setNotificationStatus({ type: 'error', message });
    }
  };

  const handlePersonalInputChange =
    (field: keyof PersonalFormState) => (event: ChangeEvent<HTMLInputElement>) => {
      setPersonalForm((prev) => ({ ...prev, [field]: event.target.value }));
    };

  const handleSubscriptionInputChange =
    (field: keyof SubscriptionFormState) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      setSubscriptionForm((prev) => ({ ...prev, [field]: event.target.value }));
    };

  const handlePreferenceInputChange =
    (field: keyof PreferenceFormState) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      setPreferenceForm((prev) => ({ ...prev, [field]: event.target.value }));
    };

  const handleNotificationToggle =
    (field: keyof NotificationFormState) => (event: ChangeEvent<HTMLInputElement>) => {
      setNotificationForm((prev) => ({ ...prev, [field]: event.target.checked }));
    };

  const isAuthenticated = Boolean(user);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-indigo-50/30">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between gap-4 mb-8">
          <h1 className="text-4xl font-bold text-gray-900 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent animate-fade-in">
            설정
          </h1>
          <button
            onClick={loadProfile}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold shadow hover:from-blue-600 hover:to-indigo-700 transition-all disabled:opacity-60"
            disabled={profileLoading}
          >
            새로 고침
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <Card gradient className="shadow-lg animate-fade-in" style={{ animationDelay: '0.1s' }}>
              <div className="p-6 space-y-4">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <span>👤</span> 프로필 요약
                </h2>
                {user ? (
                  <div className="space-y-2 text-sm text-gray-900">
                    <p><span className="font-semibold">이름:</span> {user.name}</p>
                    <p><span className="font-semibold">이메일:</span> {user.email}</p>
                    <p><span className="font-semibold">전화번호:</span> {user.phone_number ?? '미등록'}</p>
                    <p><span className="font-semibold">주소:</span> {user.address ?? '미등록'}</p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-900">사용자 정보를 불러오는 중입니다.</p>
                )}
                {profileError && (
                  <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                    {profileError}
                  </p>
                )}
                <button
                  onClick={loadProfile}
                  className="w-full px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-indigo-700 shadow-lg hover:shadow-xl transition-all disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                  disabled={profileLoading}
                >
                  프로필 새로고침
                </button>
              </div>
            </Card>

            <Card gradient className="shadow-lg animate-fade-in" style={{ animationDelay: '0.15s' }}>
              <div className="p-6 space-y-2 text-sm text-gray-900">
                <p>• 각 섹션에서 개인정보, 청약 정보, 희망 조건, 알림 설정을 수정하면 바로 저장됩니다.</p>
                <p>• 저장 완료 후에는 자동으로 최신 정보를 다시 불러옵니다.</p>
                <p>• 이미지 URL 등 공고 관련 리소스는 S3 주소를 MySQL에 저장하여 제공합니다.</p>
              </div>
            </Card>
          </div>

          <div className="lg:col-span-3">
            {!isAuthenticated ? (
              <Card gradient className="shadow-xl animate-fade-in" style={{ animationDelay: '0.2s' }}>
                <div className="p-10 text-center space-y-4">
                  <h2 className="text-2xl font-semibold text-gray-900">사용자 정보를 불러오는 중입니다</h2>
                  <p className="text-gray-900">잠시만 기다려주세요.</p>
                </div>
              </Card>
            ) : (
              <div className="space-y-6">
                <Card gradient className="shadow-xl animate-fade-in" style={{ animationDelay: '0.2s' }}>
                  <form onSubmit={handlePersonalSubmit} className="p-8 space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-2xl font-bold mb-1 flex items-center gap-3 text-gray-900">
                          <span>👤</span> 개인 정보
                        </h2>
                        <p className="text-sm text-gray-900">이메일을 변경하면 이후 로그인할 때 새 이메일을 사용하세요.</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">이메일</label>
                        <input
                          type="email"
                          value={personalForm.email}
                          onChange={handlePersonalInputChange('email')}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">비밀번호 변경</label>
                        <input
                          type="password"
                          value={personalForm.password}
                          placeholder="변경 시에만 입력하세요"
                          onChange={handlePersonalInputChange('password')}
                          minLength={8}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">이름</label>
                        <input
                          type="text"
                          value={personalForm.name}
                          onChange={handlePersonalInputChange('name')}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">전화번호</label>
                        <input
                          type="tel"
                          value={personalForm.phone_number}
                          onChange={handlePersonalInputChange('phone_number')}
                          placeholder="010-0000-0000"
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-semibold text-gray-900 mb-2">주소</label>
                        <input
                          type="text"
                          value={personalForm.address}
                          onChange={handlePersonalInputChange('address')}
                          placeholder="예: 서울특별시 중구 세종대로 110"
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                    </div>
                    {personalStatus && (
                      <p
                        className={`rounded-xl border px-4 py-3 text-sm ${
                          personalStatus.type === 'error'
                            ? 'border-red-200 bg-red-50 text-red-700'
                            : 'border-emerald-200 bg-emerald-50 text-emerald-700'
                        }`}
                        role="status"
                        aria-live="polite"
                      >
                        {personalStatus.message}
                      </p>
                    )}
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        className="px-8 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-indigo-700 shadow-lg hover:shadow-xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      >
                        저장하기
                      </button>
                    </div>
                  </form>
                </Card>

                <Card gradient className="shadow-xl animate-fade-in" style={{ animationDelay: '0.25s' }}>
                  <form onSubmit={handleSubscriptionSubmit} className="p-8 space-y-6">
                    <h2 className="text-2xl font-bold mb-2 flex items-center gap-3 text-gray-900">
                      <span>🏦</span> 청약 정보
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">가입 은행</label>
                        <input
                          type="text"
                          value={subscriptionForm.bank_name}
                          onChange={handleSubscriptionInputChange('bank_name')}
                          placeholder="예: KB국민은행"
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">가입일</label>
                        <input
                          type="date"
                          value={subscriptionForm.join_date}
                          onChange={handleSubscriptionInputChange('join_date')}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">세대주 여부</label>
                        <select
                          value={subscriptionForm.is_household_head}
                          onChange={handleSubscriptionInputChange('is_household_head')}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all bg-white"
                        >
                          <option value="">선택하세요</option>
                          <option value="yes">예</option>
                          <option value="no">아니오</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">납입 인정 횟수</label>
                        <input
                          type="number"
                          value={subscriptionForm.payment_count}
                          onChange={handleSubscriptionInputChange('payment_count')}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">총 납입 금액 (원)</label>
                        <input
                          type="number"
                          value={subscriptionForm.total_payment_amount}
                          onChange={handleSubscriptionInputChange('total_payment_amount')}
                          placeholder="예: 2400000"
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">소득 분위(%)</label>
                        <input
                          type="number"
                          value={subscriptionForm.income_level_percent}
                          onChange={handleSubscriptionInputChange('income_level_percent')}
                          placeholder="예: 80"
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                    </div>
                    {subscriptionStatus && (
                      <p
                        className={`rounded-xl border px-4 py-3 text-sm ${
                          subscriptionStatus.type === 'error'
                            ? 'border-red-200 bg-red-50 text-red-700'
                            : 'border-emerald-200 bg-emerald-50 text-emerald-700'
                        }`}
                        role="status"
                        aria-live="polite"
                      >
                        {subscriptionStatus.message}
                      </p>
                    )}
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        className="px-8 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-indigo-700 shadow-lg hover:shadow-xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      >
                        저장하기
                      </button>
                    </div>
                  </form>
                </Card>

                <Card gradient className="shadow-xl animate-fade-in" style={{ animationDelay: '0.3s' }}>
                  <form onSubmit={handlePreferenceSubmit} className="p-8 space-y-6">
                    <h2 className="text-2xl font-bold mb-2 flex items-center gap-3 text-gray-900">
                      <span>⭐</span> 희망 조건 및 자동 신청
                    </h2>
                    <div className="space-y-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">
                          희망 지역 (쉼표로 구분)
                        </label>
                        <input
                          type="text"
                          value={preferenceForm.locationsText}
                          onChange={handlePreferenceInputChange('locationsText')}
                          placeholder="예: 서울특별시 강남구, 경기도 성남시"
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">
                          희망 주택 유형 (쉼표로 구분)
                        </label>
                        <input
                          type="text"
                          value={preferenceForm.housingTypesText}
                          onChange={handlePreferenceInputChange('housingTypesText')}
                          placeholder="예: 행복주택, 공공임대"
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-semibold text-gray-900 mb-2">최소 면적 (m²)</label>
                          <input
                            type="number"
                            value={preferenceForm.min_area}
                            onChange={handlePreferenceInputChange('min_area')}
                            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gray-900 mb-2">최대 면적 (m²)</label>
                          <input
                            type="number"
                            value={preferenceForm.max_area}
                            onChange={handlePreferenceInputChange('max_area')}
                            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gray-900 mb-2">최대 보증금 (원)</label>
                          <input
                            type="number"
                            value={preferenceForm.max_deposit}
                            onChange={handlePreferenceInputChange('max_deposit')}
                            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gray-900 mb-2">최대 월 임대료 (만원)</label>
                          <input
                            type="number"
                            value={preferenceForm.max_monthly_rent}
                            onChange={handlePreferenceInputChange('max_monthly_rent')}
                            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-semibold text-gray-900 mb-2">출퇴근 기준 주소</label>
                          <input
                            type="text"
                            value={preferenceForm.commute_base_address}
                            onChange={handlePreferenceInputChange('commute_base_address')}
                            placeholder="예: 서울특별시 강남구"
                            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gray-900 mb-2">
                            최대 출퇴근 시간 (분)
                          </label>
                          <input
                            type="number"
                            value={preferenceForm.max_commute_time_minutes}
                            onChange={handlePreferenceInputChange('max_commute_time_minutes')}
                            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">자동 신청 모드</label>
                        <div className="flex flex-wrap gap-3">
                          {[
                            { id: 'full_auto', label: '완전 자동', icon: '🤖' },
                            { id: 'approval', label: '알림 후 승인', icon: '🔔' },
                            { id: 'disabled', label: '비활성화', icon: '⏸️' },
                          ].map((mode) => (
                            <label
                              key={mode.id}
                              className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 cursor-pointer transition-all ${
                                preferenceForm.auto_apply_mode === mode.id
                                  ? 'border-blue-500 bg-blue-50 text-blue-600'
                                  : 'border-gray-200 hover:border-blue-300'
                              }`}
                            >
                              <input
                                type="radio"
                                name="auto-apply-mode"
                                value={mode.id}
                                checked={preferenceForm.auto_apply_mode === mode.id}
                                onChange={handlePreferenceInputChange('auto_apply_mode')}
                                className="hidden"
                              />
                              <span>{mode.icon}</span>
                              <span className="font-medium">{mode.label}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    </div>
                    {preferenceStatus && (
                      <p
                        className={`rounded-xl border px-4 py-3 text-sm ${
                          preferenceStatus.type === 'error'
                            ? 'border-red-200 bg-red-50 text-red-700'
                            : 'border-emerald-200 bg-emerald-50 text-emerald-700'
                        }`}
                        role="status"
                        aria-live="polite"
                      >
                        {preferenceStatus.message}
                      </p>
                    )}
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        className="px-8 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-indigo-700 shadow-lg hover:shadow-xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      >
                        저장하기
                      </button>
                    </div>
                  </form>
                </Card>

                <Card gradient className="shadow-xl animate-fade-in" style={{ animationDelay: '0.35s' }}>
                  <form onSubmit={handleNotificationSubmit} className="p-8 space-y-6">
                    <h2 className="text-2xl font-bold mb-2 flex items-center gap-3 text-gray-900">
                      <span>🔔</span> 알림 설정
                    </h2>
                    <div className="space-y-4">
                      {[
                        { key: 'new_announcement', label: '새로운 공고 알림', icon: '📢' },
                        { key: 'auto_apply_complete', label: '자동 신청 완료 알림', icon: '✅' },
                        { key: 'dday', label: 'D-day 알림', icon: '⏰' },
                        { key: 'result', label: '경쟁률 및 결과 알림', icon: '📊' },
                      ].map((item) => (
                        <label
                          key={item.key}
                          className="flex items-center justify-between p-5 bg-white rounded-xl border-2 border-gray-200 hover:border-blue-300 transition-all"
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">{item.icon}</span>
                            <span className="text-gray-900 font-semibold">{item.label}</span>
                          </div>
                          <input
                            type="checkbox"
                            checked={notificationForm[item.key as keyof NotificationFormState]}
                            onChange={handleNotificationToggle(item.key as keyof NotificationFormState)}
                            className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                          />
                        </label>
                      ))}
                    </div>
                    {notificationStatus && (
                      <p
                        className={`rounded-xl border px-4 py-3 text-sm ${
                          notificationStatus.type === 'error'
                            ? 'border-red-200 bg-red-50 text-red-700'
                            : 'border-emerald-200 bg-emerald-50 text-emerald-700'
                        }`}
                        role="status"
                        aria-live="polite"
                      >
                        {notificationStatus.message}
                      </p>
                    )}
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        className="px-8 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-indigo-700 shadow-lg hover:shadow-xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      >
                        저장하기
                      </button>
                    </div>
                  </form>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}