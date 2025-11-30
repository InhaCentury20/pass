import { NextResponse } from 'next/server';
import { serverBackendBaseUrl } from '@/lib/api/config';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  const backendUrl = new URL('/api/v1/announcements', serverBackendBaseUrl);
  // 전달할 쿼리 파라미터들 전달
  for (const [key, value] of searchParams.entries()) {
    backendUrl.searchParams.set(key, value);
  }

  try {
    // 필요한 경우 인증 쿠키/헤더를 포워딩
    const reqHeaders = new Headers();
    const cookie = (request.headers.get('cookie') ?? '').trim();
    const authorization = request.headers.get('authorization') ?? '';
    if (cookie) reqHeaders.set('cookie', cookie);
    if (authorization) reqHeaders.set('authorization', authorization);
    reqHeaders.set('accept', 'application/json');

    const res = await fetch(backendUrl.toString(), {
      method: 'GET',
      cache: 'no-store',
      headers: reqHeaders,
      // credentials는 Node fetch에서 직접 쿠키를 넣어 전송하므로 생략
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      // 디버깅 편의를 위해 서버 로그에 상세 기록
      console.error(
        `[proxy/announcements] Upstream non-OK ${res.status} for ${backendUrl.toString()} - body: ${text.slice(0, 500)}`,
      );
      // 업스트림 상태코드를 그대로 전달해 원인 분석을 쉽게 함
      return NextResponse.json(
        {
          message: 'Upstream error',
          upstreamStatus: res.status,
          upstreamBody: text.slice(0, 500),
          upstreamUrl: backendUrl.toString(),
        },
        { status: res.status },
      );
    }
    const data = await res.json();
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`[proxy/announcements] Proxy request failed for ${backendUrl.toString()} - ${message}`);
    return NextResponse.json(
      {
        message: 'Proxy request failed',
        error: message,
        upstreamUrl: backendUrl.toString(),
      },
      { status: 500 },
    );
  }
}


