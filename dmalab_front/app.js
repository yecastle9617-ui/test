// API 서버 주소 설정
// 로컬 개발: 'http://localhost:8000'
// 프로덕션: 빈 문자열 (상대 경로 사용, Nginx가 /api 경로를 프록시)
const API_BASE_URL = '';

// ===== 브라우저 고유 식별자 관리 =====
// localStorage에서 브라우저 고유 ID를 가져오거나 생성
function getOrCreateClientId() {
    const STORAGE_KEY = 'dmalab_client_id';
    let clientId = localStorage.getItem(STORAGE_KEY);
    
    if (!clientId) {
        // UUID v4 형식으로 생성 (간단한 버전)
        clientId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
        localStorage.setItem(STORAGE_KEY, clientId);
    }
    
    return clientId;
}

// 전역 변수로 클라이언트 ID 저장 (페이지 로드 시 한 번만 생성)
const CLIENT_ID = getOrCreateClientId();

// fetch 래퍼 함수: 모든 API 요청에 X-Client-ID 헤더 자동 추가
async function apiFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': CLIENT_ID,
        ...(options.headers || {})
    };
    
    return fetch(url, {
        ...options,
        headers: headers
    });
}

// iframe 높이 자동 조정 (부모 페이지에 높이 전달)
function sendHeightToParent() {
    if (window.parent !== window) {
        // iframe 내부에서 실행 중인 경우
        let height = Math.max(
            document.body.scrollHeight,
            document.body.offsetHeight,
            document.documentElement.clientHeight,
            document.documentElement.scrollHeight,
            document.documentElement.offsetHeight
        );
        
        // 모달이 표시되어 있을 때는 모달 높이도 포함
        const modal = document.querySelector('.autosave-modal');
        if (modal) {
            const modalRect = modal.getBoundingClientRect();
            const modalBottom = modalRect.bottom + window.scrollY;
            // 모달이 화면 하단을 벗어나지 않도록 높이 보정
            height = Math.max(height, modalBottom + 20); // 여유 공간 20px 추가
        }
        
        // 최소 높이 보장 (너무 작으면 안됨)
        height = Math.max(height, 600);
        
        // 디버깅용 로그 (개발 환경에서만)
        if (window.location.hostname === 'localhost' || window.location.hostname.includes('127.0.0.1')) {
            console.log('[iframe-height] 높이 전송:', height + 'px');
        }
        
        // postMessage로 부모에게 높이 전달
        try {
            window.parent.postMessage({
                type: 'iframe-height',
                height: height,
                source: 'dmalab'
            }, '*');
        } catch (e) {
            console.error('[iframe-height] postMessage 실패:', e);
        }
    }
}

// 초기 높이 전송
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(sendHeightToParent, 100);
    });
} else {
    setTimeout(sendHeightToParent, 100);
}

// 콘텐츠 변경 시 높이 재전송
let resizeObserver;
if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(function() {
        sendHeightToParent();
    });
    resizeObserver.observe(document.body);
}

// 주기적으로 높이 확인 (콘텐츠 동적 로드 대응)
setInterval(sendHeightToParent, 500);

// 부모 페이지에서 높이 요청을 받으면 즉시 전송
window.addEventListener('message', function(event) {
    // 보안: 부모 페이지에서만 메시지 수신
    if (event.data && event.data.type === 'request-height') {
        sendHeightToParent();
    }
});

// 네이버 블로그 카테고리 구조
const NAVER_CATEGORIES = {
    'entertainment': {
        name: '엔터테인먼트·예술',
        subCategories: [
            { value: 'literature', label: '문학·책' },
            { value: 'movie', label: '영화' },
            { value: 'art', label: '미술·디자인' },
            { value: 'performance', label: '공연·전시' },
            { value: 'music', label: '음악' },
            { value: 'drama', label: '드라마' },
            { value: 'celebrity', label: '스타·연예인' },
            { value: 'comic', label: '만화·애니' },
            { value: 'broadcast', label: '방송' }
        ]
    },
    'life': {
        name: '생활·노하우·쇼핑',
        subCategories: [
            { value: 'daily', label: '일상·생각' },
            { value: 'parenting', label: '육아·결혼' },
            { value: 'pet', label: '반려동물' },
            { value: 'quote', label: '좋은글·이미지' },
            { value: 'fashion', label: '패션·미용' },
            { value: 'interior', label: '인테리어·DIY' },
            { value: 'cooking', label: '요리·레시피' },
            { value: 'review', label: '상품리뷰' },
            { value: 'gardening', label: '원예·재배' }
        ]
    },
    'hobby': {
        name: '취미·여가·여행',
        subCategories: [
            { value: 'game', label: '게임' },
            { value: 'sports', label: '스포츠' },
            { value: 'photo', label: '사진' },
            { value: 'car', label: '자동차' },
            { value: 'hobby', label: '취미' },
            { value: 'travel-domestic', label: '국내여행' },
            { value: 'travel-world', label: '세계여행' },
            { value: 'restaurant', label: '맛집' }
        ]
    },
    'knowledge': {
        name: '지식·동향',
        subCategories: [
            { value: 'it', label: 'IT·컴퓨터' },
            { value: 'society', label: '사회·정치' },
            { value: 'health', label: '건강·의학' },
            { value: 'business', label: '비즈니스·경제' },
            { value: 'language', label: '어학·외국어' },
            { value: 'education', label: '교육·학문' }
        ]
    }
};

// ===== 외부 링크 UI 초기화 =====
function initExternalLinksUI() {
    const container = document.getElementById('external-links-container');
    const addBtn = document.getElementById('add-external-link-btn');
    const levelSelect = document.getElementById('generate-blog-level');

    if (!container || !addBtn || !levelSelect) return;

    // 외부 링크 행 추가
    function addExternalLinkRow(initialValue = '') {
        const row = document.createElement('div');
        row.className = 'external-link-row';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'external-link-input';
        input.placeholder = 'https://example.com/page';
        input.value = initialValue;

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn-link-remove';
        removeBtn.textContent = '삭제';

        removeBtn.addEventListener('click', () => {
            if (container.children.length > 1) {
                container.removeChild(row);
            } else {
                // 최소 1개 행은 유지하되 값만 비우기
                input.value = '';
            }
        });

        row.appendChild(input);
        row.appendChild(removeBtn);
        container.appendChild(row);
    }

    // 초기 1개 행 생성
    if (container.children.length === 0) {
        addExternalLinkRow();
    }

    // 레벨에 따라 활성/비활성
    function updateExternalLinksState() {
        const level = levelSelect.value;
        const isNew = level === 'new';

        const inputs = container.querySelectorAll('.external-link-input');
        inputs.forEach(input => {
            input.disabled = isNew;
            if (isNew) {
                input.value = '';
            }
        });

        addBtn.disabled = isNew;
    }

    levelSelect.addEventListener('change', updateExternalLinksState);
    addBtn.addEventListener('click', () => {
        addExternalLinkRow();
    });

    // 전역 헬퍼: 현재 UI에서 외부 링크 배열 추출
    window.getExternalLinksFromUI = function(blogLevel) {
        if (blogLevel === 'new') return null;
        const inputs = container.querySelectorAll('.external-link-input');
        const links = [];
        inputs.forEach(input => {
            const v = (input.value || '').trim();
            if (v) {
                links.push(v);
            }
        });
        return links.length > 0 ? links : null;
    };

    // 초기 상태 반영
    updateExternalLinksState();
}

// ===== 참고 블로그 URL UI 초기화 =====
function initReferenceBlogsUI() {
    const container = document.getElementById('reference-blogs-container');
    const addBtn = document.getElementById('add-reference-blog-btn');
    const autoCheckbox = document.getElementById('generate-use-auto-reference');
    const countInput = document.getElementById('generate-reference-count');

    if (!container || !addBtn || !autoCheckbox || !countInput) return;

    function addReferenceRow(initialValue = '') {
        const row = document.createElement('div');
        row.className = 'external-link-row';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'external-link-input';
        input.placeholder = 'https://blog.naver.com/...';
        input.value = initialValue;

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn-link-remove';
        removeBtn.textContent = '삭제';

        removeBtn.addEventListener('click', () => {
            if (container.children.length > 1) {
                container.removeChild(row);
            } else {
                input.value = '';
            }
        });

        row.appendChild(input);
        row.appendChild(removeBtn);
        container.appendChild(row);
    }

    if (container.children.length === 0) {
        addReferenceRow();
    }

    addBtn.addEventListener('click', () => addReferenceRow());

    function updateAutoReferenceState() {
        // 자동 수집 사용 여부에 따라 개수 입력만 활성/비활성
        countInput.disabled = !autoCheckbox.checked;
    }

    autoCheckbox.addEventListener('change', updateAutoReferenceState);
    updateAutoReferenceState();

    // 전역 헬퍼: 참고용 블로그 URL 배열 추출
    window.getReferenceBlogsFromUI = function() {
        const inputs = container.querySelectorAll('.external-link-input');
        const urls = [];
        inputs.forEach(input => {
            const v = (input.value || '').trim();
            if (v) {
                urls.push(v);
            }
        });
        return urls.length > 0 ? urls : null;
    };
}

// 대분류 변경 시 소분류 업데이트
function initCategorySelector() {
    const mainSelect = document.getElementById('generate-category-main');
    const subSelect = document.getElementById('generate-category-sub');
    
    if (!mainSelect || !subSelect) return;
    
    mainSelect.addEventListener('change', function() {
        const mainValue = this.value;
        const subSelect = document.getElementById('generate-category-sub');
        
        // 소분류 초기화
        subSelect.innerHTML = '<option value="">소분류를 선택하세요</option>';
        
        if (mainValue && NAVER_CATEGORIES[mainValue]) {
            // 소분류 활성화 및 옵션 추가
            subSelect.disabled = false;
            NAVER_CATEGORIES[mainValue].subCategories.forEach(sub => {
                const option = document.createElement('option');
                option.value = sub.value;
                option.textContent = sub.label;
                subSelect.appendChild(option);
            });
        } else {
            // 대분류가 선택되지 않으면 소분류 비활성화
            subSelect.disabled = true;
        }
    });
}

// 아이디어 생성 탭 UI 초기화
function initIdeasUI() {
    const topicInput = document.getElementById('ideas-topic');
    const autoTopicCheckbox = document.getElementById('ideas-auto-topic');
    
    if (!topicInput || !autoTopicCheckbox) return;
    
    // 체크박스 변경 시 입력 필드 활성/비활성 처리
    function updateTopicInputState() {
        const isAuto = autoTopicCheckbox.checked;
        topicInput.disabled = isAuto;
        if (isAuto) {
            topicInput.value = '';
        }
    }
    
    // 초기 상태 설정
    updateTopicInputState();
    
    // 체크박스 변경 이벤트 리스너
    autoTopicCheckbox.addEventListener('change', updateTopicInputState);
}

// 이미지 스타일 선택 UI 초기화
function initImageStyleUI() {
    const generateImagesCheckbox = document.getElementById('generate-images');
    const imageStyleGroup = document.getElementById('image-style-group');
    const imageStyleSelect = document.getElementById('image-style-select');
    
    if (!generateImagesCheckbox || !imageStyleGroup || !imageStyleSelect) return;
    
    // 체크박스 변경 시 이미지 스타일 선택 옵션 활성/비활성 처리
    function updateImageStyleState() {
        const isEnabled = generateImagesCheckbox.checked;
        if (imageStyleSelect) {
            imageStyleSelect.disabled = !isEnabled;
        }
    }
    
    // 초기 상태 설정
    updateImageStyleState();
    
    // 체크박스 변경 이벤트 리스너
    generateImagesCheckbox.addEventListener('change', updateImageStyleState);
}

// 페이지 로드 시 카테고리 선택기 초기화 및 탭 복원
// 스크립트가 body 끝에 있으므로 DOM이 이미 로드되어 있을 수 있음
(function() {
    function initPage() {
        // localStorage에서 저장된 탭 읽기
        const savedTab = localStorage.getItem('activeTab') || 'generate';
        
        // 모든 탭 버튼과 콘텐츠 비활성화
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // 저장된 탭 활성화
        const tabBtn = document.querySelector(`.tab-btn[data-tab="${savedTab}"]`);
        const tabContent = document.getElementById(`${savedTab}-tab`);
        
        if (tabBtn && tabContent) {
            tabBtn.classList.add('active');
            tabContent.classList.add('active');
        } else {
            // 저장된 탭이 없거나 유효하지 않으면 기본값 사용
            const defaultTabBtn = document.querySelector('.tab-btn[data-tab="generate"]');
            const defaultTabContent = document.getElementById('generate-tab');
            if (defaultTabBtn) defaultTabBtn.classList.add('active');
            if (defaultTabContent) defaultTabContent.classList.add('active');
        }
        
        initCategorySelector();
        initExternalLinksUI();
        initReferenceBlogsUI();
        initIdeasUI();
        initImageStyleUI();
        // 에디터 초기화
        initializeQuillEditors();
        
        // 활성화된 탭에 맞게 에디터 표시/숨김 처리
        const activeTabBtn = document.querySelector('.tab-btn.active');
        const activeTab = activeTabBtn ? activeTabBtn.dataset.tab : 'generate';
        const resultDiv = document.getElementById('result');
        if (resultDiv) {
            if (activeTab === 'process') {
                resultDiv.style.display = 'none';
            } else if (activeTab === 'generate') {
                resultDiv.style.display = 'block';
            }
        }
        // 임시 저장된 내용이 있으면 복원 여부를 사용자에게 물어봄
        // AI 블로그 생성 탭에서만 표시
        if (activeTab === 'generate') {
            // async 함수이므로 await 없이 호출 (백그라운드에서 실행)
            showRestoreDraftModalIfNeeded();
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPage);
    } else {
        // DOM이 이미 로드된 경우 즉시 실행
        setTimeout(initPage, 100); // 약간의 지연으로 DOM이 완전히 준비되도록
    }
})();

// 사용량 정보 조회 및 업데이트
async function updateUsageInfo() {
    try {
        const response = await apiFetch(`${API_BASE_URL}/api/usage`);
        if (!response.ok) {
            throw new Error('사용량 조회 실패');
        }
        const usage = await response.json();
        
        // 상위 블로그 분석 탭
        const processUsageText = document.getElementById('process-usage-text');
        if (processUsageText) {
            if (usage.is_admin) {
                processUsageText.textContent = '🔓 Admin: 무제한 사용 가능';
                processUsageText.style.color = '#28a745';
            } else {
                const ref = usage.reference_analysis;
                const remaining = ref.remaining;
                const color = remaining === 0 ? '#dc3545' : remaining <= 1 ? '#ff9800' : '#666';
                processUsageText.textContent = `상위 블로그 분석: ${ref.used}/${ref.limit}회 사용 (남은 횟수: ${remaining}회)`;
                processUsageText.style.color = color;
            }
        }
        
        // AI 블로그 생성 탭 (버튼 클릭 1회 = 1회로 계산)
        const generateUsageText = document.getElementById('generate-usage-text');
        if (generateUsageText) {
            if (usage.is_admin) {
                generateUsageText.innerHTML = '🔓 Admin: 무제한 사용 가능';
                generateUsageText.style.color = '#28a745';
            } else {
                const blog = usage.blog_generation;
                const blogRemaining = blog.remaining;
                const blogColor = blogRemaining === 0 ? '#dc3545' : blogRemaining <= 1 ? '#ff9800' : '#666';
                
                generateUsageText.innerHTML = `
                    블로그 생성: <span style="color: ${blogColor}">${blog.used}/${blog.limit}회</span> (남은 횟수: ${blogRemaining}회)
                `;
            }
        }
        
        // AI 블로그 아이디어 생성 탭
        const ideasUsageText = document.getElementById('ideas-usage-text');
        if (ideasUsageText) {
            if (usage.is_admin) {
                ideasUsageText.textContent = '🔓 Admin: 무제한 사용 가능';
                ideasUsageText.style.color = '#28a745';
            } else {
                const ideas = usage.blog_ideas || usage.blog_generation; // 하위 호환성
                const remaining = ideas.remaining;
                const color = remaining === 0 ? '#dc3545' : remaining <= 1 ? '#ff9800' : '#666';
                ideasUsageText.textContent = `블로그 아이디어 생성: ${ideas.used}/${ideas.limit}회 사용 (남은 횟수: ${remaining}회)`;
                ideasUsageText.style.color = color;
            }
        }
    } catch (error) {
        console.error('사용량 조회 오류:', error);
        // 오류 시 기본 메시지 표시
        const usageTexts = ['process-usage-text', 'generate-usage-text', 'ideas-usage-text'];
        usageTexts.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.textContent = '사용량 조회 실패';
                elem.style.color = '#999';
            }
        });
    }
}

