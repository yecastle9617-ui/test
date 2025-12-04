const API_BASE_URL = 'http://localhost:8000';

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
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';
    document.getElementById('result').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
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
        case 'search':
            resultContent.innerHTML = renderSearchResult(data);
            break;
        case 'crawl':
            resultContent.innerHTML = renderCrawlResult(data);
            break;
        case 'crawl-bulk':
            resultContent.innerHTML = renderCrawlBulkResult(data);
            break;
        case 'analyze':
            resultContent.innerHTML = renderAnalyzeResult(data);
            break;
        case 'process':
            resultContent.innerHTML = renderProcessResult(data);
            break;
        default:
            // JSON 표시는 pre 태그 사용
            resultContent.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }
}

// 검색 결과 렌더링
function renderSearchResult(data) {
    let html = `<div class="result-header">
        <h3>검색 결과</h3>
        <p class="result-summary">키워드: <strong>${data.keyword}</strong> | 발견된 블로그: <strong>${data.count}개</strong></p>
    </div>`;
    
    if (data.blogs && data.blogs.length > 0) {
        html += '<div class="blog-list">';
        data.blogs.forEach((blog, index) => {
            html += `
                <div class="blog-card">
                    <div class="blog-rank">TOP ${index + 1}</div>
                    <div class="blog-content">
                        <h4 class="blog-title">${escapeHtml(blog.title)}</h4>
                        <a href="${blog.url}" target="_blank" class="blog-url">${blog.url}</a>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    return html;
}

// 크롤링 결과 렌더링 (단일)
function renderCrawlResult(data) {
    console.log('renderCrawlResult 데이터:', data); // 디버깅
    
    let html = `<div class="result-header">
        <h3>크롤링 결과</h3>
        <div class="result-status ${data.success ? 'success' : 'error'}">
            ${data.success ? '✅ 성공' : '❌ 실패'}
        </div>
    </div>`;
    
    if (data.success) {
        html += `
            <div class="crawl-info">
                <p><strong>제목:</strong> ${data.title || '제목 없음'}</p>
                <p><strong>URL:</strong> <a href="${data.url}" target="_blank">${data.url}</a></p>
                <p><strong>본문 길이:</strong> ${data.body_length ? data.body_length.toLocaleString() + '자' : 'N/A'}</p>
                ${data.txt_path ? `<p><strong>저장 경로:</strong> ${data.txt_path}</p>` : ''}
            </div>
        `;
        
        // body_text 확인 및 표시
        console.log('renderCrawlResult - body_text 존재 여부:', !!data.body_text);
        console.log('renderCrawlResult - body_text 타입:', typeof data.body_text);
        console.log('renderCrawlResult - body_text 길이:', data.body_text ? data.body_text.length : 0);
        
        if (data.body_text) {
            const bodyText = String(data.body_text).trim();
            console.log('renderCrawlResult - trim 후 길이:', bodyText.length);
            
            if (bodyText.length > 0) {
                const formattedText = formatText(bodyText);
                console.log('renderCrawlResult - 포맷팅된 텍스트 길이:', formattedText.length);
                
                html += `
                    <div class="body-text-container">
                        <h4>본문 내용</h4>
                        <div class="body-text">${formattedText}</div>
                    </div>
                `;
            } else {
                html += `<div class="body-text-container"><p class="no-content">본문 내용이 비어있습니다.</p></div>`;
            }
        } else {
            html += `<div class="body-text-container"><p class="no-content">본문 내용이 없습니다. (body_text가 응답에 포함되지 않았습니다)</p></div>`;
        }
    } else {
        html += `<div class="error-message">${escapeHtml(data.error || '알 수 없는 오류')}</div>`;
    }
    
    return html;
}

// 크롤링 결과 렌더링 (리스트)
function renderCrawlBulkResult(data) {
    let html = `<div class="result-header">
        <h3>크롤링 결과 (리스트)</h3>
        <p class="result-summary">전체: <strong>${data.total_count}개</strong> | 성공: <strong>${data.success_count}개</strong> | 실패: <strong>${data.total_count - data.success_count}개</strong></p>
    </div>`;
    
    if (data.results && data.results.length > 0) {
        html += '<div class="crawl-results-list">';
        data.results.forEach((result, index) => {
            html += `
                <div class="crawl-result-card ${result.success ? 'success' : 'error'}">
                    <div class="result-card-header">
                        <span class="result-index">#${index + 1}</span>
                        <span class="result-status-badge ${result.success ? 'success' : 'error'}">
                            ${result.success ? '✅ 성공' : '❌ 실패'}
                        </span>
                    </div>
                    <div class="result-card-body">
                        <p><strong>제목:</strong> ${escapeHtml(result.title || 'N/A')}</p>
                        <p><strong>URL:</strong> <a href="${result.url}" target="_blank">${result.url}</a></p>
                        ${result.body_length ? `<p><strong>본문 길이:</strong> ${result.body_length.toLocaleString()}자</p>` : ''}
                        ${result.body_text && result.body_text.trim() ? `
                            <div class="body-text-container" style="margin-top: 15px;">
                                <h4 style="margin-bottom: 10px; color: #333; font-size: 1rem;">본문 내용</h4>
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

// 키워드 분석 결과 렌더링
function renderAnalyzeResult(data) {
    let html = `<div class="result-header">
        <h3>키워드 분석 결과</h3>
        <p class="result-summary">${data.success ? `총 <strong>${data.total_keywords}개</strong>의 키워드가 발견되었습니다.` : '분석 실패'}</p>
    </div>`;
    
    if (data.success && data.keywords && data.keywords.length > 0) {
        html += '<div class="keyword-table-container"><table class="keyword-table"><thead><tr><th>순위</th><th>키워드</th><th>출현 횟수</th></tr></thead><tbody>';
        
        data.keywords.forEach(keyword => {
            html += `
                <tr>
                    <td class="rank-cell">${keyword.rank}</td>
                    <td class="keyword-cell"><strong>${escapeHtml(keyword.keyword)}</strong></td>
                    <td class="count-cell">${keyword.count}회</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        
        if (data.excel_path) {
            html += `<p class="excel-path"><strong>엑셀 파일:</strong> ${data.excel_path}</p>`;
        }
    } else if (data.error) {
        html += `<div class="error-message">${escapeHtml(data.error)}</div>`;
    }
    
    return html;
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

// 검색
async function handleSearch() {
    const keyword = document.getElementById('search-keyword').value.trim();
    const count = parseInt(document.getElementById('search-count').value);

    if (!keyword) {
        alert('검색 키워드를 입력하세요.');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: keyword,
                n: count
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '검색 실패');
        }

        showResult(data, 'search');
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// 크롤링 (단일)
async function handleCrawl() {
    const url = document.getElementById('crawl-url').value.trim();
    const title = document.getElementById('crawl-title').value.trim();

    if (!url) {
        alert('블로그 URL을 입력하세요.');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/api/crawl`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                title: title || null
            })
        });

        const data = await response.json();
        console.log('크롤링 응답 전체:', data); // 디버깅용
        console.log('body_text 존재:', !!data.body_text);
        console.log('body_text 길이:', data.body_text ? data.body_text.length : 0);
        console.log('body_text 처음 100자:', data.body_text ? data.body_text.substring(0, 100) : '없음');
        showResult(data, 'crawl');
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// 크롤링 (리스트)
async function handleCrawlBulk() {
    const urlsText = document.getElementById('crawl-urls').value.trim();
    const titlesText = document.getElementById('crawl-titles').value.trim();

    if (!urlsText) {
        alert('블로그 URL 리스트를 입력하세요.');
        return;
    }

    const urls = urlsText.split('\n').filter(url => url.trim());
    const titles = titlesText ? titlesText.split('\n').filter(t => t.trim()) : null;

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/api/crawl/bulk`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                urls: urls,
                titles: titles
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '크롤링 실패');
        }

        showResult(data, 'crawl-bulk');
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// 키워드 분석
async function handleAnalyze() {
    const text = document.getElementById('analyze-text').value.trim();
    const topN = parseInt(document.getElementById('analyze-topn').value) || 20;
    const minLength = parseInt(document.getElementById('analyze-minlength').value) || 2;
    const minCount = parseInt(document.getElementById('analyze-mincount').value) || 2;

    if (!text) {
        alert('분석할 텍스트를 입력하세요.');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                top_n: topN,
                min_length: minLength,
                min_count: minCount
            })
        });

        const data = await response.json();
        showResult(data, 'analyze');
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
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

    showLoading();

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

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '처리 실패');
        }

        showResult(data, 'process');
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

