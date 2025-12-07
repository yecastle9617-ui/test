const API_BASE_URL = 'http://localhost:8000';

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

// 페이지 로드 시 카테고리 선택기 초기화
// 스크립트가 body 끝에 있으므로 DOM이 이미 로드되어 있을 수 있음
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initCategorySelector();
            initExternalLinksUI();
            initReferenceBlogsUI();
        });
    } else {
        // DOM이 이미 로드된 경우 즉시 실행
        setTimeout(function() {
            initCategorySelector();
            initExternalLinksUI();
            initReferenceBlogsUI();
        }, 100); // 약간의 지연으로 DOM이 완전히 준비되도록
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
        
        // 모든 탭 버튼과 콘텐츠 비활성화
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // 선택한 탭 활성화
        btn.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// 로딩 표시
function showLoading(message = '처리 중...') {
    const loadingDiv = document.getElementById('loading');
    const loadingMessage = document.getElementById('loading-message');
    const loadingSteps = document.getElementById('loading-steps');
    
    if (loadingDiv) {
        loadingDiv.style.display = 'block';
        if (loadingMessage) {
            loadingMessage.textContent = message;
        }
        if (loadingSteps) {
            loadingSteps.innerHTML = '';
        }
    }
    document.getElementById('error').style.display = 'none';
    document.getElementById('result').style.display = 'none';
}

function updateLoadingStep(step, status = 'pending') {
    // status: 'pending', 'processing', 'completed', 'error'
    const loadingSteps = document.getElementById('loading-steps');
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
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

// 에러 표시
function showError(message) {
    document.getElementById('error').style.display = 'block';
    document.getElementById('error').textContent = '오류: ' + message;
}

// 결과 표시
function showResult(data, type = 'default') {
    const resultDiv = document.getElementById('result');
    const resultContent = document.getElementById('result-content');
    
    resultDiv.style.display = 'block';
    
    // 타입에 따라 다른 렌더링
    switch(type) {
        case 'process':
            if (resultContent) {
            resultContent.innerHTML = renderProcessResult(data);
            }
            break;
        case 'generate':
            // 제목, 본문, 태그로 분리된 에디터에 렌더링
            renderBlogContentSeparated(data.blog_content || data);
            // 현재 블로그 콘텐츠 저장 (복사 기능용)
            window.currentBlogContent = data.blog_content || data;
            break;
        default:
            // JSON 표시는 pre 태그 사용
            if (resultContent) {
            resultContent.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
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
        <p class="output-dir"><strong>출력 디렉토리:</strong> ${data.output_dir}</p>
    </div>`;
    
    if (data.results && data.results.length > 0) {
        html += '<div class="process-results-list">';
        data.results.forEach((result, index) => {
            html += `
                <div class="process-result-card ${result.success ? 'success' : 'error'}">
                    <div class="result-card-header">
                        <span class="result-rank">TOP ${result.rank}</span>
                        <span class="result-status-badge ${result.success ? 'success' : 'error'}">
                            ${result.success ? '✅ 성공' : '❌ 실패'}
                        </span>
                    </div>
                    <div class="result-card-body">
                        <h4 class="result-title">${escapeHtml(result.title)}</h4>
                        <p><strong>URL:</strong> <a href="${result.url}" target="_blank">${result.url}</a></p>
                        ${result.body_length ? `<p><strong>본문 길이:</strong> ${result.body_length.toLocaleString()}자</p>` : ''}
                        ${result.txt_path ? `<p><strong>TXT 파일:</strong> ${result.txt_path}</p>` : ''}
                        ${result.excel_path ? `<p><strong>엑셀 파일:</strong> ${result.excel_path}</p>` : ''}
                        ${result.keywords && result.keywords.length > 0 ? `
                            <div class="keywords-preview">
                                <strong>주요 키워드:</strong>
                                <div class="keyword-tags">
                                    ${result.keywords.slice(0, 10).map(k => `<span class="keyword-tag">${escapeHtml(k.keyword)} (${k.count})</span>`).join('')}
                                </div>
                            </div>
                        ` : ''}
                        ${result.image_urls && result.image_urls.length > 0 ? `
                            <div class="images-container" style="margin-top: 20px;">
                                <h4 style="margin-bottom: 15px; color: #333;">이미지 (${result.image_urls.length}개)</h4>
                                <div class="images-grid">
                                    ${result.image_urls.map((imgUrl, idx) => {
                                        // output_dir이 있으면 전달 (process 결과인 경우)
                                        const outputDir = data.output_dir ? `${data.output_dir}/TOP${result.rank}` : null;
                                        const proxyUrl = getProxyImageUrl(imgUrl, outputDir);
                                        const originalUrl = imgUrl.startsWith('/') ? imgUrl : imgUrl.split('?url=')[1] ? decodeURIComponent(imgUrl.split('?url=')[1].split('&')[0]) : imgUrl;
                                        return `
                                        <div class="image-item">
                                            <img src="${proxyUrl}" 
                                                 alt="이미지 ${idx + 1}" 
                                                 loading="lazy"
                                                 data-original-url="${escapeHtml(originalUrl)}"
                                                 onerror="console.error('이미지 로드 실패:', '${originalUrl}'); this.style.display='none'; this.nextElementSibling.style.display='block';"
                                                 onload="console.log('이미지 로드 성공:', '${originalUrl}');">
                                            <div class="image-error" style="display: none;">이미지를 불러올 수 없습니다<br><small>${escapeHtml(originalUrl)}</small></div>
                                            <a href="${originalUrl}" target="_blank" class="image-link">원본 보기</a>
                                        </div>
                                    `;
                                    }).join('')}
                                </div>
                            </div>
                        ` : ''}
                        ${result.link_urls && result.link_urls.length > 0 ? `
                            <div class="links-container" style="margin-top: 15px;">
                                <h4 style="margin-bottom: 10px; color: #333;">링크 (${result.link_urls.length}개)</h4>
                                <div class="links-list">
                                    ${result.link_urls.map((linkUrl, idx) => `
                                        <div class="link-item">
                                            <a href="${linkUrl}" target="_blank">${escapeHtml(linkUrl)}</a>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        ${result.body_text && result.body_text.trim() ? `
                            <div class="body-text-container" style="margin-top: 20px;">
                                <h4 style="margin-bottom: 15px; color: #333;">본문 내용</h4>
                                <div class="body-text">${formatText(String(result.body_text).trim())}</div>
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

    showLoading('전체 처리 시작...');
    updateLoadingStep('블로그 검색 중', 'processing');

    try {
        const response = await fetch(`${API_BASE_URL}/api/process`, {
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

        updateLoadingStep('블로그 검색 중', 'completed');
        updateLoadingStep('블로그 크롤링 중', 'processing');

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '처리 실패');
        }

        updateLoadingStep('블로그 크롤링 중', 'completed');
        
        if (analyze) {
            updateLoadingStep('키워드 분석 중', 'processing');
            setTimeout(() => {
                updateLoadingStep('키워드 분석 중', 'completed');
                showLoading('완료!');
                setTimeout(() => {
                    showResult(data, 'process');
                }, 500);
            }, 500);
        } else {
            showLoading('완료!');
            setTimeout(() => {
                showResult(data, 'process');
            }, 500);
        }
    } catch (error) {
        showError(error.message);
        hideLoading();
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

    showLoading('블로그 생성 시작...');

    try {
        const banWordsList = banWords ? banWords.split(',').map(w => w.trim()).filter(w => w) : null;

        // 단계별 진행 상황 표시
        if (useAutoReference || (manualReferenceUrls && manualReferenceUrls.length > 0)) {
            updateLoadingStep('상위 블로그 분석 중', 'processing');
        }
        
        updateLoadingStep('블로그 글 생성 중', 'processing');

        const response = await fetch(`${API_BASE_URL}/api/generate-blog`, {
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
                save_json: true
            })
        });

        // 상위 블로그 분석 완료
        if (useAutoReference || (manualReferenceUrls && manualReferenceUrls.length > 0)) {
            updateLoadingStep('상위 블로그 분석 중', 'completed');
        }

        // 블로그 글 생성 완료
        updateLoadingStep('블로그 글 생성 중', 'completed');

        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || '블로그 생성 실패');
        }

        // 이미지 생성 단계 표시 (체크박스가 활성화된 경우만)
        if (generateImages && data.blog_content && data.blog_content.generated_images && data.blog_content.generated_images.length > 0) {
            const imageCount = data.blog_content.generated_images.length;
            updateLoadingStep(`이미지 생성 중 (${imageCount}개)`, 'processing');
            
            // 이미지 생성은 백엔드에서 이미 완료되었으므로 완료로 표시
            setTimeout(() => {
                updateLoadingStep(`이미지 생성 중 (${imageCount}개)`, 'completed');
            }, 500);
        } else if (generateImages) {
            // 이미지 생성이 활성화되었지만 생성된 이미지가 없는 경우 (플레이스홀더가 없거나 생성 실패)
            const imagePlaceholders = data.blog_content?.body?.flatMap(section => 
                section.blocks?.filter(block => block.type === 'image_placeholder') || []
            ) || [];
            if (imagePlaceholders.length > 0) {
                updateLoadingStep('이미지 생성 중', 'processing');
                setTimeout(() => {
                    updateLoadingStep('이미지 생성 중', 'completed');
                }, 500);
            }
        }

        // 저장 중
        updateLoadingStep('파일 저장 중', 'processing');
        
        if (data.json_path) {
            updateLoadingStep('파일 저장 중', 'completed');
        }

        // 완료 메시지
        setTimeout(() => {
            showLoading('완료!');
            setTimeout(() => {
                hideLoading();
                showResult(data, 'generate');
            }, 500);
        }, 1000);

    } catch (error) {
        showError(error.message);
        hideLoading();
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
                        html += `<div ${applyStyle(block.style)}>${escapeHtml(block.placeholder || '[이미지 삽입]')}</div>`;
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

// 블로그 콘텐츠를 제목, 본문, 태그로 분리하여 렌더링
function renderBlogContentSeparated(content) {
    if (!content) return;

    const applyStyle = (style) => {
        if (!style) return '';
        let css = '';
        if (style.font_size) css += `font-size: ${style.font_size}px; `;
        if (style.color) {
            css += `color: ${style.color}; `;
        } else {
            css += 'color: #333333; ';
        }
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
            if (!style.color) {
                css += 'color: #333333; ';
            }
        }
        return css ? `style="${css}"` : '';
    };

    // 제목 영역
    const titleDiv = document.getElementById('result-title');
    if (titleDiv) {
        if (content.title) {
            titleDiv.innerHTML = `<h1 ${applyStyle(content.title.style)}>${escapeHtml(content.title.content)}</h1>`;
        } else {
            titleDiv.innerHTML = '';
        }
    }

    // 본문 영역 (서론 + 본문 + 결론 + FAQ)
    const bodyDiv = document.getElementById('result-body');
    if (bodyDiv) {
        let bodyHtml = '<div class="blog-content">';

        // 서론
        if (content.introduction) {
            bodyHtml += `<div ${applyStyle(content.introduction.style)}>${escapeHtml(content.introduction.content).replace(/\n/g, '<br>')}</div>`;
        }

        // 본문
        if (content.body && Array.isArray(content.body)) {
            bodyHtml += '<div class="blog-body">';
            
            // 이미지 플레이스홀더 인덱스 추적 (전체 본문에서 순차적으로)
            let globalImageIndex = 1;
            const generatedImages = content.generated_images || [];
            
            content.body.forEach((section, sectionIdx) => {
                bodyHtml += '<div class="blog-section">';
                
                // 부제목
                if (section.subtitle) {
                    bodyHtml += `<h2 ${applyStyle(section.subtitle.style)}>${escapeHtml(section.subtitle.content)}</h2>`;
                }

                // 블록들
                if (section.blocks && Array.isArray(section.blocks)) {
                    bodyHtml += '<div class="blog-blocks">';
                    section.blocks.forEach((block, blockIdx) => {
                        if (block.type === 'paragraph') {
                            bodyHtml += `<p ${applyStyle(block.style)}>${escapeHtml(block.content).replace(/\n/g, '<br>')}</p>`;
                        } else if (block.type === 'quote') {
                            bodyHtml += `<blockquote ${applyStyle(block.style)}>${escapeHtml(block.content).replace(/\n/g, '<br>')}</blockquote>`;
                        } else if (block.type === 'list') {
                            bodyHtml += `<ul ${applyStyle(block.style)}>`;
                            if (block.items && Array.isArray(block.items)) {
                                block.items.forEach(item => {
                                    bodyHtml += `<li>${escapeHtml(item)}</li>`;
                                });
                            }
                            bodyHtml += '</ul>';
                        } else if (block.type === 'image_placeholder') {
                            // 생성된 이미지가 있는지 확인 (placeholder 또는 index로 매칭)
                            const imageInfo = generatedImages.find(img => 
                                img.index === globalImageIndex || 
                                img.placeholder === block.placeholder
                            );
                            
                            if (imageInfo && imageInfo.image_path) {
                                // 이미지 URL 구성 (정적 파일 경로)
                                // 백슬래시를 슬래시로 변환 (Windows 경로 대응)
                                const normalizedPath = imageInfo.image_path.replace(/\\/g, '/');
                                const imageUrl = `${API_BASE_URL}/static/blog/create_naver/${normalizedPath}`;
                                // 파일명 추출 (경로에서 마지막 부분만)
                                const pathParts = normalizedPath.split('/');
                                const actualFilename = pathParts[pathParts.length - 1] || (escapeHtml(block.placeholder.replace(/[^a-zA-Z0-9가-힣]/g, '_')) + '.png');
                                const safeFilename = actualFilename;
                                bodyHtml += `
                                    <div class="generated-image-container" style="margin: 20px 0;">
                                        <img src="${imageUrl}" alt="${escapeHtml(block.placeholder)}" 
                                             style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; display: block; margin: 10px 0;" 
                                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                                        <div style="display: none; padding: 10px; background: #f5f5f5; border-radius: 4px; color: #666;">
                                            이미지를 불러올 수 없습니다: ${escapeHtml(block.placeholder)}
                                        </div>
                                        <div style="margin-top: 8px; display: flex; gap: 8px; align-items: center;">
                                            <button onclick="downloadImage('${imageUrl}', '${safeFilename}')" 
                                                    class="btn-secondary-small" 
                                                    style="padding: 4px 12px; font-size: 12px;">
                                                📥 이미지 다운로드
                                            </button>
                                            <span style="font-size: 12px; color: #999; font-style: italic;">
                                                ${escapeHtml(block.placeholder)}
                                            </span>
                                        </div>
                                    </div>
                                `;
                            } else {
                                // 이미지가 생성되지 않은 경우 플레이스홀더만 표시
                                bodyHtml += `<div ${applyStyle(block.style)}>${escapeHtml(block.placeholder || '[이미지 삽입]')}</div>`;
                            }
                            
                            // 이미지 플레이스홀더를 만날 때마다 인덱스 증가
                            globalImageIndex++;
                        } else if (block.type === 'hr') {
                            bodyHtml += `<hr ${applyStyle(block.style)}>`;
                        }
                    });
                    bodyHtml += '</div>';
                }

                bodyHtml += '</div>';
            });
            bodyHtml += '</div>';
        }

        // 결론
        if (content.conclusion) {
            bodyHtml += `<div ${applyStyle(content.conclusion.style)}>${escapeHtml(content.conclusion.content).replace(/\n/g, '<br>')}</div>`;
        }

        // FAQ
        if (content.faq && Array.isArray(content.faq) && content.faq.length > 0) {
            bodyHtml += '<div class="blog-faq"><h2>자주 묻는 질문</h2>';
            content.faq.forEach((faq, faqIdx) => {
                bodyHtml += '<div class="faq-item">';
                if (faq.q) {
                    bodyHtml += `<h3 ${applyStyle(faq.q.style)}>Q: ${escapeHtml(faq.q.content)}</h3>`;
                }
                if (faq.a) {
                    bodyHtml += `<p ${applyStyle(faq.a.style)}>A: ${escapeHtml(faq.a.content).replace(/\n/g, '<br>')}</p>`;
                }
                bodyHtml += '</div>';
            });
            bodyHtml += '</div>';
        }

        bodyHtml += '</div>';
        bodyDiv.innerHTML = bodyHtml;
    }

    // 태그 영역 (순수 텍스트로만 표시 - 쉼표로 구분)
    const tagsDiv = document.getElementById('result-tags');
    if (tagsDiv) {
        if (content.tags && Array.isArray(content.tags) && content.tags.length > 0) {
            // HTML 태그 없이 순수 텍스트로만 표시 (편집 시 스타일 깨짐 방지)
            tagsDiv.textContent = content.tags.join(', ');
        } else {
            tagsDiv.textContent = '';
        }
    }
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
    if (!window.currentBlogContent) {
        alert('복사할 내용이 없습니다.');
        return;
    }

    const content = window.currentBlogContent;
    let html = '';

    // 제목
    if (content.title) {
        const titleStyle = applyNaverStyle(content.title.style);
        html += `<div ${titleStyle} style="margin-bottom: 20px;">${escapeHtml(content.title.content)}</div>\n`;
    }

    // 서론
    if (content.introduction) {
        const introStyle = applyNaverStyle(content.introduction.style);
        const introContent = escapeHtml(content.introduction.content).replace(/\n/g, '<br>');
        html += `<div ${introStyle} style="margin-bottom: 25px;">${introContent}</div>\n`;
    }

    // 본문
    if (content.body && Array.isArray(content.body)) {
        content.body.forEach((section, sectionIdx) => {
            // 섹션 시작
            html += '<div>\n';
            
            // 첫 번째 섹션이 아니면 소제목 위에 구분선 추가
            if (sectionIdx > 0) {
                html += '  <hr style="margin: 30px 0 20px 0; border: none; border-top: 2px solid #e0e0e0; background: none; height: 0;">\n';
            }
            
            // 부제목 (단순한 구조로 네이버 에디터 자동 구분선 방지)
            if (section.subtitle) {
                const subtitleStyle = applyNaverStyle(section.subtitle.style, true);
                // 소제목은 단순한 div로 표시 (네이버 에디터가 자동 구분선을 추가하지 않도록)
                // strong, border, padding 등 제거하여 단순한 구조 유지
                html += `  <div ${subtitleStyle}>${escapeHtml(section.subtitle.content)}</div>\n`;
            }

            // 블록들
            if (section.blocks && Array.isArray(section.blocks)) {
                section.blocks.forEach((block, blockIdx) => {
                    if (block.type === 'paragraph') {
                        const blockStyle = applyNaverStyle(block.style);
                        const blockContent = escapeHtml(block.content).replace(/\n/g, '<br>');
                        // 문단별 간격 추가 (margin-bottom)
                        html += `  <div ${blockStyle} style="margin-bottom: 20px; line-height: 1.8;">${blockContent}</div>\n`;
                    } else if (block.type === 'quote') {
                        const quoteStyle = applyNaverStyle(block.style);
                        const quoteContent = escapeHtml(block.content).replace(/\n/g, '<br>');
                        html += `  <blockquote ${quoteStyle} style="margin-bottom: 20px;">${quoteContent}</blockquote>\n`;
                    } else if (block.type === 'list') {
                        const listStyle = applyNaverStyle(block.style);
                        html += `  <ul ${listStyle} style="margin-bottom: 20px; padding-left: 25px; line-height: 1.8;">\n`;
                        if (block.items && Array.isArray(block.items)) {
                            block.items.forEach(item => {
                                const itemStyle = applyNaverStyle(block.style);
                                html += `    <li ${itemStyle} style="margin-bottom: 8px;">${escapeHtml(item)}</li>\n`;
                            });
                        }
                        html += `  </ul>\n`;
                    } else if (block.type === 'image_placeholder') {
                        const imgStyle = applyNaverStyle(block.style);
                        html += `  <div ${imgStyle} style="margin-bottom: 20px; text-align: center;">[ ${escapeHtml(block.placeholder || '이미지 삽입')} ]</div>\n`;
                    } else if (block.type === 'hr') {
                        const hrStyle = applyNaverStyle(block.style);
                        html += `  <hr ${hrStyle} style="margin: 30px 0; border: none; border-top: 2px solid #e0e0e0;">\n`;
                    }
                });
            }

            html += '</div>\n';
        });
    }

    // 결론
    if (content.conclusion) {
        const conclusionStyle = applyNaverStyle(content.conclusion.style);
        const conclusionContent = escapeHtml(content.conclusion.content).replace(/\n/g, '<br>');
        html += `<div ${conclusionStyle} style="margin-top: 30px; margin-bottom: 25px;">${conclusionContent}</div>\n`;
    }

    // FAQ
    if (content.faq && Array.isArray(content.faq) && content.faq.length > 0) {
        html += '<div>\n';
        html += '  <div style="font-size: 18px; font-weight: bold; margin-top: 30px; margin-bottom: 15px; color: #333333; background-color: transparent;">자주 묻는 질문</div>\n';
        content.faq.forEach((faq, faqIdx) => {
            html += '  <div style="margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; border-radius: 8px;">\n';
            if (faq.q) {
                const qStyle = applyNaverStyle(faq.q.style);
                html += `    <div ${qStyle}>Q: ${escapeHtml(faq.q.content)}</div>\n`;
            }
            if (faq.a) {
                const aStyle = applyNaverStyle(faq.a.style);
                const aContent = escapeHtml(faq.a.content).replace(/\n/g, '<br>');
                html += `    <div ${aStyle} style="margin-top: 8px;">A: ${aContent}</div>\n`;
            }
            html += '  </div>\n';
        });
        html += '</div>\n';
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
            alert('✅ 블로그 내용이 클립보드에 복사되었습니다!\n\n네이버 블로그 에디터에서 Ctrl+V (또는 Cmd+V)로 붙여넣으세요.\n스타일이 포함된 HTML 형식으로 복사되었습니다.');
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
            alert('✅ 블로그 내용이 클립보드에 복사되었습니다!\n\n네이버 블로그 에디터에서 붙여넣으세요.');
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