// 페이지 로드 시 및 주기적으로 사용량 업데이트
(function() {
    // 초기 로드 시 사용량 조회
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            updateUsageInfo();
            // 30초마다 사용량 업데이트
            setInterval(updateUsageInfo, 30000);
        });
    } else {
        updateUsageInfo();
        setInterval(updateUsageInfo, 30000);
    }
})();

// 이미지 URL을 프록시를 통해 로드하는 헬퍼 함수
function getProxyImageUrl(imageUrl, outputDir = null) {
    if (!imageUrl) return '';
    
    // 이미 프록시 URL이거나 저장된 경로인 경우
    if (imageUrl.startsWith('/api/image-proxy') || imageUrl.startsWith('/static/')) {
        return `${API_BASE_URL}${imageUrl}`;
    }
    
    // URL 인코딩
    const encodedUrl = encodeURIComponent(imageUrl);
    let proxyUrl = `${API_BASE_URL}/api/image-proxy?url=${encodedUrl}`;
    
    // output_dir이 있으면 추가
    if (outputDir) {
        proxyUrl += `&output_dir=${encodeURIComponent(outputDir)}`;
    }
    
    return proxyUrl;
}

// 탭 전환
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // localStorage에 현재 탭 저장
        localStorage.setItem('activeTab', tabName);
        
        // 모든 탭 버튼과 콘텐츠 비활성화
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // 선택한 탭 활성화
        btn.classList.add('active');
        const activeContent = document.getElementById(`${tabName}-tab`);
        if (activeContent) {
            activeContent.classList.add('active');
        }

        // 탭 전환 시 모든 탭의 로딩 상태 초기화
        const loadingDivs = ['process-loading', 'generate-loading', 'ideas-loading'];
        loadingDivs.forEach(id => {
            const loadingDiv = document.getElementById(id);
            if (loadingDiv) {
                loadingDiv.style.display = 'none';
            }
        });

        // 탭에 따라 결과 영역 표시/숨김 제어
        const resultDiv = document.getElementById('result');          // 블로그 에디터 영역
        const resultContent = document.getElementById('result-content'); // 상위 블로그 분석 결과 영역
        const ideasResult = document.getElementById('ideas-result');  // 아이디어 결과 영역

        if (tabName === 'process') {
            // 상위 블로그 분석 탭: result-content만 표시 (전체 처리 결과)
            if (resultDiv) {
                resultDiv.style.display = 'block';
                // 에디터 영역 숨김
                const blogEditorSections = resultDiv.querySelector('.blog-editor-sections');
                if (blogEditorSections) blogEditorSections.style.display = 'none';
                const resultHeader = resultDiv.querySelector('.result-header');
                if (resultHeader) resultHeader.style.display = 'none';
            }
            // result-content 표시 (기존 결과 유지)
            if (resultContent) {
                resultContent.style.display = 'block';
            }
            if (ideasResult) ideasResult.style.display = 'none';
        } else if (tabName === 'ideas') {
            // 아이디어 탭: 아이디어 결과만 표시 (프롬프트 결과)
            if (resultDiv) resultDiv.style.display = 'none';
            // result-content 숨김 (결과는 삭제하지 않음)
            if (resultContent) {
                resultContent.style.display = 'none';
            }
            // ideas-result 표시 (내용이 있으면)
            if (ideasResult) {
                const ideasResultContent = document.getElementById('ideas-result-content');
                // 전역 변수에 저장된 결과 데이터가 있으면 복원
                if (window.currentIdeasResult) {
                    renderIdeasResult(window.currentIdeasResult);
                    ideasResult.style.display = 'block';
                } else if (ideasResultContent && ideasResultContent.innerHTML.trim()) {
                    ideasResult.style.display = 'block';
                } else {
                    ideasResult.style.display = 'none';
                }
            }
        } else if (tabName === 'generate') {
            // 블로그 생성 탭: 에디터만 표시 (result-content 숨김)
            if (resultDiv) {
                resultDiv.style.display = 'block';
                // 에디터 영역 표시
                const blogEditorSections = resultDiv.querySelector('.blog-editor-sections');
                if (blogEditorSections) blogEditorSections.style.display = 'block';
                const resultHeader = resultDiv.querySelector('.result-header');
                if (resultHeader) resultHeader.style.display = 'flex';
            }
            // result-content 숨김 (결과는 삭제하지 않음)
            if (resultContent) {
                resultContent.style.display = 'none';
            }
            if (ideasResult) ideasResult.style.display = 'none';
        }
    });
});

// 로딩 표시 (현재 활성 탭의 로딩 요소 사용)
function showLoading(message = '처리 중...') {
    const activeTabBtn = document.querySelector('.tab-btn.active');
    const activeTab = activeTabBtn ? activeTabBtn.dataset.tab : null;
    
    // 탭별 로딩 요소 ID 매핑
    const loadingIds = {
        'process': { div: 'process-loading', message: 'process-loading-message', steps: 'process-loading-steps' },
        'generate': { div: 'generate-loading', message: 'generate-loading-message', steps: 'generate-loading-steps' },
        'ideas': { div: 'ideas-loading', message: 'ideas-loading-message', steps: 'ideas-loading-steps' }
    };
    
    const loadingId = activeTab && loadingIds[activeTab] ? loadingIds[activeTab] : null;
    
    if (loadingId) {
        const loadingDiv = document.getElementById(loadingId.div);
        const loadingMessage = document.getElementById(loadingId.message);
        const loadingSteps = document.getElementById(loadingId.steps);
        
        if (loadingDiv) {
            loadingDiv.style.display = 'block';
            if (loadingMessage) {
                loadingMessage.textContent = message;
            }
            if (loadingSteps) {
                loadingSteps.innerHTML = '';
            }
        }
    }
    
    const errorDiv = document.getElementById('error');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

function updateLoadingStep(step, status = 'pending') {
    // status: 'pending', 'processing', 'completed', 'error'
    const activeTabBtn = document.querySelector('.tab-btn.active');
    const activeTab = activeTabBtn ? activeTabBtn.dataset.tab : null;
    
    // 탭별 로딩 스텝 요소 ID 매핑
    const loadingStepsIds = {
        'process': 'process-loading-steps',
        'generate': 'generate-loading-steps',
        'ideas': 'ideas-loading-steps'
    };
    
    const stepsId = activeTab && loadingStepsIds[activeTab] ? loadingStepsIds[activeTab] : null;
    const loadingSteps = stepsId ? document.getElementById(stepsId) : null;
    
    if (!loadingSteps) return;
    
    const stepId = `step-${step.replace(/\s+/g, '-').toLowerCase()}`;
    let stepElement = document.getElementById(stepId);
    
    if (!stepElement) {
        stepElement = document.createElement('div');
        stepElement.id = stepId;
        stepElement.className = 'loading-step';
        loadingSteps.appendChild(stepElement);
    }
    
    const icons = {
        'pending': '⏳',
        'processing': '🔄',
        'completed': '✅',
        'error': '❌'
    };
    
    const colors = {
        'pending': '#999',
        'processing': '#667eea',
        'completed': '#28a745',
        'error': '#dc3545'
    };
    
    stepElement.innerHTML = `
        <span class="step-icon">${icons[status] || icons.pending}</span>
        <span class="step-text" style="color: ${colors[status] || colors.pending}">${step}</span>
    `;
    
    stepElement.className = `loading-step step-${status}`;
}

function hideLoading() {
    // 모든 탭의 로딩 요소 숨기기
    const loadingDivs = ['process-loading', 'generate-loading', 'ideas-loading'];
    loadingDivs.forEach(id => {
        const loadingDiv = document.getElementById(id);
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    });
    
    // 로딩이 끝나면 현재 탭에 맞게 결과 영역 표시/숨김
    const activeTabBtn = document.querySelector('.tab-btn.active');
    const activeTab = activeTabBtn ? activeTabBtn.dataset.tab : null;
    const resultDiv = document.getElementById('result');
    const resultContent = document.getElementById('result-content');
    const ideasResult = document.getElementById('ideas-result');

    if (activeTab === 'process') {
        // 상위 블로그 분석 탭: result-content만 표시 (에디터 숨김)
        if (resultDiv) resultDiv.style.display = 'block';
        // 에디터 영역 숨김
        const blogEditorSections = resultDiv?.querySelector('.blog-editor-sections');
        if (blogEditorSections) blogEditorSections.style.display = 'none';
        const resultHeader = resultDiv?.querySelector('.result-header');
        if (resultHeader) resultHeader.style.display = 'none';
        // result-content 표시 (기존 결과 유지)
        if (resultContent) {
            resultContent.style.display = 'block';
        }
        if (ideasResult) ideasResult.style.display = 'none';
    } else if (activeTab === 'ideas') {
        // 아이디어 탭: 아이디어 결과만 표시 (에디터 숨김)
        if (resultDiv) resultDiv.style.display = 'none';
        // result-content 숨김 (결과는 삭제하지 않음)
        if (resultContent) {
            resultContent.style.display = 'none';
        }
        // ideas-result 표시 (내용이 있으면)
        if (ideasResult) {
            const ideasResultContent = document.getElementById('ideas-result-content');
            // 전역 변수에 저장된 결과 데이터가 있으면 복원
            if (window.currentIdeasResult) {
                renderIdeasResult(window.currentIdeasResult);
                ideasResult.style.display = 'block';
            } else if (ideasResultContent && ideasResultContent.innerHTML.trim()) {
                ideasResult.style.display = 'block';
            } else {
                ideasResult.style.display = 'none';
            }
        }
    } else if (activeTab === 'generate') {
        // 블로그 생성 탭: 에디터만 표시 (result-content 숨김)
        if (resultDiv) resultDiv.style.display = 'block';
        // result-content 숨김 (결과는 삭제하지 않음)
        if (resultContent) {
            resultContent.style.display = 'none';
        }
        if (ideasResult) ideasResult.style.display = 'none';
        // 에디터 영역 표시
        const blogEditorSections = resultDiv?.querySelector('.blog-editor-sections');
        if (blogEditorSections) blogEditorSections.style.display = 'block';
        const resultHeader = resultDiv?.querySelector('.result-header');
        if (resultHeader) resultHeader.style.display = 'flex';
    }
}

// 에러 표시
function showError(message) {
    document.getElementById('error').style.display = 'block';
    document.getElementById('error').textContent = '오류: ' + message;
}

// GPT가 생성한 이미지 플레이스홀더 텍스트 정규화
// 예: "[아임웹 디자인 편집 화면_이미지 삽입1]" -> "[아임웹 디자인 편집 화면]"
function normalizeImagePlaceholderText(placeholder) {
    if (!placeholder) return '[이미지 삽입]';
    return placeholder.replace(/(_이미지 삽입\d*)(?=\])/g, '');
}

// 결과 표시
function showResult(data, type = 'default') {
    const resultDiv = document.getElementById('result');
    const resultContent = document.getElementById('result-content');
    
    // 결과를 표시할 때는 항상 에디터 영역을 보이도록 설정
    if (resultDiv) {
        resultDiv.style.display = 'block';
    }
    
    // 타입에 따라 다른 렌더링
    switch (type) {
        case 'process': {
            // 상위 블로그 분석 결과 표시 - result-content만 표시
            if (resultDiv) {
                resultDiv.style.display = 'block';
                // 에디터 영역은 숨김
                const blogEditorSections = resultDiv.querySelector('.blog-editor-sections');
                if (blogEditorSections) {
                    blogEditorSections.style.display = 'none';
                }
                const resultHeader = resultDiv.querySelector('.result-header');
                if (resultHeader) {
                    resultHeader.style.display = 'none';
                }
            }
            if (resultContent) {
                resultContent.innerHTML = renderProcessResult(data);
                resultContent.style.display = 'block';
            }
            // 다른 결과 영역 숨김
            const ideasResult = document.getElementById('ideas-result');
            if (ideasResult) ideasResult.style.display = 'none';
            break;
        }
        case 'generate': {
            // 블로그 생성 결과 표시 - 에디터만 표시
            if (resultDiv) {
                resultDiv.style.display = 'block';
                // result-content 영역은 숨김
                if (resultContent) {
                    resultContent.innerHTML = '';
                    resultContent.style.display = 'none';
                }
                // 에디터 영역 표시
                const blogEditorSections = resultDiv.querySelector('.blog-editor-sections');
                if (blogEditorSections) {
                    blogEditorSections.style.display = 'block';
                }
                const resultHeader = resultDiv.querySelector('.result-header');
                if (resultHeader) {
                    resultHeader.style.display = 'flex';
                }
            }
            // 다른 결과 영역 숨김
            const ideasResult = document.getElementById('ideas-result');
            if (ideasResult) ideasResult.style.display = 'none';
            // 제목, 본문, 태그로 분리된 에디터에 렌더링
            const content = data.blog_content || data;
            renderBlogContentSeparated(content);
            // 현재 블로그 콘텐츠 저장 (복사 기능용)
            window.currentBlogContent = content;
            
            // 이미지 다운로드 버튼 활성화/비활성화 (에디터 렌더링 후 실행)
            setTimeout(() => {
                const downloadImagesBtn = document.getElementById('download-images-btn');
                if (downloadImagesBtn) {
                    const hasImages = content.generated_images && content.generated_images.length > 0;
                    console.log('[이미지 다운로드 버튼]', {
                        hasImages,
                        generated_images: content.generated_images,
                        button: downloadImagesBtn
                    });
                    // 버튼은 항상 표시하되, 이미지가 없으면 비활성화
                    downloadImagesBtn.disabled = !hasImages;
                    downloadImagesBtn.style.display = 'inline-block';
                    if (!hasImages) {
                        downloadImagesBtn.title = '생성된 이미지가 없습니다';
                    } else {
                        downloadImagesBtn.title = '';
                    }
                } else {
                    console.warn('[이미지 다운로드 버튼] 버튼을 찾을 수 없음');
                }
            }, 300);
            break;
        }
        default: {
            // JSON 표시는 pre 태그 사용
            if (resultContent) {
                resultContent.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            }
            break;
        }
    }
}

