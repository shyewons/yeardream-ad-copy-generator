const form = document.querySelector('#ad-form');
const button = document.querySelector('#generate');
const statusText = document.querySelector('#status');
const errorText = document.querySelector('#error');
const result = document.querySelector('#result');
const panel = document.querySelector('#result-panel');
const loading = document.querySelector('#loading');
const elapsed = document.querySelector('#elapsed');

// 입력을 JSON으로 변환해서 FastAPI에 전송한다.
form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (button.disabled) return;
    const payload = Object.fromEntries(new FormData(form));
    for (const [key, value] of Object.entries(payload)) {
        payload[key] = value.trim();
        if (!payload[key]) {
            errorText.textContent = '공백만 입력할 수 없어요. 모든 항목을 채워주세요.';
            errorText.hidden = false;
            form.elements.namedItem(key).focus();
            return;
        }
    }
    button.disabled = true;
    button.textContent = '생성 중…';
    panel.setAttribute('aria-busy', 'true');
    errorText.hidden = true;
    result.hidden = true;
    statusText.textContent = '광고를 작성하고 있어요. 모델 상태에 따라 몇 분 걸릴 수 있어요.';
    // 타이머 호출 횟수 대신 실제 경과 시간을 계산한다.
    const startedAt = performance.now();
    const updateElapsed = () => {
        const seconds = Math.floor((performance.now() - startedAt) / 1000);
        elapsed.textContent = seconds < 60
            ? `경과 시간 ${seconds}초`
            : `경과 시간 ${Math.floor(seconds / 60)}분 ${seconds % 60}초`;
    };
    updateElapsed();
    loading.hidden = false;
    const timer = setInterval(updateElapsed, 1000);
    try {
        const response = await fetch('/ads/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            const failure = await response.json().catch(() => null);
            const message = failure?.detail?.message;
            throw new Error(typeof message === 'string' ? message : response.status === 422
                ? '입력 형식이나 글자 수를 확인해주세요.'
                : `광고 생성에 실패했어요 (${response.status}). 잠시 후 다시 시도해주세요.`);
        }
        const ad = await response.json();
        if (![ad.headline, ad.body, ad.cta].every(value => typeof value === 'string') ||
            !Array.isArray(ad.hashtags) || !ad.hashtags.every(value => typeof value === 'string')) {
            throw new Error('광고 응답 형식이 올바르지 않아요.');
        }
        // 모델 응답을 HTML이 아닌 텍스트로 표시한다.
        for (const key of ['headline', 'body', 'cta', 'hashtags']) {
            document.getElementById(key).textContent = key === 'hashtags' ? ad[key].join(' ') : ad[key];
        }
        result.hidden = false;
        statusText.textContent = '광고 초안이 완성됐어요.';
    } catch (error) {
        statusText.textContent = '입력을 유지했어요. 확인 후 다시 시도해주세요.';
        errorText.textContent = error instanceof TypeError
            ? '서버에 연결하지 못했어요. FastAPI 실행 상태를 확인해주세요.' : error.message;
        errorText.hidden = false;
    } finally {
        clearInterval(timer);
        loading.hidden = true;
        button.disabled = false;
        button.textContent = '광고 생성하기';
        panel.setAttribute('aria-busy', 'false');
    }
});

// 항목별 복사 버튼
for (const copyButton of document.querySelectorAll('[data-copy]')) {
    copyButton.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(document.getElementById(copyButton.dataset.copy).textContent);
            statusText.textContent = '클립보드에 복사했어요.';
        } catch {
            statusText.textContent = '복사 권한을 확인하거나 문구를 직접 선택해서 복사해주세요.';
        }
    });
}
