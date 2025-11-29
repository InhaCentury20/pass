'use client';

import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { fetchUserProfile } from '@/lib/api/users';
import { login } from '@/lib/api/auth';

const TEST_USER = {
  email: 'testuser@example.com',
  password: 'TestPass123!',
};

export default function AuthBootstrap() {
  const queryClient = useQueryClient();

  useEffect(() => {
    let mounted = true;
    const run = async () => {
      try {
        // 최초 1회만 시도
        if (typeof window !== 'undefined' && sessionStorage.getItem('autoLoginDone') === '1') return;
        await fetchUserProfile();
        if (mounted) {
          sessionStorage.setItem('autoLoginDone', '1');
        }
      } catch {
        // 401 등인 경우 테스트 계정으로 로그인 시도
        try {
          await login(TEST_USER);
          await queryClient.invalidateQueries(); // 전체 무효화로 사용자 상태 최신화
          if (mounted) {
            sessionStorage.setItem('autoLoginDone', '1');
          }
        } catch {
          // 실패시 무시
        }
      }
    };
    run();
    return () => {
      mounted = false;
    };
  }, [queryClient]);

  return null;
}