// 전체 처리 결과 렌더링
function renderProcessResult(data) {
    let html = `<div class="result-header">
        <h3>전체 처리 결과</h3>
        <p class="result-summary">
            키워드: <strong>${data.keyword}</strong> | 
            전체: <strong>${data.total_count}개</strong> | 
            성공: <strong>${data.success_count}개</strong> | 
            실패: <strong>${data.total_count - data.success_count}개</strong>
        </p>
    </div>`;
    
    if (data.results && data.results.length > 0) {
        html += '<div class="process-results-list">';
        data.results.forEach((result, index) => {
            const cardId = `process-card-${result.rank}`;
            html += `
                <div class="process-result-card ${result.success ? 'success' : 'error'}">
                    <div class="result-card-header" onclick="toggleProcessCard('${cardId}')" style="cursor: pointer; user-select: none;">
                        <span class="result-rank">TOP ${result.rank}</span>
                        <span class="result-status-badge ${result.success ? 'success' : 'error'}">
                            ${result.success ? '✅ 성공' : '❌ 실패'}
                        </span>
                        <span class="card-toggle-icon" id="${cardId}-icon">▼</span>
                    </div>
                    <div class="result-card-body" id="${cardId}" style="display: none;">
                        <!-- 1. 링크 -->
                        <div class="result-field">
                            <strong class="field-label">링크:</strong>
                            <a href="${result.url}" target="_blank" class="result-link">${escapeHtml(result.url)}</a>
                        </div>
                        
                        <!-- 2. 제목 -->
                        <div class="result-field">
                            <strong class="field-label">제목:</strong>
                            <h4 class="result-title">${escapeHtml(result.title)}</h4>
                        </div>
                        
                        <!-- 3. 키워드 -->
                        ${result.keywords && result.keywords.length > 0 ? `
                            <div class="result-field">
                                <strong class="field-label">키워드:</strong>
                                <div class="keyword-tags">
                                    ${result.keywords.slice(0, 20).map(k => `<span class="keyword-tag">${escapeHtml(k.keyword)} (${k.count})</span>`).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        <!-- 4. 본문 글자수 -->
                        ${result.body_length ? `
                            <div class="result-field">
                                <strong class="field-label">본문 글자수:</strong>
                                <span class="body-length">${result.body_length.toLocaleString()}자</span>
                            </div>
                        ` : ''}
                        
                        <!-- 5. 본문 (이미지/링크 포함) -->
                        ${result.body_text && result.body_text.trim() ? `
                            <div class="result-field body-text-field">
                                <strong class="field-label">본문:</strong>
                                ${formatProcessBodyText(
                                    String(result.body_text).trim(),
                                    result.image_urls || [],
                                    result.link_urls || [],
                                    data.output_dir ? `${data.output_dir}/TOP${result.rank}` : null
                                )}
                            </div>
                        ` : ''}
                        
                        ${result.error ? `<p class="error-text"><strong>오류:</strong> ${escapeHtml(result.error)}</p>` : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    return html;
}

// 프로세스 결과 카드 토글 함수
function toggleProcessCard(cardId) {
    const cardBody = document.getElementById(cardId);
    const icon = document.getElementById(`${cardId}-icon`);
    if (cardBody && icon) {
        if (cardBody.style.display === 'none') {
            cardBody.style.display = 'block';
            icon.textContent = '▲';
        } else {
            cardBody.style.display = 'none';
            icon.textContent = '▼';
        }
    }
}

// 유틸리티 함수들
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatText(text) {
    if (!text) {
        console.log('formatText: text가 없습니다');
        return '';
    }
    
    // HTML 이스케이프 먼저 수행
    let escaped = escapeHtml(text);
    
    // 마커를 하이라이트 (숫자가 포함된 경우도 처리)
    // [이미지 삽입], [이미지 삽입1], [이미지 삽입2] 등 모두 매칭
    escaped = escaped.replace(/\[이미지 삽입\d*\]/g, '<span class="media-marker image-marker">$&</span>');
    escaped = escaped.replace(/\[링크 삽입\d*\]/g, '<span class="media-marker link-marker">$&</span>');
    escaped = escaped.replace(/\[이모티콘 삽입\d*\]/g, '<span class="media-marker emoji-marker">$&</span>');
    
    // 줄바꿈 처리
    const formatted = escaped.replace(/\n/g, '<br>');
    
    return formatted;
}

// 상위 블로그 분석용 본문 포맷팅 (이미지/링크를 실제로 표시)
function formatProcessBodyText(text, imageUrls, linkUrls, outputDir) {
    if (!text) {
        return '<div class="body-text">본문이 없습니다.</div>';
    }
    
    // 이미지와 링크 HTML을 먼저 생성
    const imageHtmls = [];
    const linkHtmls = [];
    
    // 이미지 HTML 생성
    imageUrls.forEach((imgUrl, idx) => {
        const proxyUrl = getProxyImageUrl(imgUrl, outputDir);
        const originalUrl = imgUrl.startsWith('/') ? imgUrl : imgUrl.split('?url=')[1] ? decodeURIComponent(imgUrl.split('?url=')[1].split('&')[0]) : imgUrl;
        imageHtmls.push(`<div class="process-body-image" style="margin: 15px 0; text-align: center;"><img src="${proxyUrl}" alt="이미지 ${idx + 1}" style="width: 400px; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" loading="lazy" data-original-url="${escapeHtml(originalUrl)}" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"><div class="image-error" style="display: none; padding: 10px; background: #ffecec; border-radius: 4px; margin-top: 5px;">이미지를 불러올 수 없습니다<br><small><a href="${originalUrl}" target="_blank">${escapeHtml(originalUrl)}</a></small></div></div>`);
    });
    
    // 링크 HTML 생성
    linkUrls.forEach((linkUrl) => {
        linkHtmls.push(`<a href="${linkUrl}" target="_blank" style="color: #3BB1E2; text-decoration: underline;">${escapeHtml(linkUrl)}</a>`);
    });
    
    // 마커를 임시 플레이스홀더로 교체 (이스케이프 전에 처리)
    let formatted = text;
    const placeholders = [];
    
    // 이미지 마커를 플레이스홀더로 교체
    let imageIndex = 0;
    formatted = formatted.replace(/\[이미지 삽입\d*\]/g, (match) => {
        if (imageIndex < imageHtmls.length) {
            const placeholder = `__IMAGE_PLACEHOLDER_${imageIndex}__`;
            placeholders.push({ placeholder, html: imageHtmls[imageIndex] });
            imageIndex++;
            return placeholder;
        }
        return match; // 이미지가 없으면 마커 그대로 유지
    });
    
    // 링크 마커를 플레이스홀더로 교체
    let linkIndex = 0;
    formatted = formatted.replace(/\[링크 삽입\d*\]/g, (match) => {
        if (linkIndex < linkHtmls.length) {
            const placeholder = `__LINK_PLACEHOLDER_${linkIndex}__`;
            placeholders.push({ placeholder, html: linkHtmls[linkIndex] });
            linkIndex++;
            return placeholder;
        }
        return match; // 링크가 없으면 마커 그대로 유지
    });
    
    // 이제 텍스트를 이스케이프
    formatted = escapeHtml(formatted);
    
    // 플레이스홀더를 실제 HTML로 교체
    placeholders.forEach(({ placeholder, html }) => {
        formatted = formatted.replace(escapeHtml(placeholder), html);
    });
    
    // 이모티콘 마커는 그대로 유지 (하이라이트만)
    formatted = formatted.replace(/\[이모티콘 삽입\d*\]/g, '<span class="media-marker emoji-marker">$&</span>');
    
    // 줄바꿈 처리
    formatted = formatted.replace(/\n/g, '<br>');
    
    // 이미지/링크 갯수 표시
    const imageCount = imageUrls.length;
    const linkCount = linkUrls.length;
    let countInfo = '';
    if (imageCount > 0 || linkCount > 0) {
        countInfo = '<div style="margin-bottom: 15px; padding: 10px; background: #f5f5f5; border-radius: 4px; font-size: 0.9rem; color: #666;">';
        if (imageCount > 0) {
            countInfo += `<strong>이미지:</strong> ${imageCount}개 `;
        }
        if (linkCount > 0) {
            if (imageCount > 0) countInfo += '| ';
            countInfo += `<strong>링크:</strong> ${linkCount}개`;
        }
        countInfo += '</div>';
    }
    
    return `
        ${countInfo}
        <div class="body-text">${formatted}</div>
    `;
}

// 전체 처리
async function handleProcess() {
    const keyword = document.getElementById('process-keyword').value.trim();
    const count = parseInt(document.getElementById('process-count').value) || 3;
    const analyze = document.getElementById('process-analyze').checked;
    const topN = parseInt(document.getElementById('process-topn').value) || 20;
    const minLength = parseInt(document.getElementById('process-minlength').value) || 2;
    const minCount = parseInt(document.getElementById('process-mincount').value) || 2;

    if (!keyword) {
        alert('검색 키워드를 입력하세요.');
        return;
    }
    
    // 블로그 개수 제한 확인
    if (count > 3) {
        alert('무료버전은 최대 3개까지만 처리할 수 있습니다.');
        document.getElementById('process-count').value = '3';
        return;
    }

    // 결과 영역 표시 및 로딩 메시지 표시
    const resultDiv = document.getElementById('result');
    const resultContent = document.getElementById('result-content');
    
    // process-loading은 사용하지 않음 (resultContent에 진행률 바가 표시됨)
    
    if (resultDiv) {
        resultDiv.style.display = 'block';
        // 에디터 영역은 숨김
        const blogEditorSections = resultDiv.querySelector('.blog-editor-sections');
        if (blogEditorSections) {
            blogEditorSections.style.display = 'none';
        }
        const resultHeader = resultDiv.querySelector('.result-header');
        if (resultHeader) {
            resultHeader.style.display = 'none';
        }
    }
    if (resultContent) {
        resultContent.style.display = 'block';
        resultContent.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; min-height: 300px; flex-direction: column; gap: 20px;">
                <div class="spinner" style="border-top-color: #3BB1E2;"></div>
                <p id="process-loading-text" style="font-size: 1.1rem; color: #666; font-weight: 500; margin-bottom: 10px;">상위 블로그를 분석 중입니다...</p>
                <div style="width: 300px; background: #e0e0e0; border-radius: 10px; overflow: hidden; height: 8px;">
                    <div id="process-progress-bar" style="width: 1%; height: 100%; background: linear-gradient(90deg, #3BB1E2, #667eea); transition: width 0.3s ease; border-radius: 10px;"></div>
                </div>
                <p id="process-progress-text" style="font-size: 0.9rem; color: #999; margin-top: 5px;">1%</p>
            </div>
        `;
    }

    // 진행률 업데이트 함수
    function updateProcessProgress(current, total, label) {
        const percentage = Math.min(Math.max((current / total) * 100, 1), 100); // 최소 1%, 최대 100%
        const progressBar = document.getElementById('process-progress-bar');
        const progressText = document.getElementById('process-progress-text');
        const loadingText = document.getElementById('process-loading-text');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
        if (progressText) {
            progressText.textContent = `${Math.round(percentage)}%`;
        }
        if (loadingText && label) {
            loadingText.textContent = label;
        }
    }
    
    // 진행률 관련 변수 (함수 스코프 밖에서 접근 가능하도록)
    let searchProgressInterval = null;
    let crawlProgressInterval = null;
    let currentProgressValue = 0; // 현재 진행률 값 추적
    
    // 초기 진행률 표시 (1%)
    currentProgressValue = 1;
    updateProcessProgress(0, count, `상위 블로그를 분석 중입니다... (0/${count})`);
    
    // 진행률 시뮬레이션 (블로그 검색 단계: 1% ~ 20%)
    let searchProgress = 1;
    searchProgressInterval = setInterval(() => {
        searchProgress += 0.3;
        if (searchProgress <= 20) {
            const progressPercent = (searchProgress / 20) * 0.2; // 0~20% 범위를 0~0.2로 매핑
            const currentBlogs = Math.floor(progressPercent * count);
            currentProgressValue = progressPercent * count;
            updateProcessProgress(currentProgressValue, count, `블로그 검색 중... (${currentBlogs}/${count})`);
        } else {
            clearInterval(searchProgressInterval);
            searchProgressInterval = null;
            currentProgressValue = count * 0.2; // 20% 완료
        }
        }, 100);

    try {
        const response = await apiFetch(`${API_BASE_URL}/api/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: keyword,
                n: count,
                analyze: analyze,
                top_n: topN,
                min_length: minLength,
                min_count: minCount
            })
        });
        
        // 블로그 크롤링 진행률 시뮬레이션 (20% ~ 95%)
        if (searchProgressInterval) {
            clearInterval(searchProgressInterval);
            searchProgressInterval = null;
        }
        
        // 현재 진행률에서 시작 (20% = count * 0.2)
        const startProgress = currentProgressValue;
        const targetProgress = count * 0.95; // 95%까지 시뮬레이션
        const progressRange = targetProgress - startProgress;
        const steps = 50; // 50단계로 나누어 부드럽게 진행
        const stepIncrement = progressRange / steps;
        let crawlStep = 0;
        
        crawlProgressInterval = setInterval(() => {
            crawlStep++;
            const newProgress = Math.min(startProgress + (stepIncrement * crawlStep), targetProgress);
            currentProgressValue = newProgress;
            const completedBlogs = Math.floor(newProgress);
            const remainingBlogs = count - completedBlogs;
            
            if (newProgress < targetProgress) {
                updateProcessProgress(newProgress, count, `블로그 크롤링 중... (${completedBlogs}/${count})`);
            } else {
                clearInterval(crawlProgressInterval);
                crawlProgressInterval = null;
                currentProgressValue = targetProgress;
                updateProcessProgress(targetProgress, count, `블로그 크롤링 중... (${completedBlogs}/${count})`);
            }
        }, 150);

        // 응답이 JSON인지 확인
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`서버 응답 오류: ${text.substring(0, 100)}`);
        }

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '처리 실패');
        }
        
        // 크롤링 완료 후 진행률을 부드럽게 100%로 증가
        if (crawlProgressInterval) {
            clearInterval(crawlProgressInterval);
            crawlProgressInterval = null;
        }
        
        // 현재 진행률에서 100%까지 부드럽게 증가
        const finalStartProgress = currentProgressValue;
        const finalTargetProgress = count;
        const finalProgressRange = finalTargetProgress - finalStartProgress;
        const finalSteps = 20;
        const finalStepIncrement = finalProgressRange / finalSteps;
        let finalStep = 0;
        
        const finalProgressInterval = setInterval(() => {
            finalStep++;
            const newProgress = Math.min(finalStartProgress + (finalStepIncrement * finalStep), finalTargetProgress);
            currentProgressValue = newProgress;
            updateProcessProgress(newProgress, count, `블로그 크롤링 완료 (${count}/${count})`);
            
            if (finalStep >= finalSteps || newProgress >= finalTargetProgress) {
                clearInterval(finalProgressInterval);
                currentProgressValue = finalTargetProgress;
                updateProcessProgress(finalTargetProgress, count, `블로그 크롤링 완료 (${count}/${count})`);
            }
        }, 50);
        
        if (analyze) {
            // 키워드 분석 중에도 진행률은 100% 유지
            setTimeout(() => {
                setTimeout(() => {
                    showResult(data, 'process');
                }, 500);
            }, 500);
        } else {
            setTimeout(() => {
                showResult(data, 'process');
                // 사용량 업데이트
                updateUsageInfo();
            }, 500);
        }
    } catch (error) {
        // 에러 발생 시 진행률 바 제거
        const resultContent = document.getElementById('result-content');
        if (resultContent) {
            resultContent.innerHTML = '';
        }
        showError(error.message);
    }
}

// GPT 블로그 생성
async function handleGenerateBlog() {
    const keywords = document.getElementById('generate-keywords').value.trim();
    const mainCategory = document.getElementById('generate-category-main').value;
    const subCategory = document.getElementById('generate-category-sub').value;
    const blogLevel = document.getElementById('generate-blog-level').value;
    const banWords = document.getElementById('generate-ban-words').value.trim();

    // 유효성 검증
    if (!keywords) {
        alert('키워드를 입력하세요.');
        document.getElementById('generate-keywords').focus();
        return;
    }

    if (keywords.length > 100) {
        alert('키워드는 100자 이하여야 합니다.');
        document.getElementById('generate-keywords').focus();
        return;
    }

    // 카테고리 검증
    if (!mainCategory) {
        alert('대분류를 선택하세요.');
        document.getElementById('generate-category-main').focus();
        return;
    }
    
    if (!subCategory) {
        alert('소분류를 선택하세요.');
        document.getElementById('generate-category-sub').focus();
        return;
    }
    
    // 카테고리 값 검증
    if (!NAVER_CATEGORIES[mainCategory]) {
        alert('올바른 대분류를 선택하세요.');
        document.getElementById('generate-category-main').focus();
        return;
    }
    
    const validSubCategories = NAVER_CATEGORIES[mainCategory].subCategories.map(sc => sc.value);
    if (!validSubCategories.includes(subCategory)) {
        alert('올바른 소분류를 선택하세요.');
        document.getElementById('generate-category-sub').focus();
        return;
    }
    
    // 카테고리 전체 이름 구성 (예: "엔터테인먼트·예술 > IT·컴퓨터")
    const mainCategoryName = NAVER_CATEGORIES[mainCategory].name;
    const subCategoryName = NAVER_CATEGORIES[mainCategory].subCategories.find(sc => sc.value === subCategory).label;
    const category = `${mainCategoryName} > ${subCategoryName}`;

    // 블로그 레벨 검증
    const validLevels = ['new', 'mid', 'high'];
    if (!validLevels.includes(blogLevel)) {
        alert('올바른 블로그 레벨을 선택하세요.');
        document.getElementById('generate-blog-level').focus();
        return;
    }

    // 금칙어 검증
    if (banWords && banWords.length > 200) {
        alert('금칙어는 총 200자 이하여야 합니다.');
        document.getElementById('generate-ban-words').focus();
        return;
    }

    // 외부 링크 수집 (new 레벨에서는 사용하지 않음)
    let externalLinks = null;
    if (typeof window.getExternalLinksFromUI === 'function') {
        externalLinks = window.getExternalLinksFromUI(blogLevel);
    }

    // 상위 블로그 자동 수집 및 참고용 블로그 URL 수집
    const useAutoReference = document.getElementById('generate-use-auto-reference').checked;
    let referenceCount = parseInt(document.getElementById('generate-reference-count').value || '3', 10);
    if (Number.isNaN(referenceCount)) referenceCount = 3;
    referenceCount = Math.min(10, Math.max(1, referenceCount));

    let manualReferenceUrls = null;
    if (typeof window.getReferenceBlogsFromUI === 'function') {
        manualReferenceUrls = window.getReferenceBlogsFromUI();
    }

    // 이미지 생성 여부 확인
    const generateImages = document.getElementById('generate-images').checked;
    // 이미지 스타일 확인 (드롭다운에서 선택)
    const imageStyleSelect = document.getElementById('image-style-select');
    const imageStyle = imageStyleSelect && imageStyleSelect.value ? imageStyleSelect.value : 'photo'; // 기본값: photo (선택 안 하면 photo)

    // 결과 영역 표시 및 로딩 메시지 표시
    const resultDiv = document.getElementById('result');
    const resultContent = document.getElementById('result-content');
    if (resultDiv) {
        resultDiv.style.display = 'block';
        // result-content 영역은 숨김 (에디터 영역만 표시)
        if (resultContent) {
            resultContent.innerHTML = '';
            resultContent.style.display = 'none';
        }
        // 에디터 영역 표시
        const blogEditorSections = resultDiv.querySelector('.blog-editor-sections');
        if (blogEditorSections) {
            blogEditorSections.style.display = 'block';
            blogEditorSections.style.position = 'relative';
            // 기존 로딩 오버레이 제거
            const existingOverlay = blogEditorSections.querySelector('#blog-generate-loading');
            if (existingOverlay) {
                existingOverlay.remove();
            }
            // 로딩 오버레이 추가
            const loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'blog-generate-loading';
            loadingOverlay.style.cssText = 'display: flex; align-items: center; justify-content: center; min-height: 400px; flex-direction: column; gap: 20px; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255, 255, 255, 0.95); z-index: 100;';
            loadingOverlay.innerHTML = `
                <div class="spinner" style="border-top-color: #3BB1E2;"></div>
                <p id="blog-generate-loading-text" style="font-size: 1.1rem; color: #666; font-weight: 500; margin-bottom: 10px;">블로그를 생성 중입니다...</p>
                <div style="width: 300px; background: #e0e0e0; border-radius: 10px; overflow: hidden; height: 8px;">
                    <div id="blog-generate-progress-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #3BB1E2, #667eea); transition: width 0.3s ease; border-radius: 10px;"></div>
                </div>
                <p id="blog-generate-progress-text" style="font-size: 0.9rem; color: #999; margin-top: 5px;">0%</p>
            `;
            blogEditorSections.appendChild(loadingOverlay);
        }
        const resultHeader = resultDiv.querySelector('.result-header');
        if (resultHeader) {
            resultHeader.style.display = 'flex';
        }
    }

    // 전체 단계 수 계산
    const hasReferenceStep = useAutoReference || (manualReferenceUrls && manualReferenceUrls.length > 0);
    const hasImageStep = generateImages;
    
    // 각 단계별 진행률 범위 정의
    let progressRanges = [];
    let currentProgressIndex = 0;
    
    if (hasReferenceStep) {
        progressRanges.push({ start: 0, end: 15, label: '상위 블로그 분석 중' });
    }
    progressRanges.push({ start: hasReferenceStep ? 15 : 0, end: 70, label: '블로그 글 생성 중' });
    if (hasImageStep) {
        progressRanges.push({ start: 70, end: 95, label: '이미지 생성 중' });
    }
    progressRanges.push({ start: hasImageStep ? 95 : 70, end: 100, label: '파일 저장 중' });
    
    // 프로그레스 바 업데이트 함수
    function updateProgress(percentage, label) {
        const progressBar = document.getElementById('blog-generate-progress-bar');
        const progressText = document.getElementById('blog-generate-progress-text');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
        if (progressText) {
            progressText.textContent = `${Math.round(percentage)}%`;
        }
        if (label) {
            const loadingText = document.getElementById('blog-generate-loading-text');
            if (loadingText) {
                loadingText.textContent = label;
            }
        }
    }
    
    // 진행 중인 시뮬레이션 인터벌 추적
    let currentSimulationInterval = null;
    let currentProgressValue = 0; // 현재 진행률 값 추적
    
    // 단계별 진행률 시뮬레이션 함수
    function simulateStepProgress(startPercent, endPercent, label, duration = 1000) {
        // 기존 시뮬레이션 중지
        if (currentSimulationInterval) {
            clearInterval(currentSimulationInterval);
        }
        
        const startProgress = Math.max(startPercent, currentProgressValue); // 현재 진행률부터 시작
        const endProgress = endPercent;
        const steps = 30; // 30단계로 나누어 더 부드럽게 진행
        const stepDuration = duration / steps;
        const stepIncrement = (endProgress - startProgress) / steps;
        
        let currentStep = 0;
        currentSimulationInterval = setInterval(() => {
            currentStep++;
            const currentProgress = Math.min(startProgress + (stepIncrement * currentStep), endProgress);
            currentProgressValue = currentProgress; // 현재 진행률 저장
            updateProgress(currentProgress, label);
            
            if (currentStep >= steps || currentProgress >= endProgress) {
                clearInterval(currentSimulationInterval);
                currentSimulationInterval = null;
                currentProgressValue = endProgress;
            }
        }, stepDuration);
    }
    
    // 시뮬레이션 즉시 완료 함수 (부드럽게 증가)
    function completeSimulation(endPercent, label) {
        if (currentSimulationInterval) {
            clearInterval(currentSimulationInterval);
            currentSimulationInterval = null;
        }
        
        // 현재 진행률이 목표보다 낮으면 부드럽게 증가
        if (currentProgressValue < endPercent) {
            const diff = endPercent - currentProgressValue;
            const steps = 10;
            const stepIncrement = diff / steps;
            let step = 0;
            
            const smoothInterval = setInterval(() => {
                step++;
                const newProgress = Math.min(currentProgressValue + (stepIncrement * step), endPercent);
                currentProgressValue = newProgress;
                updateProgress(newProgress, label);
                
                if (step >= steps || newProgress >= endPercent) {
                    clearInterval(smoothInterval);
                    currentProgressValue = endPercent;
                    updateProgress(endPercent, label);
                }
            }, 50);
        } else {
            updateProgress(endPercent, label);
            currentProgressValue = endPercent;
        }
    }
    
    // 초기 진행률 표시
    currentProgressValue = 0;
    updateProgress(0, progressRanges[0]?.label || '블로그를 생성 중입니다...');

    try {
        const banWordsList = banWords ? banWords.split(',').map(w => w.trim()).filter(w => w) : null;

        // 첫 번째 단계 시작 (상위 블로그 분석 또는 블로그 글 생성)
        if (hasReferenceStep) {
            simulateStepProgress(0, 15, '상위 블로그 분석 중', 2000); // 상위 블로그 분석 시뮬레이션
        } else {
            // 상위 블로그 분석이 없으면 바로 블로그 글 생성 시작
            simulateStepProgress(0, 70, '블로그 글 생성 중', 30000); // 블로그 글 생성은 더 오래 걸림 (30초)
        }

        // 백엔드 요청 전에 블로그 글 생성 시뮬레이션 시작 (상위 블로그 분석이 있는 경우)
        let blogGenerationSimulationStarted = false;
        if (hasReferenceStep) {
            // 상위 블로그 분석이 완료되면 블로그 글 생성 시뮬레이션 시작
            const startBlogGen = setTimeout(() => {
                if (currentProgressValue < 15) {
                    currentProgressValue = 15;
                    updateProgress(15, '블로그 글 생성 중');
                }
                // 백엔드 응답을 기다리는 동안 계속 진행률 증가
                simulateStepProgress(Math.max(15, currentProgressValue), 70, '블로그 글 생성 중', 30000);
                blogGenerationSimulationStarted = true;
            }, 2100); // 상위 블로그 분석 완료 후 시작
        }

        // 타임아웃 설정 (5분 = 300초)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5분 타임아웃
        
        const response = await apiFetch(`${API_BASE_URL}/api/generate-blog`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keywords: keywords,
                category: category,
                blog_level: blogLevel,
                ban_words: banWordsList,
                use_auto_reference: useAutoReference,
                reference_count: referenceCount,
                manual_reference_urls: manualReferenceUrls,
                external_links: externalLinks,
                generate_images: generateImages,
                image_style: generateImages ? imageStyle : 'photo', // 이미지 생성 시에만 스타일 전달
                save_json: true
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        // 상위 블로그 분석 완료 → 블로그 글 생성 시작
        // 백엔드 응답을 기다리는 동안 블로그 글 생성 시뮬레이션 계속 실행
        if (hasReferenceStep && !blogGenerationSimulationStarted) {
            // 15%로 즉시 설정하고 블로그 글 생성 시뮬레이션 시작
            if (currentProgressValue < 15) {
                currentProgressValue = 15;
                updateProgress(15, '블로그 글 생성 중');
            }
            // 백엔드 응답을 기다리는 동안 계속 진행률 증가 (30초 동안 15% → 70%)
            simulateStepProgress(Math.max(15, currentProgressValue), 70, '블로그 글 생성 중', 30000);
            blogGenerationSimulationStarted = true;
        }
        // else는 이미 위에서 블로그 글 생성 시뮬레이션이 시작되었으므로 추가 작업 불필요

        // 응답이 JSON인지 확인
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`서버 응답 오류: ${text.substring(0, 100)}`);
        }

        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || '블로그 생성 실패');
        }

        // 블로그 글 생성 완료 (백엔드 응답 수신 시)
        // 현재 진행률이 70% 미만이면 부드럽게 70%까지 증가 (최소 1초는 진행률 증가)
        const targetProgress = 70;
        if (currentProgressValue < targetProgress) {
            // 현재 진행률에서 70%까지 부드럽게 증가 (최소 1초)
            const diff = targetProgress - currentProgressValue;
            const minDuration = 1000; // 최소 1초
            const steps = Math.max(20, Math.ceil(diff / 2)); // 최소 20단계
            const stepDuration = minDuration / steps;
            const stepIncrement = diff / steps;
            
            let step = 0;
            const smoothInterval = setInterval(() => {
                step++;
                const newProgress = Math.min(currentProgressValue + (stepIncrement * step), targetProgress);
                currentProgressValue = newProgress;
                updateProgress(newProgress, '블로그 글 생성 중');
                
                if (step >= steps || newProgress >= targetProgress) {
                    clearInterval(smoothInterval);
                    currentProgressValue = targetProgress;
                    updateProgress(targetProgress, '블로그 글 생성 완료');
                }
            }, stepDuration);
            
            // 최소 1초 대기
            await new Promise(resolve => setTimeout(resolve, minDuration));
        } else {
            updateProgress(70, '블로그 글 생성 완료');
            currentProgressValue = 70;
            await new Promise(resolve => setTimeout(resolve, 300));
        }

        // 이미지 생성 단계 (체크박스가 활성화된 경우만)
        if (hasImageStep) {
            const imageCount = data.blog_content?.generated_images?.length || 0;
            const imageLabel = imageCount > 0 ? `이미지 생성 중 (${imageCount}개)` : '이미지 생성 중';
            // 이미지 생성 시뮬레이션 (70% → 95%)
            simulateStepProgress(70, 95, imageLabel, 2000);
            await new Promise(resolve => setTimeout(resolve, 2000));
            updateProgress(95, imageCount > 0 ? `이미지 생성 완료 (${imageCount}개)` : '이미지 생성 완료');
            currentProgressValue = 95;
        }

        // 파일 저장 단계
        const saveStartPercent = hasImageStep ? 95 : 70;
        const saveLabel = '파일 저장 중';
        updateProgress(saveStartPercent, saveLabel);
        // 파일 저장 시뮬레이션
        simulateStepProgress(saveStartPercent, 100, saveLabel, 1000);
        await new Promise(resolve => setTimeout(resolve, 1000));
        updateProgress(100, '파일 저장 완료');
        currentProgressValue = 100;

        // 완료 메시지
        setTimeout(() => {
            // 100% 완료 표시
            updateProgress(100, '완료!');
            
            setTimeout(() => {
                // 로딩 오버레이 제거
                const blogEditorSections = document.querySelector('.blog-editor-sections');
                if (blogEditorSections) {
                    const loadingOverlay = blogEditorSections.querySelector('#blog-generate-loading');
                    if (loadingOverlay) {
                        loadingOverlay.remove();
                    }
                    blogEditorSections.style.position = '';
                }
                showResult(data, 'generate');
                // 사용량 업데이트
                updateUsageInfo();
            }, 500);
        }, 600);

    } catch (error) {
        // 로딩 오버레이 제거
        const blogEditorSections = document.querySelector('.blog-editor-sections');
        if (blogEditorSections) {
            const loadingOverlay = blogEditorSections.querySelector('#blog-generate-loading');
            if (loadingOverlay) {
                loadingOverlay.remove();
            }
            blogEditorSections.style.position = '';
        }
        showError(error.message);
        hideLoading();
    }
}

// 블로그 아이디어 생성 (제목 + 작성 프롬프트)
async function handleGenerateIdeas() {
    const keywordInput = document.getElementById('ideas-keyword');
    const topicInput = document.getElementById('ideas-topic');
    const blogProfileInput = document.getElementById('ideas-blog-profile');
    const extraPromptInput = document.getElementById('ideas-extra-prompt');
    const countInput = document.getElementById('ideas-count');
    const autoTopicCheckbox = document.getElementById('ideas-auto-topic');
    const generateBtn = document.getElementById('ideas-generate-btn');
    const statusText = document.getElementById('ideas-status');

    const keyword = (keywordInput?.value || '').trim();
    const topic = (topicInput?.value || '').trim();
    const blogProfile = (blogProfileInput?.value || '').trim();
    let extraPrompt = (extraPromptInput?.value || '').trim();
    let count = parseInt(countInput?.value || '3', 10);
    const autoTopic = !!(autoTopicCheckbox && autoTopicCheckbox.checked);

    // 유효성 검증
    if (!keyword) {
        alert('대표 키워드를 입력하세요.');
        keywordInput && keywordInput.focus();
        return;
    }
    if (!topic && !autoTopic) {
        alert('주제 / 방향을 입력하거나, \"주제 / 방향을 GPT에게 추천받기\"를 선택하세요.');
        topicInput && topicInput.focus();
        return;
    }
    if (!blogProfile) {
        alert('내 블로그의 특징을 간단히 입력해주세요.');
        blogProfileInput && blogProfileInput.focus();
        return;
    }

    if (keyword.length > 100) {
        alert('대표 키워드는 100자 이하여야 합니다.');
        keywordInput && keywordInput.focus();
        return;
    }
    if (topic && topic.length > 150) {
        alert('주제 / 방향은 150자 이하여야 합니다.');
        topicInput && topicInput.focus();
        return;
    }
    if (blogProfile.length > 500) {
        alert('내 블로그의 특징은 500자 이하여야 합니다.');
        blogProfileInput && blogProfileInput.focus();
        return;
    }
    if (extraPrompt && extraPrompt.length > 600) {
        alert('추가 프롬프트는 600자 이하여야 합니다.');
        extraPromptInput && extraPromptInput.focus();
        return;
    }

    if (Number.isNaN(count)) count = 3;
    count = Math.min(10, Math.max(1, count));
    if (countInput) {
        countInput.value = String(count);
    }

    // 버튼/상태 UI 업데이트
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.textContent = '생성 중...';
    }

    // 결과 영역 표시 및 로딩 메시지 표시
    const ideasResult = document.getElementById('ideas-result');
    const ideasResultContent = document.getElementById('ideas-result-content');
    if (ideasResult) {
        ideasResult.style.display = 'block';
    }
    if (ideasResultContent) {
        ideasResultContent.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; min-height: 300px; flex-direction: column; gap: 20px;">
                <div class="spinner" style="border-top-color: #3BB1E2;"></div>
                <p style="font-size: 1.1rem; color: #666; font-weight: 500;">블로그 프롬프트를 생성 중입니다...</p>
            </div>
        `;
    }

    try {

        const res = await apiFetch(`${API_BASE_URL}/api/generate-blog-ideas`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keyword,
                topic,
                blog_profile: blogProfile,
                extra_prompt: extraPrompt || null,
                count,
                auto_topic: autoTopic
            })
        });

        // 응답이 JSON인지 확인
        const contentType = res.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await res.text();
            throw new Error(`서버 응답 오류: ${text.substring(0, 100)}`);
        }

        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.error || data.detail || '아이디어 생성에 실패했습니다.');
        }

        setTimeout(() => {
            renderIdeasResult(data);
        }, 500);
    } catch (e) {
        console.error(e);
        showError(e.message || '아이디어 생성 중 오류가 발생했습니다.');
    } finally {
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = '아이디어 생성';
        }
        if (statusText) {
            statusText.style.display = 'none';
        }
        // 사용량 업데이트
        updateUsageInfo();
    }
}

// 블로그 아이디어 결과 렌더링
function renderIdeasResult(data) {
    const container = document.getElementById('ideas-result');
    const contentDiv = document.getElementById('ideas-result-content');
    const zipBtn = document.getElementById('ideas-download-zip-btn');

    if (!container || !contentDiv) return;

    // 결과 데이터를 전역 변수에 저장 (탭 전환 시 복원용)
    window.currentIdeasResult = data;

    const ideas = Array.isArray(data.ideas) ? data.ideas : [];

    if (ideas.length === 0) {
        contentDiv.innerHTML = '<p>생성된 아이디어가 없습니다. 입력값을 조금 더 구체적으로 조정해 보세요.</p>';
    } else {
        let html = '<div class="ideas-list">';

        ideas.forEach((idea) => {
            const idx = idea.index || 0;
            const title = idea.title || '';
            const prompt = idea.prompt || '';
            const filePath = idea.file_path || null;

            const safeTitle = escapeHtml(title);
            const safePrompt = escapeHtml(prompt);

            html += `
                <div class="idea-card">
                    <div class="idea-card-header">
                        <span class="idea-index">프롬프트 ${idx}</span>
                        ${filePath ? `<button type="button" class="btn-secondary-small" data-file-path="${filePath}" onclick="downloadIdeaFile('${filePath}')">TXT 다운로드</button>` : ''}
                    </div>
                    <div class="idea-card-body">
                        <div class="idea-title-row">
                            <label>제목</label>
                            <div class="idea-title-text">${safeTitle}</div>
                            <button type="button" class="btn-copy-small" onclick="copyTextToClipboard('${safeTitle.replace(/'/g, "\\'")}')">제목 복사</button>
                        </div>
                        <div class="idea-prompt-row">
                            <label>작성 프롬프트</label>
                            <textarea class="idea-prompt-text" readonly>${prompt}</textarea>
                            <button type="button" class="btn-copy-small" onclick="copyTextToClipboard(\`${prompt.replace(/`/g, '\\`')}\`)">프롬프트 복사</button>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        contentDiv.innerHTML = html;
    }

    // ZIP 버튼 처리
    if (zipBtn) {
        if (data.zip_path) {
            zipBtn.style.display = 'inline-flex';
            zipBtn.onclick = function() {
                const url = `${API_BASE_URL}${data.zip_path}`;
                window.location.href = url;
            };
        } else {
            zipBtn.style.display = 'none';
            zipBtn.onclick = null;
        }
    }

    container.style.display = 'block';
}

// 단일 아이디어 TXT 파일 다운로드
async function downloadIdeaFile(filePath) {
    if (!filePath) return;
    const url = filePath.startsWith('http') ? filePath : `${API_BASE_URL}${filePath}`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('파일 다운로드에 실패했습니다.');
        }
        
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        
        // 파일명 추출 (경로에서 마지막 부분)
        const filename = filePath.split('/').pop() || 'idea.txt';
        a.download = filename;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // 메모리 해제
        window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
        console.error('다운로드 오류:', error);
        alert('파일 다운로드에 실패했습니다: ' + error.message);
    }
}

// 텍스트 복사 헬퍼 (일반 텍스트용)
function copyTextToClipboard(text) {
    if (!text) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            alert('클립보드에 복사되었습니다.');
        }).catch(err => {
            console.error('복사 실패:', err);
            fallbackCopyText(text);
        });
    } else {
        fallbackCopyText(text);
    }
}

function fallbackCopyText(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.top = '-1000px';
    textarea.style.left = '-1000px';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        alert('클립보드에 복사되었습니다.');
    } catch (e) {
        alert('복사에 실패했습니다. 직접 선택해서 복사해주세요.');
    }
    document.body.removeChild(textarea);
}

// 네이버 발행용 파일 다운로드
async function handleExportBlog() {
    if (!quillTitle || !quillBody || !quillTags) {
        alert('에디터가 초기화되지 않았습니다.');
        return;
    }

    const blogContent = quillContentToJSON();
    if (!blogContent) {
        alert('블로그 내용을 JSON으로 변환할 수 없습니다.');
        return;
    }

    // 에디터 내 모든 이미지 수집
    const imgNodes = quillBody.root.querySelectorAll('img');
    const images = Array.from(imgNodes).map((img, idx) => {
        const src = img.getAttribute('src') || '';
        return {
            index: idx + 1,
            src,
            // AI 생성 이미지 여부 (기존 style 필드를 그대로 사용)
            style: (window.imageStyleMap && window.imageStyleMap[src]) || null,
            // 썸네일 여부 (별도 맵에서 관리)
            is_thumbnail: !!(window.imageThumbnailMap && window.imageThumbnailMap[src]),
            caption: (window.imageCaptionMap && window.imageCaptionMap[src]) || ''
        };
    });

    try {
        showLoading('네이버 발행용 파일 생성 중...');
        updateLoadingStep('에디터 내용을 JSON으로 변환 중', 'processing');

        const res = await apiFetch(`${API_BASE_URL}/api/export-blog`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                blog_content: blogContent,
                images: images
            })
        });

        // 응답이 JSON인지 확인
        const contentType = res.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await res.text();
            throw new Error(`서버 응답 오류: ${text.substring(0, 100)}`);
        }

        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.error || '파일 내보내기 실패');
        }

        updateLoadingStep('에디터 내용을 JSON으로 변환 중', 'completed');
        updateLoadingStep('파일 패키지 생성 완료', 'completed');

        if (data.zip_path) {
            // ZIP 파일 다운로드
            const downloadUrl = `${API_BASE_URL}${data.zip_path}`;
            window.location.href = downloadUrl;
        } else {
            alert('ZIP 파일 경로를 받지 못했습니다.');
        }

        hideLoading();
    } catch (e) {
        console.error(e);
        hideLoading();
        alert('발행용 파일 생성 중 오류가 발생했습니다: ' + e.message);
    }
}

// 이미지 다운로드
async function handleDownloadImages() {
    // 현재 블로그 콘텐츠에서 이미지 경로 추출
    const content = window.currentBlogContent;
    if (!content) {
        alert('블로그 콘텐츠가 없습니다.');
        return;
    }
    
    const generatedImages = content.generated_images || [];
    if (generatedImages.length === 0) {
        alert('다운로드할 이미지가 없습니다.');
        return;
    }
    
    // 이미지 경로 추출 (blog/create_naver/images 기준)
    const imagePaths = generatedImages.map(img => {
        let path = img.image_path || img.full_path || '';
        
        // image_path가 상대 경로인 경우 처리
        if (path && !path.startsWith('/')) {
            // 이미 images/로 시작하면 그대로 사용
            if (path.startsWith('images/')) {
                return path;
            }
            // images 폴더가 없으면 추가
            return `images/${path}`;
        }
        // /static/blog/create_naver/로 시작하는 경우
        if (path.startsWith('/static/blog/create_naver/')) {
            // /static/blog/create_naver/ 부분 제거
            return path.substring('/static/blog/create_naver/'.length);
        }
        return path;
    }).filter(path => path); // 빈 값 제거
    
    if (imagePaths.length === 0) {
        alert('유효한 이미지 경로를 찾을 수 없습니다.');
        return;
    }
    
    try {
        const downloadBtn = document.getElementById('download-images-btn');
        if (downloadBtn) {
            downloadBtn.disabled = true;
            downloadBtn.textContent = '다운로드 준비 중...';
        }
        
        const response = await apiFetch(`${API_BASE_URL}/api/download-images`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_paths: imagePaths
            })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || '이미지 다운로드 실패');
        }
        
        if (data.zip_path) {
            // ZIP 파일 다운로드
            const downloadUrl = `${API_BASE_URL}${data.zip_path}`;
            window.location.href = downloadUrl;
        } else {
            alert('ZIP 파일 경로를 받지 못했습니다.');
        }
        
    } catch (e) {
        console.error(e);
        alert('이미지 다운로드 중 오류가 발생했습니다: ' + e.message);
    } finally {
        const downloadBtn = document.getElementById('download-images-btn');
        if (downloadBtn) {
            downloadBtn.disabled = false;
            downloadBtn.textContent = '이미지 다운로드';
        }
    }
}

// JSON 파일 불러오기
// 블로그 콘텐츠 렌더링
function renderBlogContent(content) {
    if (!content) return '';

    const applyStyle = (style) => {
        if (!style) return '';
        let css = '';
        if (style.font_size) css += `font-size: ${style.font_size}px; `;
        // 색상: 기본값 설정하여 검정 배경 문제 해결
        if (style.color) {
            css += `color: ${style.color}; `;
        } else {
            css += 'color: #333333; ';
        }
        // 배경색: 명시적으로 설정
        if (style.background) {
            css += `background-color: ${style.background}; `;
        } else {
            css += 'background-color: transparent; ';
        }
        if (style.bold) css += 'font-weight: bold; ';
        if (style.italic) css += 'font-style: italic; ';
        if (style.underline) css += 'text-decoration: underline; ';
        if (style.line_height) css += `line-height: ${style.line_height}; `;
        if (style.padding) css += `padding: ${style.padding}; `;
        if (style.margin) css += `margin: ${style.margin}; `;
        if (style.border_left) css += `border-left: ${style.border_left}; `;
        if (style.quote) {
            css += 'border-left: 4px solid #cccccc; background-color: #f5f5f5; padding: 10px 15px; margin: 10px 0; ';
            // 인용구도 텍스트 색상 명시
            if (!style.color) {
                css += 'color: #333333; ';
            }
        }
        return css ? `style="${css}"` : '';
    };

    let html = '<div class="blog-content">';

    // 제목
    if (content.title) {
        html += `<h1 ${applyStyle(content.title.style)}>${escapeHtml(content.title.content)}</h1>`;
    }

    // 서론
    if (content.introduction) {
        html += `<div ${applyStyle(content.introduction.style)}>${escapeHtml(content.introduction.content).replace(/\n/g, '<br>')}</div>`;
    }

    // 본문
    if (content.body && Array.isArray(content.body)) {
        html += '<div class="blog-body">';
        content.body.forEach((section, sectionIdx) => {
            html += '<div class="blog-section">';
            
            // 부제목
            if (section.subtitle) {
                html += `<h2 ${applyStyle(section.subtitle.style)}>${escapeHtml(section.subtitle.content)}</h2>`;
            }

            // 블록들
            if (section.blocks && Array.isArray(section.blocks)) {
                html += '<div class="blog-blocks">';
                section.blocks.forEach((block, blockIdx) => {
                    if (block.type === 'paragraph') {
                        html += `<p ${applyStyle(block.style)}>${escapeHtml(block.content).replace(/\n/g, '<br>')}</p>`;
                    } else if (block.type === 'quote') {
                        html += `<blockquote ${applyStyle(block.style)}>${escapeHtml(block.content).replace(/\n/g, '<br>')}</blockquote>`;
                    } else if (block.type === 'list') {
                        html += `<ul ${applyStyle(block.style)}>`;
                        if (block.items && Array.isArray(block.items)) {
                            block.items.forEach(item => {
                                html += `<li>${escapeHtml(item)}</li>`;
                            });
                        }
                        html += '</ul>';
                    } else if (block.type === 'image_placeholder') {
                        const normalized = normalizeImagePlaceholderText(block.placeholder || '[이미지 삽입]');
                        html += `<div ${applyStyle(block.style)}>${escapeHtml(normalized)}</div>`;
                    } else if (block.type === 'hr') {
                        html += `<hr ${applyStyle(block.style)}>`;
                    }
                });
                html += '</div>';
            }

            html += '</div>';
        });
        html += '</div>';
    }

    // 결론
    if (content.conclusion) {
        html += `<div ${applyStyle(content.conclusion.style)}>${escapeHtml(content.conclusion.content).replace(/\n/g, '<br>')}</div>`;
    }

    // FAQ
    if (content.faq && Array.isArray(content.faq) && content.faq.length > 0) {
        html += '<div class="blog-faq"><h2>자주 묻는 질문</h2>';
        content.faq.forEach((faq, faqIdx) => {
            html += '<div class="faq-item">';
            if (faq.q) {
                html += `<h3 ${applyStyle(faq.q.style)}>Q: ${escapeHtml(faq.q.content)}</h3>`;
            }
            if (faq.a) {
                html += `<p ${applyStyle(faq.a.style)}>A: ${escapeHtml(faq.a.content).replace(/\n/g, '<br>')}</p>`;
            }
            html += '</div>';
        });
        html += '</div>';
    }

    // 태그
    if (content.tags && Array.isArray(content.tags) && content.tags.length > 0) {
        html += '<div class="blog-tags"><strong>태그: </strong>';
        content.tags.forEach((tag, tagIdx) => {
            html += `<span class="tag">#${escapeHtml(tag)}</span>`;
        });
        html += '</div>';
    }

    html += '</div>';

    // 복사 버튼 추가
    html += `
        <div style="margin-top: 30px; padding: 20px; background: #f0f0f0; border-radius: 8px; text-align: center;">
            <button id="copy-blog-content-btn" onclick="copyBlogContentToNaverEditor()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 14px 32px; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: transform 0.2s;">
                📋 네이버 에디터에 복사하기
            </button>
            <p style="margin-top: 12px; font-size: 0.9rem; color: #666; line-height: 1.5;">복사 버튼을 클릭하면 스타일이 포함된 HTML 형식으로 클립보드에 복사됩니다.<br>네이버 블로그 에디터에 바로 붙여넣으세요.</p>
        </div>
    `;

    // JSON 원본 보기
    html += `<details style="margin-top: 20px; user-select: none;"><summary style="cursor: pointer; font-weight: 600; color: #667eea;">JSON 원본 보기</summary><pre style="user-select: text; margin-top: 10px;">${JSON.stringify(content, null, 2)}</pre></details>`;

    // 복사를 위한 원본 콘텐츠를 전역 변수에 저장
    window.currentBlogContent = content;

    return html;
}

// 블로그 콘텐츠를 제목, 본문, 태그로 분리하여 렌더링 (Quill 에디터 사용)
function renderBlogContentSeparated(content) {
    if (!content) return;

    // 로딩 오버레이 제거
    const blogEditorSections = document.querySelector('.blog-editor-sections');
    if (blogEditorSections) {
        const loadingOverlay = blogEditorSections.querySelector('#blog-generate-loading');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
        blogEditorSections.style.position = '';
    }

    // Quill 에디터 초기화
    initializeQuillEditors();

    // 약간의 지연을 두고 콘텐츠 로드 (에디터 초기화 완료 대기)
    setTimeout(() => {
        loadBlogContentToQuill(content);
        
        // 이미지 다운로드 버튼 활성화/비활성화 업데이트
        const downloadImagesBtn = document.getElementById('download-images-btn');
        if (downloadImagesBtn) {
            const hasImages = content.generated_images && content.generated_images.length > 0;
            downloadImagesBtn.disabled = !hasImages;
            downloadImagesBtn.style.display = 'inline-block';
            if (!hasImages) {
                downloadImagesBtn.title = '생성된 이미지가 없습니다';
            } else {
                downloadImagesBtn.title = '';
            }
        }
    }, 200);
}

// 네이버 에디터용 HTML 스타일 적용 함수
function applyNaverStyle(style, isSubtitle = false) {
    let inlineStyle = '';
    
    // 소제목인 경우 강한 기본 스타일 적용 (border-bottom 제거: 네이버 에디터 자동 구분선 방지)
    if (isSubtitle) {
        inlineStyle += 'font-weight: bold; font-size: 20px; color: #333333; margin-top: 0; margin-bottom: 15px; background-color: transparent; display: block; ';
    }
    
    if (!style && !isSubtitle) return '';
    
    // 폰트 크기
    if (style && style.font_size) {
        inlineStyle += `font-size: ${style.font_size}px; `;
    }
    
    // 색상 (배경색 문제 해결: 텍스트 색상이 없으면 기본 색상 사용)
    if (style && style.color) {
        if (!isSubtitle) {
            inlineStyle += `color: ${style.color}; `;
        }
    } else if (!isSubtitle) {
        // 기본 텍스트 색상 (검정색이 아닌 진한 회색)
        inlineStyle += `color: #333333; `;
    }
    
    // 배경색 (명시적으로 설정하여 검정 배경 문제 해결)
    if (style && style.background) {
        inlineStyle += `background-color: ${style.background}; `;
    } else if (!isSubtitle) {
        // 배경색이 없으면 투명
        inlineStyle += `background-color: transparent; `;
    }
    
    // 굵게
    if (style && style.bold && !isSubtitle) {
        inlineStyle += 'font-weight: bold; ';
    }
    
    // 기울임
    if (style && style.italic) {
        inlineStyle += 'font-style: italic; ';
    }
    
    // 밑줄
    if (style && style.underline) {
        inlineStyle += 'text-decoration: underline; ';
    }
    
    // 줄 간격
    if (style && style.line_height) {
        inlineStyle += `line-height: ${style.line_height}; `;
    }
    
    // 패딩
    if (style && style.padding) {
        inlineStyle += `padding: ${style.padding}; `;
    }
    
    // 마진 (소제목이 아니면 스타일의 마진 사용)
    if (style && style.margin && !isSubtitle) {
        inlineStyle += `margin: ${style.margin}; `;
    }
    
    // 왼쪽 테두리
    if (style && style.border_left) {
        inlineStyle += `border-left: ${style.border_left}; `;
    }
    
    // 인용구 스타일
    if (style && style.quote) {
        inlineStyle += 'border-left: 4px solid #cccccc; background-color: #f5f5f5; padding: 10px 15px; margin: 20px 0; ';
        // 인용구는 텍스트 색상도 명시
        if (!style.color) {
            inlineStyle += 'color: #333333; ';
        }
    }
    
    return inlineStyle ? `style="${inlineStyle.trim()}"` : '';
}

// 네이버 에디터에 복사하기 (HTML 형식으로 스타일 포함)
function copyBlogContentToNaverEditor() {
    // Quill 에디터에서 직접 내용 가져오기
    if (!quillTitle || !quillBody || !quillTags) {
        alert('에디터가 초기화되지 않았습니다.');
        return;
    }

    // Quill에서 HTML 가져오기
    const titleHtml = quillTitle.root.innerHTML;
    const bodyHtml = quillBody.root.innerHTML;
    const tagsText = quillTags.getText();

    // 기존 JSON 구조도 유지 (하위 호환성)
    const content = window.currentBlogContent || {};
    let html = '';

    // 제목
    if (titleHtml) {
        html += `<div style="margin-bottom: 20px; font-size: 26px; font-weight: bold; color: #333;">${titleHtml}</div>\n`;
    }

    // 본문 (Quill HTML 사용)
    if (bodyHtml) {
        // 에디터 내에서만 사용되는 이미지 스타일 툴바 제거
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = bodyHtml;
        tempDiv.querySelectorAll('.image-style-toolbar').forEach(el => el.remove());

        let processedBodyHtml = tempDiv.innerHTML;

        // Quill의 이미지 URL을 절대 경로로 변환
        processedBodyHtml = processedBodyHtml.replace(/src="([^"]+)"/g, (match, url) => {
            // 상대 경로인 경우 API_BASE_URL 추가
            if (url.startsWith('/static/')) {
                return `src="${API_BASE_URL}${url}"`;
            }
            // 이미 절대 경로인 경우 그대로
            return match;
        });
        
        html += `<div style="line-height: 1.8; color: #333;">${processedBodyHtml}</div>\n`;
    }

    // 클립보드에 HTML 형식으로 복사
    if (navigator.clipboard && navigator.clipboard.write) {
        // HTML과 플레인 텍스트 모두 제공 (네이버 에디터가 HTML을 인식하도록)
        const htmlBlob = new Blob([html], { type: 'text/html' });
        const textBlob = new Blob([html.replace(/<[^>]*>/g, '')], { type: 'text/plain' });
        const data = new ClipboardItem({
            'text/html': htmlBlob,
            'text/plain': textBlob
        });

        navigator.clipboard.write([data]).then(() => {
            const btn = document.getElementById('copy-blog-content-btn');
            if (btn) {
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ 복사 완료!';
                btn.style.background = '#28a745';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                }, 2000);
            }
            alert('✅ 블로그 내용이 클립보드에 복사되었습니다!\n\nCtrl+V (또는 Cmd+V)로 붙여넣으세요.\n스타일이 포함된 HTML 형식으로 복사되었습니다.');
        }).catch(err => {
            console.error('복사 실패:', err);
            fallbackCopyHTMLToClipboard(html);
        });
    } else {
        fallbackCopyHTMLToClipboard(html);
    }
}

// 폴백: 구형 브라우저용 HTML 복사 함수
function fallbackCopyHTMLToClipboard(html) {
    // HTML을 임시 div에 넣어서 복사
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    tempDiv.style.position = 'fixed';
    tempDiv.style.top = '0';
    tempDiv.style.left = '0';
    tempDiv.style.width = '1px';
    tempDiv.style.height = '1px';
    tempDiv.style.opacity = '0';
    tempDiv.style.pointerEvents = 'none';
    tempDiv.style.zIndex = '-1';
    document.body.appendChild(tempDiv);

    // 텍스트 선택 및 복사
    const range = document.createRange();
    range.selectNodeContents(tempDiv);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);

    try {
        const successful = document.execCommand('copy');
        document.body.removeChild(tempDiv);
        selection.removeAllRanges();
        
        if (successful) {
            const btn = document.getElementById('copy-blog-content-btn');
            if (btn) {
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ 복사 완료!';
                btn.style.background = '#28a745';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                }, 2000);
            }
            alert('✅ 블로그 내용이 클립보드에 복사되었습니다!');
        } else {
            alert('복사에 실패했습니다. 텍스트를 수동으로 선택해서 복사해주세요.');
        }
    } catch (err) {
        document.body.removeChild(tempDiv);
        selection.removeAllRanges();
        alert('복사 중 오류가 발생했습니다. 텍스트를 수동으로 선택해서 복사해주세요.');
    }
}

// 이미지 다운로드 함수
function downloadImage(imageUrl, filename) {
    try {
        // 이미지 URL에서 파일 다운로드
        fetch(imageUrl, {
            method: 'GET',
            headers: {
                'Accept': 'image/*'
            }
        })
            .then(response => {
        if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                // Content-Type 확인
                const contentType = response.headers.get('content-type') || 'image/png';
                return response.blob().then(blob => ({ blob, contentType }));
            })
            .then(({ blob, contentType }) => {
                // Blob 타입 확인 및 수정
                if (!blob.type && contentType) {
                    blob = new Blob([blob], { type: contentType });
                }
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                
                // 정리
                setTimeout(() => {
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                }, 100);
            })
            .catch(error => {
                console.error('이미지 다운로드 실패:', error);
                console.error('이미지 URL:', imageUrl);
                alert(`이미지 다운로드에 실패했습니다: ${error.message}`);
            });
    } catch (error) {
        console.error('이미지 다운로드 오류:', error);
        alert('이미지 다운로드 중 오류가 발생했습니다.');
    }
}


// HTML 이스케이프
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// ===== Quill Editor 관련 함수 =====

// 네이버 에디터 기준 폰트 크기 정의
const NAVER_FONT_SIZES = {
    '11': '11px',
    '13': '13px',
    '15': '15px',
    '16': '16px',
    '19': '19px',
    '24': '24px',
    '28': '28px',
    '30': '30px',
    '34': '34px',
    '38': '38px'
};

// 네이버 에디터 스타일 정의
const NAVER_STYLES = {
    'body': '본문',
    'subtitle': '소제목',
    'quote': '인용구'
};

// Quill 커스텀 Size 클래스 등록
const Size = Quill.import('attributors/style/size');
Size.whitelist = Object.keys(NAVER_FONT_SIZES).map(key => NAVER_FONT_SIZES[key]);
Quill.register(Size, true);

// Quill 에디터 인스턴스 저장
let quillTitle = null;
let quillBody = null;
let quillTags = null;

// 에디터 내 이미지 스타일/메타데이터
// - imageStyleMap: src -> 'ai' | null (AI 생성 이미지 여부)
// - imageThumbnailMap: src -> true (썸네일로 사용할지 여부)
// - imageCaptionMap: src -> caption string (이미지 설명)
window.imageStyleMap = window.imageStyleMap || {};
window.imageThumbnailMap = window.imageThumbnailMap || {};
window.imageCaptionMap = window.imageCaptionMap || {};


// localStorage 키
const STORAGE_KEYS = {
    TITLE: 'dmalab_editor_title',
    BODY: 'dmalab_editor_body',
    TAGS: 'dmalab_editor_tags',
    IMAGE_META: 'dmalab_editor_image_meta'
};

// 에디터 내용을 서버에 임시 저장 (IP 기반)
async function saveEditorContent() {
    try {
        const draftData = {};
        
        if (quillTitle) {
            draftData.title = quillTitle.getContents();
        }
        if (quillBody) {
            draftData.body = quillBody.getContents();
        }
        if (quillTags) {
            draftData.tags = quillTags.getContents();
        }
        // 이미지 메타데이터 저장 (스타일/썸네일/캡션)
        draftData.image_meta = {
            styleMap: window.imageStyleMap || {},
            thumbnailMap: window.imageThumbnailMap || {},
            captionMap: window.imageCaptionMap || {}
        };
        
        // 서버에 저장 (에러가 발생해도 조용히 처리 - 사용자 경험 방해하지 않음)
        try {
            await apiFetch(`${API_BASE_URL}/api/save-draft`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(draftData)
            });
        } catch (e) {
            // 네트워크 오류 등은 조용히 처리 (사용자에게 알리지 않음)
            console.warn('[DMaLab] 임시 저장 실패 (조용히 처리):', e);
        }
    } catch (error) {
        console.error('에디터 내용 저장 실패:', error);
    }
}

// 서버에서 에디터 내용 복원 (IP 기반)
async function restoreEditorContent() {
    try {
        const response = await apiFetch(`${API_BASE_URL}/api/get-draft`);
        if (!response.ok) {
            throw new Error('임시 저장 불러오기 실패');
        }
        
        const data = await response.json();
        if (!data.success || !data.title && !data.body && !data.tags) {
            // 저장된 내용이 없음
            return;
        }
        
        if (quillTitle && data.title && data.title.ops && data.title.ops.length > 0) {
            quillTitle.setContents(data.title);
        }
        if (quillBody && data.body && data.body.ops && data.body.ops.length > 0) {
            quillBody.setContents(data.body);
        }
        if (quillTags && data.tags && data.tags.ops && data.tags.ops.length > 0) {
            quillTags.setContents(data.tags);
        }
        
        // 이미지 메타데이터 복원
        if (data.image_meta) {
            window.imageStyleMap = data.image_meta.styleMap || {};
            window.imageThumbnailMap = data.image_meta.thumbnailMap || {};
            window.imageCaptionMap = data.image_meta.captionMap || {};
        } else {
            window.imageStyleMap = {};
            window.imageThumbnailMap = {};
            window.imageCaptionMap = {};
        }
        
        // 에디터 내용 복원 후 높이 재계산
        setTimeout(() => {
            sendHeightToParent();
        }, 100);
    } catch (error) {
        console.error('에디터 내용 복원 실패:', error);
    }
}

// 에디터 내용 초기화 (서버의 임시 저장도 함께 삭제)
async function clearEditorContent() {
    try {
        // 서버에서 임시 저장 삭제
        try {
            await apiFetch(`${API_BASE_URL}/api/delete-draft`, {
                method: 'DELETE'
            });
        } catch (e) {
            console.warn('[DMaLab] 임시 저장 삭제 실패:', e);
        }
        
        if (quillTitle) quillTitle.setContents([]);
        if (quillBody) quillBody.setContents([]);
        if (quillTags) quillTags.setContents([]);

        // 이미지 메타데이터도 초기화
        window.imageStyleMap = {};
        window.imageThumbnailMap = {};
        window.imageCaptionMap = {};
        
        // 에디터 내용 초기화 후 높이 재계산
        setTimeout(() => {
            sendHeightToParent();
        }, 100);
    } catch (error) {
        console.error('에디터 내용 초기화 실패:', error);
    }
}

// 임시 저장된 에디터 내용이 있는지 확인 (서버에서 확인)
async function hasSavedEditorContent() {
    try {
        const response = await apiFetch(`${API_BASE_URL}/api/get-draft`);
        if (!response.ok) {
            return false;
        }
        const data = await response.json();
        return data.success && (data.title || data.body || data.tags);
    } catch (e) {
        console.error('임시 저장 여부 확인 중 오류:', e);
        return false;
    }
}

// 새로고침 시 임시 저장된 글을 불러올지 물어보는 팝업 표시
async function showRestoreDraftModalIfNeeded() {
    const hasContent = await hasSavedEditorContent();
    if (!hasContent) {
        return;
    }

    // 이미 모달이 있으면 다시 만들지 않음
    if (document.querySelector('.autosave-modal-overlay')) {
        return;
    }

    // iframe 내부에서 실행 중이면 부모 페이지에 모달 표시 요청
    if (window.parent !== window) {
        window.parent.postMessage({
            type: 'show-restore-modal',
            source: 'dmalab'
        }, '*');
        
        // 부모 페이지에서 선택 결과를 받을 리스너 등록
        const messageHandler = (event) => {
            // 보안: 부모 페이지에서만 메시지 수신
            if (event.data && event.data.type === 'restore-modal-action') {
                const action = event.data.action;
                if (action === 'restore') {
                    restoreEditorContent();
                } else if (action === 'discard') {
                    clearEditorContent();
                }
                window.removeEventListener('message', messageHandler);
            }
        };
        window.addEventListener('message', messageHandler);
        return;
    }

    // iframe 외부에서 실행 중이면 기존 방식대로 표시
    const overlay = document.createElement('div');
    overlay.className = 'autosave-modal-overlay';

    const modal = document.createElement('div');
    modal.className = 'autosave-modal';
    modal.innerHTML = `
        <h3 class="autosave-modal-title">작성 중이던 글이 있습니다</h3>
        <p class="autosave-modal-message">
            이전에 작성하던 임시 저장 내용을 불러올까요?<br>
            "불러오기"를 선택하면 제목/본문/태그가 복원됩니다.
        </p>
        <div class="autosave-modal-actions">
            <button type="button" class="autosave-btn-primary" data-action="restore">불러오기</button>
            <button type="button" class="autosave-btn-secondary" data-action="discard">새로 작성</button>
        </div>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // 모달이 표시된 후 높이 재계산 (iframe 높이 조정)
    setTimeout(() => {
        sendHeightToParent();
    }, 100);

    const handleAction = (action) => {
        if (action === 'restore') {
            restoreEditorContent();
        } else if (action === 'discard') {
            clearEditorContent();
        }
        overlay.remove();
        // 모달이 닫힌 후 높이 재계산
        setTimeout(() => {
            sendHeightToParent();
        }, 100);
    };

    overlay.addEventListener('click', (e) => {
        // 바깥 클릭 시에는 닫지 않고, 버튼으로만 처리
        const btn = e.target.closest('[data-action]');
        if (!btn) return;
        const action = btn.getAttribute('data-action');
        handleAction(action);
    });
}

// Quill 에디터 초기화
function initializeQuillEditors() {
    // 제목 에디터
    const titleContainer = document.getElementById('result-title');
    if (titleContainer && !quillTitle) {
        quillTitle = new Quill('#result-title', {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'size': Object.values(NAVER_FONT_SIZES) }],
                    ['bold', 'italic', 'underline'],
                    [{ 'color': [] }, { 'background': [] }],
                    ['link']
                ]
            },
            placeholder: '제목을 입력하세요...'
        });
        
        // 제목 변경 시 자동 저장 및 높이 재계산 (디바운싱 적용)
        let titleSaveTimeout = null;
        quillTitle.on('text-change', function() {
            clearTimeout(titleSaveTimeout);
            titleSaveTimeout = setTimeout(() => {
                saveEditorContent(); // async 함수이지만 await 없이 호출 (백그라운드 저장)
                // 높이 재계산
                sendHeightToParent();
            }, 500); // 500ms 후 저장
        });

    }

    // 본문 에디터
    const bodyContainer = document.getElementById('result-body');
    if (bodyContainer && !quillBody) {
        const toolbarOptions = [
            [{ 'size': Object.values(NAVER_FONT_SIZES) }],
            ['bold', 'italic', 'underline', 'strike'],
            [{ 'color': [] }, { 'background': [] }],
            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
            [{ 'indent': '-1'}, { 'indent': '+1' }],
            ['link', 'image'],
            ['clean']
        ];
        
        quillBody = new Quill('#result-body', {
            theme: 'snow',
            modules: {
                toolbar: toolbarOptions
            },
            placeholder: '본문을 입력하세요...'
        });

        // 본문 변경 시 자동 저장 및 높이 재계산 (디바운싱 적용)
        let bodySaveTimeout = null;
        quillBody.on('text-change', function() {
            clearTimeout(bodySaveTimeout);
            bodySaveTimeout = setTimeout(() => {
                saveEditorContent(); // async 함수이지만 await 없이 호출 (백그라운드 저장)
                // 높이 재계산
                sendHeightToParent();
            }, 500); // 500ms 후 저장
        });

        // 이미지 업로드 핸들러
        quillBody.getModule('toolbar').addHandler('image', function() {
            selectLocalImage();
        });

        // 이미지 클릭 시 스타일 편집 UI 표시 (에디터 DOM을 직접 수정하지 않고, 바깥에 오버레이로 표시)
        quillBody.root.addEventListener('click', function (event) {
            const img = event.target.closest('img');

            // 이미지 외 영역 클릭 시 기존 오버레이 제거
            if (!img) {
                const existingOverlay = document.querySelector('.image-style-toolbar-overlay');
                if (existingOverlay) existingOverlay.remove();
                return;
            }

            const src = img.getAttribute('src');
            if (!src) return;

            // 기존 오버레이 제거 후 새로 생성
            const existingOverlay = document.querySelector('.image-style-toolbar-overlay');
            if (existingOverlay) existingOverlay.remove();

            const overlay = document.createElement('div');
            overlay.className = 'image-style-toolbar-overlay image-style-toolbar';
            overlay.innerHTML = `
                <div class="image-style-row">
                    <span class="image-style-label">이미지 스타일:</span>
                    <button type="button" data-style="ai" class="image-style-toggle-btn">AI 생성</button>
                    <button type="button" data-style="thumbnail" class="image-style-toggle-btn">썸네일</button>
                </div>
                <div class="image-caption-row">
                    <input type="text" class="image-caption-input" placeholder="이미지 설명 (파일 제목용) 입력..." />
                </div>
            `;

            // 현재 스타일/썸네일 상태 반영
            const isAi = (window.imageStyleMap && window.imageStyleMap[src] === 'ai');
            const isThumbnail = !!(window.imageThumbnailMap && window.imageThumbnailMap[src]);
            overlay.querySelectorAll('button[data-style]').forEach(btn => {
                const style = btn.getAttribute('data-style');
                if (style === 'ai' && isAi) {
                    btn.classList.add('active');
                } else if (style === 'thumbnail' && isThumbnail) {
                    btn.classList.add('active');
                }
            });

            // 현재 캡션 반영
            const captionInput = overlay.querySelector('.image-caption-input');
            if (captionInput) {
                captionInput.value = window.imageCaptionMap[src] || '';
                captionInput.addEventListener('input', () => {
                    const value = captionInput.value.trim();
                    if (value) {
                        window.imageCaptionMap[src] = value;
                        // 이미지 데이터 속성에도 저장 (추후 활용)
                        img.dataset.caption = value;
                    } else {
                        delete window.imageCaptionMap[src];
                        delete img.dataset.caption;
                    }
                });
            }

            // 버튼 클릭 핸들러
            overlay.addEventListener('click', (e) => {
                const btn = e.target.closest('button[data-style]');
                if (!btn) return;
                const style = btn.getAttribute('data-style');

                if (style === 'ai') {
                    // AI 생성 이미지 토글
                    const prev = (window.imageStyleMap && window.imageStyleMap[src]) || '';
                    const nextStyle = (prev === 'ai') ? '' : 'ai';

                    if (nextStyle) {
                        window.imageStyleMap[src] = nextStyle;
                    } else {
                        delete window.imageStyleMap[src];
                    }
                } else if (style === 'thumbnail') {
                    // 썸네일 토글 (AI 여부와는 독립적으로 동작)
                    const prevThumbnail = !!(window.imageThumbnailMap && window.imageThumbnailMap[src]);
                    if (prevThumbnail) {
                        delete window.imageThumbnailMap[src];
                    } else {
                        window.imageThumbnailMap[src] = true;
                    }
                }

                // 현재 상태 재계산
                const isAiNow = (window.imageStyleMap && window.imageStyleMap[src] === 'ai');
                const isThumbnailNow = !!(window.imageThumbnailMap && window.imageThumbnailMap[src]);

                // 버튼 active 상태 갱신 (각 버튼은 독립 토글)
                overlay.querySelectorAll('button[data-style]').forEach(b => {
                    const s = b.getAttribute('data-style');
                    b.classList.remove('active');
                    if (s === 'ai' && isAiNow) {
                        b.classList.add('active');
                    } else if (s === 'thumbnail' && isThumbnailNow) {
                        b.classList.add('active');
                    }
                });

                // 이미지 클래스/데이터 속성 갱신
                img.classList.remove('img-style-ai', 'img-style-thumbnail');
                img.dataset.style = isAiNow ? 'ai' : '';
                if (isAiNow) img.classList.add('img-style-ai');
                if (isThumbnailNow) img.classList.add('img-style-thumbnail');
            });

            // 화면 좌표 기준으로 이미지 바로 아래에 오버레이 위치시키기
            const imgRect = img.getBoundingClientRect();
            const scrollY = window.scrollY || window.pageYOffset;
            const scrollX = window.scrollX || window.pageXOffset;

            overlay.style.top = `${imgRect.bottom + scrollY + 4}px`;
            overlay.style.left = `${imgRect.left + scrollX}px`;

            document.body.appendChild(overlay);
        });
        
        // 툴바에 스타일 드롭다운 추가 (본문 / 소제목 / 인용구)
        setTimeout(() => {
            const toolbarModule = quillBody.getModule('toolbar');
            if (!toolbarModule || !toolbarModule.container) {
                console.warn('[DMaLab] Quill toolbar 모듈을 찾을 수 없습니다.');
                return;
            }

            const toolbar = toolbarModule.container;

            // 이미 추가되어 있다면 다시 추가하지 않음
            if (toolbar.querySelector('.ql-style-custom')) {
                return;
            }

            const styleContainer = document.createElement('span');
            styleContainer.className = 'ql-formats';

            const styleSelect = document.createElement('select');
            styleSelect.className = 'ql-style-custom';
            styleSelect.title = '글 스타일';

            Object.keys(NAVER_STYLES).forEach(key => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = NAVER_STYLES[key]; // 본문 / 소제목 / 인용구
                styleSelect.appendChild(option);
            });

            // 기본 선택값을 '본문'으로 설정
            styleSelect.value = 'body';

            styleSelect.addEventListener('change', function() {
                const value = this.value;
                const range = quillBody.getSelection(true);
                if (!range) return;

                if (value === 'subtitle') {
                    // 소제목: H2
                    quillBody.formatLine(range.index, range.length, 'header', 2);
                    quillBody.formatLine(range.index, range.length, 'blockquote', false);
                } else if (value === 'quote') {
                    // 인용구
                    quillBody.formatLine(range.index, range.length, 'header', false);
                    quillBody.formatLine(range.index, range.length, 'blockquote', true);
                } else if (value === 'body') {
                    // 본문
                    quillBody.formatLine(range.index, range.length, 'header', false);
                    quillBody.formatLine(range.index, range.length, 'blockquote', false);
                }
                // 선택값은 유지해서 드롭다운에 현재 스타일이 보이도록 함
            });

            styleContainer.appendChild(styleSelect);
            // 툴바 맨 앞에 스타일 드롭다운 삽입
            toolbar.insertBefore(styleContainer, toolbar.firstChild);

            console.log('[DMaLab] 스타일 드롭다운 추가 완료');

            // 현재 커서 위치에 따라 드롭다운 값을 동기화하는 헬퍼
            const syncStyleSelectWithCursor = () => {
                // focus=true를 주지 않아서 다른 에디터(제목/태그)로 포커스를 옮겼을 때
                // 다시 본문으로 포커스가 강제로 돌아오지 않도록 함
                const range = quillBody.getSelection();
                if (!range) return;
                const format = quillBody.getFormat(range);
                if (format.header === 2) {
                    styleSelect.value = 'subtitle';
                } else if (format.blockquote) {
                    styleSelect.value = 'quote';
                } else {
                    styleSelect.value = 'body';
                }
            };

            // 선택 변경 / 내용 변경 시 드롭다운 값 업데이트
            quillBody.on('selection-change', () => {
                syncStyleSelectWithCursor();
            });
            quillBody.on('text-change', () => {
                syncStyleSelectWithCursor();
            });
        }, 150);
        
        // 본문 변경 시 자동 저장은 이미 위에서 설정됨 (1963번 줄)
        // 중복 이벤트 리스너 제거
    }

    // 태그 에디터 (툴바 없이 간단한 텍스트 입력)
    const tagsContainer = document.getElementById('result-tags');
    if (tagsContainer && !quillTags) {
        quillTags = new Quill('#result-tags', {
            theme: 'snow',
            modules: {
                toolbar: false
            },
            placeholder: '태그를 입력하세요 (쉼표로 구분)...'
        });
        
        // 태그 변경 시 자동 저장 및 높이 재계산 (디바운싱 적용)
        let tagsSaveTimeout = null;
        quillTags.on('text-change', function() {
            clearTimeout(tagsSaveTimeout);
            tagsSaveTimeout = setTimeout(() => {
                saveEditorContent();
                // 높이 재계산
                sendHeightToParent();
            }, 500); // 500ms 후 저장
        });
    }
    
    // 에디터 초기화 후 저장된 내용 복원 (단, loadBlogContentToQuill이 호출되지 않은 경우만)
    // loadBlogContentToQuill이 호출되면 자동으로 복원하지 않음
    if (!window._isLoadingBlogContent) {
        setTimeout(() => {
            restoreEditorContent();
        }, 100);
    }
}

// 로컬 이미지 선택 및 삽입
function selectLocalImage() {
    const input = document.createElement('input');
    input.setAttribute('type', 'file');
    input.setAttribute('accept', 'image/*');
    input.click();

    input.onchange = () => {
        const file = input.files[0];
        if (file) {
            // 파일 크기 체크 (5MB 제한)
            if (file.size > 5 * 1024 * 1024) {
                alert('이미지 크기는 5MB 이하여야 합니다.');
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                const imageUrl = e.target.result;
                if (!quillBody) {
                    console.error('[DMaLab] quillBody 인스턴스를 찾을 수 없어 이미지를 삽입하지 못했습니다.');
                    return;
                }

                let range = quillBody.getSelection(true);
                // 선택 영역이 없으면 문서 끝에 삽입
                if (!range) {
                    range = { index: quillBody.getLength(), length: 0 };
                }

                try {
                    quillBody.insertEmbed(range.index, 'image', imageUrl, 'user');
                    // 이미지 뒤에 줄바꿈 추가
                    quillBody.setSelection(range.index + 1, 0);
                } catch (err) {
                    console.error('[DMaLab] 이미지 삽입 중 오류:', err);
                }
            };
            reader.readAsDataURL(file);
        }
    };
}

// JSON 스타일 정보를 Quill Delta 형식으로 변환
function styleToQuillDelta(content, style) {
    if (!content) return null;

    const ops = [];
    const lines = content.split('\n');
    
    lines.forEach((line, lineIndex) => {
        if (lineIndex > 0) {
            ops.push({ insert: '\n' });
        }

        if (line.trim()) {
            const op = { insert: line };
            
            // 스타일 속성을 class로 변환
            const classes = [];
            const attributes = {};

            if (style) {
                if (style.font_size) {
                    attributes.size = getQuillSize(style.font_size);
                }
                if (style.color) {
                    attributes.color = style.color;
                }
                if (style.background) {
                    attributes.background = style.background;
                }
                if (style.bold) {
                    attributes.bold = true;
                }
                if (style.italic) {
                    attributes.italic = true;
                }
                if (style.underline) {
                    attributes.underline = true;
                }
                if (style.quote) {
                    attributes.blockquote = true;
                }
            }

            if (Object.keys(attributes).length > 0) {
                op.attributes = attributes;
            }

            ops.push(op);
        }
    });

    return { ops };
}

// 폰트 크기를 Quill size로 변환 (네이버 에디터 기준)
function getQuillSize(fontSize) {
    // 네이버 에디터 기준 폰트 크기로 매핑
    const sizeMap = {
        11: '11px',
        13: '13px',
        15: '15px',
        16: '16px',
        19: '19px',
        24: '24px',
        28: '28px',
        30: '30px',
        34: '34px',
        38: '38px'
    };
    
    // 가장 가까운 크기 찾기
    const sizes = Object.keys(sizeMap).map(Number).sort((a, b) => a - b);
    let closestSize = 16; // 기본값
    
    for (let i = 0; i < sizes.length; i++) {
        if (fontSize <= sizes[i]) {
            closestSize = sizes[i];
            break;
        }
        closestSize = sizes[i];
    }
    
    return sizeMap[closestSize] || '16px';
}

// Quill Delta를 JSON 스타일 형식으로 변환
function quillDeltaToStyle(delta) {
    if (!delta || !delta.ops) return { content: '', style: {} };

    let content = '';
    const style = {
        font_size: 16,
        color: null,
        background: null,
        bold: false,
        italic: false,
        underline: false,
        quote: false
    };

    // 첫 번째 op의 스타일 정보 추출
    const firstOp = delta.ops.find(op => op.insert && typeof op.insert === 'string' && op.insert.trim());
    if (firstOp && firstOp.attributes) {
        const attrs = firstOp.attributes;
        
        if (attrs.size) {
            style.font_size = getFontSizeFromQuillSize(attrs.size);
        }
        if (attrs.color) {
            style.color = attrs.color;
        }
        if (attrs.background) {
            style.background = attrs.background;
        }
        if (attrs.bold) {
            style.bold = true;
        }
        if (attrs.italic) {
            style.italic = true;
        }
        if (attrs.underline) {
            style.underline = true;
        }
        if (attrs.blockquote) {
            style.quote = true;
        }
    }

    // 전체 텍스트 추출
    delta.ops.forEach(op => {
        if (typeof op.insert === 'string') {
            content += op.insert;
        } else if (op.insert && op.insert.image) {
            // 이미지는 placeholder로 처리
            content += '[이미지]\n';
        }
    });

    return { content: content.trim(), style };
}

// Quill size를 폰트 크기로 변환 (네이버 에디터 기준)
function getFontSizeFromQuillSize(size) {
    if (!size) return 16; // 기본값
    
    // '11px', '13px' 등의 형식에서 숫자만 추출
    const match = size.match(/(\d+)px/);
    if (match) {
        return parseInt(match[1], 10);
    }
    
    // 기존 매핑 (하위 호환성)
    const sizeMap = {
        'small': 13,
        'large': 19,
        'huge': 24
    };
    return sizeMap[size] || 16;
}

// JSON 블로그 콘텐츠를 Quill 에디터에 로드
function loadBlogContentToQuill(content) {
    if (!content) return;

    // 에디터 초기화 확인
    if (!quillTitle || !quillBody || !quillTags) {
        window._isLoadingBlogContent = true; // 콘텐츠 로딩 중 플래그 설정
        initializeQuillEditors();
        // 초기화 후 약간의 지연을 두고 로드
        setTimeout(() => {
            loadBlogContentToQuill(content);
        }, 200);
        return;
    }
    
    // 새 콘텐츠 로드 시 기존 저장된 내용은 덮어쓰기 (블로그 생성 시)
    window._isLoadingBlogContent = true; // 콘텐츠 로딩 중 플래그 설정

    // 제목 로드
    if (content.title) {
        const titleDelta = styleToQuillDelta(content.title.content, content.title.style);
        if (titleDelta) {
            quillTitle.setContents(titleDelta);
        }
    }

    // 본문을 Delta 형식으로 구성
    const bodyOps = [];
    const generatedImages = content.generated_images || [];
    let globalImageIndex = 1;

    // 서론
    if (content.introduction) {
        const introDelta = styleToQuillDelta(content.introduction.content, content.introduction.style);
        if (introDelta && introDelta.ops) {
            bodyOps.push(...introDelta.ops);
            bodyOps.push({ insert: '\n\n' });
        }
    }

    // 본문 섹션들
    if (content.body && Array.isArray(content.body)) {
        content.body.forEach((section, sectionIdx) => {
            // 섹션 간 구분선 (첫 섹션이 아니면)
            if (sectionIdx > 0) {
                bodyOps.push({ insert: '\n' });
            }

            // 부제목: JSON의 subtitle을 항상 소제목(H2) 스타일로 강제 삽입
            if (section.subtitle && section.subtitle.content) {
                const sub = section.subtitle;
                const text = sub.content || '';
                const style = sub.style || {};

                const attrs = {};
                if (style.font_size) {
                    attrs.size = getQuillSize(style.font_size);
                }
                if (style.color) {
                    attrs.color = style.color;
                }
                if (style.background) {
                    attrs.background = style.background;
                }
                if (style.bold !== false) {
                    // 소제목은 기본적으로 굵게
                    attrs.bold = true;
                }

                if (text) {
                    if (Object.keys(attrs).length > 0) {
                        bodyOps.push({ insert: text, attributes: attrs });
                    } else {
                        bodyOps.push({ insert: text });
                    }
                    // 줄바꿈에 header:2 적용 (Quill 블록 포맷 규칙)
                    bodyOps.push({ insert: '\n', attributes: { header: 2 } });
                    // 소제목과 다음 본문 사이에 한 줄 여백
                    bodyOps.push({ insert: '\n' });
                }
            }

            // 블록들
            if (section.blocks && Array.isArray(section.blocks)) {
                section.blocks.forEach((block) => {
                    if (block.type === 'paragraph') {
                        const paraDelta = styleToQuillDelta(block.content, block.style);
                        if (paraDelta && paraDelta.ops) {
                            bodyOps.push(...paraDelta.ops);
                            bodyOps.push({ insert: '\n\n' });
                        }
                    } else if (block.type === 'quote') {
                        const quoteDelta = styleToQuillDelta(block.content, block.style);
                        if (quoteDelta && quoteDelta.ops) {
                            quoteDelta.ops.forEach(op => {
                                if (op.insert && typeof op.insert === 'string') {
                                    if (!op.attributes) op.attributes = {};
                                    op.attributes.blockquote = true;
                                }
                            });
                            bodyOps.push(...quoteDelta.ops);
                            bodyOps.push({ insert: '\n\n' });
                        }
                    } else if (block.type === 'list') {
                        if (block.items && Array.isArray(block.items)) {
                            block.items.forEach(item => {
                                bodyOps.push({ insert: item });
                                if (block.style) {
                                    const attrs = {};
                                    if (block.style.font_size) {
                                        attrs.size = getQuillSize(block.style.font_size);
                                    }
                                    if (block.style.color) {
                                        attrs.color = block.style.color;
                                    }
                                    if (block.style.bold) attrs.bold = true;
                                    if (block.style.italic) attrs.italic = true;
                                    if (Object.keys(attrs).length > 0) {
                                        bodyOps[bodyOps.length - 1].attributes = attrs;
                                    }
                                }
                                bodyOps.push({ insert: '\n', attributes: { list: 'bullet' } });
                            });
                        }
                        bodyOps.push({ insert: '\n' });
                    } else if (block.type === 'image_placeholder') {
                        const imageInfo = generatedImages.find(img => 
                            img.index === globalImageIndex || 
                            img.placeholder === block.placeholder
                        );
                        
                        if (imageInfo && imageInfo.image_path) {
                            // 이미지 URL 구성
                            let normalizedPath = imageInfo.image_path.replace(/\\/g, '/');
                            
                            // 상대 경로인 경우 절대 경로로 변환
                            let imageUrl;
                            if (normalizedPath.startsWith('http://') || normalizedPath.startsWith('https://')) {
                                // 이미 절대 URL인 경우
                                imageUrl = normalizedPath;
                            } else if (normalizedPath.startsWith('/static/')) {
                                // /static/로 시작하는 경우
                                imageUrl = `${API_BASE_URL}${normalizedPath}`;
                            } else {
                                // 상대 경로인 경우
                                imageUrl = `${API_BASE_URL}/static/blog/create_naver/${normalizedPath}`;
                            }
                            
                            console.log('[이미지 삽입]', {
                                imageInfo,
                                normalizedPath,
                                imageUrl,
                                globalImageIndex
                            });

                            // 이미지 스타일/썸네일 상태 복원 (export된 JSON에서도 토글 UI가 반영되도록)
                            try {
                                window.imageStyleMap = window.imageStyleMap || {};
                                window.imageThumbnailMap = window.imageThumbnailMap || {};
                                if (imageInfo.style) {
                                    window.imageStyleMap[imageUrl] = imageInfo.style;
                                }
                                if (imageInfo.is_thumbnail) {
                                    window.imageThumbnailMap[imageUrl] = true;
                                }
                            } catch (e) {
                                console.warn('[DMaLab] 이미지 스타일/썸네일 복원 중 오류:', e);
                            }

                            // 이미지 설명(캡션) 기본값을 GPT placeholder(접미사 제거 버전)로 설정
                            try {
                                const rawPlaceholder = block.placeholder || '[이미지 삽입]';
                                const normalizedPlaceholder = normalizeImagePlaceholderText(rawPlaceholder);
                                window.imageCaptionMap = window.imageCaptionMap || {};
                                window.imageCaptionMap[imageUrl] = normalizedPlaceholder;
                            } catch (e) {
                                console.warn('[DMaLab] 이미지 캡션 초기화 중 오류:', e);
                            }
                            
                            // Quill에 이미지 삽입
                            bodyOps.push({ insert: { image: imageUrl } });
                            bodyOps.push({ insert: '\n\n' });
                        } else {
                            // 플레이스홀더 텍스트 (접미사 "_이미지 삽입1" 등 제거)
                            const rawPlaceholder = block.placeholder || '[이미지 삽입]';
                            const normalizedPlaceholder = normalizeImagePlaceholderText(rawPlaceholder);
                            const placeholderDelta = styleToQuillDelta(normalizedPlaceholder, block.style);
                            if (placeholderDelta && placeholderDelta.ops) {
                                bodyOps.push(...placeholderDelta.ops);
                                bodyOps.push({ insert: '\n\n' });
                            }
                        }
                        globalImageIndex++;
                    } else if (block.type === 'hr') {
                        bodyOps.push({ insert: '\n' });
                        // Quill은 hr을 직접 지원하지 않으므로 구분선으로 표시
                        bodyOps.push({ insert: '---\n\n' });
                    }
                });
            }
        });
    }

    // 결론
    if (content.conclusion) {
        const conclusionDelta = styleToQuillDelta(content.conclusion.content, content.conclusion.style);
        if (conclusionDelta && conclusionDelta.ops) {
            bodyOps.push({ insert: '\n' });
            bodyOps.push(...conclusionDelta.ops);
            bodyOps.push({ insert: '\n\n' });
        }
    }

    // FAQ
    if (content.faq && Array.isArray(content.faq) && content.faq.length > 0) {
        bodyOps.push({ insert: '자주 묻는 질문\n\n', attributes: { header: 2, bold: true } });
        content.faq.forEach((faq) => {
            if (faq.q) {
                const qDelta = styleToQuillDelta('Q: ' + faq.q.content, faq.q.style);
                if (qDelta && qDelta.ops) {
                    qDelta.ops.forEach(op => {
                        if (op.insert && typeof op.insert === 'string' && !op.attributes) {
                            op.attributes = { bold: true };
                        }
                    });
                    bodyOps.push(...qDelta.ops);
                    bodyOps.push({ insert: '\n' });
                }
            }
            if (faq.a) {
                const aDelta = styleToQuillDelta('A: ' + faq.a.content, faq.a.style);
                if (aDelta && aDelta.ops) {
                    bodyOps.push(...aDelta.ops);
                    bodyOps.push({ insert: '\n\n' });
                }
            }
        });
    }

    // 외부 링크를 에디터 하단에 배치 (서브타이틀 없이 링크만)
    if (content.external_links && Array.isArray(content.external_links) && content.external_links.length > 0) {
        bodyOps.push({ insert: '\n\n' });
        content.external_links.forEach((link, index) => {
            if (link && link.trim()) {
                // 링크를 클릭 가능한 형태로 삽입
                bodyOps.push({ 
                    insert: link, 
                    attributes: { 
                        link: link,
                        color: '#0066cc'
                    } 
                });
                bodyOps.push({ insert: '\n' });
            }
        });
    }

    // 본문을 Quill에 설정
    quillBody.setContents({ ops: bodyOps });
    
    // 콘텐츠 로드 후 자동 저장 및 높이 재계산
    setTimeout(() => {
        saveEditorContent();
        window._isLoadingBlogContent = false; // 콘텐츠 로딩 완료
        // 높이 재계산
        sendHeightToParent();
    }, 100);

    // 태그 로드
    if (content.tags && Array.isArray(content.tags) && content.tags.length > 0) {
        quillTags.setText(content.tags.join(', '));
    }
}

// Quill 에디터 내용을 JSON 형식으로 변환
function quillContentToJSON() {
    if (!quillTitle || !quillBody || !quillTags) {
        return null;
    }

    const titleDelta = quillTitle.getContents();
    const bodyDelta = quillBody.getContents();
    
    // 본문 Delta를 줄 단위로 분해
    const bodyOps = (bodyDelta && bodyDelta.ops) || [];
    const lines = []; // { type: 'text'|'image', delta?, attrs?, src? }
    let currentLineOps = [];
    
    bodyOps.forEach(op => {
        if (typeof op.insert === 'string') {
            if (op.insert === '\n') {
                // 줄 종료 (블록 속성 포함)
                lines.push({
                    type: 'text',
                    delta: { ops: currentLineOps },
                    attrs: op.attributes || {}
                });
                currentLineOps = [];
            } else if (op.insert.includes('\n')) {
                const parts = op.insert.split('\n');
                parts.forEach((part, idx) => {
                    if (part.length > 0) {
                        currentLineOps.push({
                            insert: part,
                            attributes: op.attributes
                        });
                    }
                    if (idx < parts.length - 1) {
                        lines.push({
                            type: 'text',
                            delta: { ops: currentLineOps },
                            attrs: op.attributes || {}
                        });
                        currentLineOps = [];
                    }
                });
            } else {
                currentLineOps.push(op);
            }
        } else if (op.insert && op.insert.image) {
            // 이전에 쌓인 텍스트 라인 flush
            if (currentLineOps.length > 0) {
                lines.push({
                    type: 'text',
                    delta: { ops: currentLineOps },
                    attrs: {}
                });
                currentLineOps = [];
            }
            
            lines.push({
                type: 'image',
                src: op.insert.image,
                attrs: op.attributes || {}
            });
        }
    });
    
    // 마지막 라인 flush
    if (currentLineOps.length > 0) {
        lines.push({
            type: 'text',
            delta: { ops: currentLineOps },
            attrs: {}
        });
    }
    
    // 섹션 구성: header=2 는 소제목, 그 외는 paragraph
    const body = [];
    let currentSection = null;
    let imageIndex = 1;
    
    const ensureDefaultSection = () => {
        if (!currentSection) {
            currentSection = {
                // 기본 섹션은 실제로 보이는 소제목 텍스트를 넣지 않음
                subtitle: {
                    content: '',
                    style: { font_size: 20, bold: true }
                },
                blocks: []
            };
            body.push(currentSection);
        }
    };
    
    let currentListBlock = null;

    const flushCurrentList = () => {
        if (currentListBlock && currentSection) {
            currentSection.blocks.push(currentListBlock);
        }
        currentListBlock = null;
    };

    lines.forEach(line => {
        if (line.type === 'image') {
            flushCurrentList();
            ensureDefaultSection();
            const src = line.src || '';
            const caption = (window.imageCaptionMap && window.imageCaptionMap[src]) || '';
            const placeholder = caption || `[이미지 ${imageIndex}]`;
            
            currentSection.blocks.push({
                type: 'image_placeholder',
                placeholder: placeholder,
                image_prompt: '',
                index: imageIndex
            });
            imageIndex++;
        } else if (line.type === 'text' && line.delta && line.delta.ops && line.delta.ops.length > 0) {
            const lineData = quillDeltaToStyle(line.delta);
            if (!lineData.content) {
                return;
            }
            
            const isHeader2 = line.attrs && line.attrs.header === 2;
            const isList = line.attrs && (line.attrs.list === 'bullet' || line.attrs.list === 'ordered');
            
            if (isHeader2) {
                // 소제목 시작 전에 열려 있는 리스트가 있으면 먼저 flush
                flushCurrentList();
                currentSection = {
                    subtitle: {
                        content: lineData.content,
                        style: Object.assign({}, lineData.style, { bold: true })
                    },
                    blocks: []
                };
                body.push(currentSection);
            } else if (isList) {
                ensureDefaultSection();
                const style = Object.assign({}, lineData.style);
                const listType = line.attrs.list === 'ordered' ? 'ordered' : 'bullet';

                if (!currentListBlock) {
                    currentListBlock = {
                        type: 'list',
                        items: [],
                        style: style,
                        ordered: listType === 'ordered'
                    };
                }
                currentListBlock.items.push(lineData.content);
            } else {
                // 일반 문단/인용구
                ensureDefaultSection();
                const style = Object.assign({}, lineData.style);
                if (line.attrs && line.attrs.blockquote) {
                    style.quote = true;
                }
                // 리스트가 열려 있었다면 여기서 마무리
                flushCurrentList();
                currentSection.blocks.push({
                    type: 'paragraph',
                    content: lineData.content,
                    style: style
                });
            }
        }
    });

    // 마지막에 열려 있는 리스트 flush
    flushCurrentList();

    // 제목
    const titleData = quillDeltaToStyle(titleDelta);
    const title = {
        content: titleData.content,
        style: titleData.style
    };

    // 태그
    const tagsText = quillTags.getText();
    const tags = tagsText.split(',').map(tag => tag.trim()).filter(tag => tag);

    return {
        title: title,
        introduction: { content: '', style: {} },
        body: body,
        conclusion: { content: '', style: {} },
        faq: [],
        tags: tags
    };
}

