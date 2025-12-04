import React, { useState } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [activeTab, setActiveTab] = useState('search')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // 검색 상태
  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchCount, setSearchCount] = useState(3)

  // 크롤링 상태
  const [crawlUrl, setCrawlUrl] = useState('')
  const [crawlTitle, setCrawlTitle] = useState('')
  const [crawlUrls, setCrawlUrls] = useState('')
  const [crawlTitles, setCrawlTitles] = useState('')

  // 분석 상태
  const [analyzeText, setAnalyzeText] = useState('')
  const [analyzeTopN, setAnalyzeTopN] = useState(20)

  // 전체 처리 상태
  const [processKeyword, setProcessKeyword] = useState('')
  const [processCount, setProcessCount] = useState(3)

  const handleSearch = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/api/search`, {
        keyword: searchKeyword,
        n: searchCount
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCrawl = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/api/crawl`, {
        url: crawlUrl,
        title: crawlTitle || null
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCrawlBulk = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const urls = crawlUrls.split('\n').filter(url => url.trim())
      const titles = crawlTitles ? crawlTitles.split('\n').filter(t => t.trim()) : null

      const response = await axios.post(`${API_BASE_URL}/api/crawl/bulk`, {
        urls: urls,
        titles: titles
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/api/analyze`, {
        text: analyzeText,
        top_n: analyzeTopN,
        min_length: 2,
        min_count: 2
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleProcess = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/api/process`, {
        keyword: processKeyword,
        n: processCount,
        analyze: true,
        top_n: 20,
        min_length: 2,
        min_count: 2
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🚀 DMaLab</h1>
        <p>네이버 블로그 크롤링 및 키워드 분석</p>
      </header>

      <div className="tabs">
        <button
          className={activeTab === 'search' ? 'active' : ''}
          onClick={() => setActiveTab('search')}
        >
          검색
        </button>
        <button
          className={activeTab === 'crawl' ? 'active' : ''}
          onClick={() => setActiveTab('crawl')}
        >
          크롤링
        </button>
        <button
          className={activeTab === 'crawl-bulk' ? 'active' : ''}
          onClick={() => setActiveTab('crawl-bulk')}
        >
          크롤링 (리스트)
        </button>
        <button
          className={activeTab === 'analyze' ? 'active' : ''}
          onClick={() => setActiveTab('analyze')}
        >
          키워드 분석
        </button>
        <button
          className={activeTab === 'process' ? 'active' : ''}
          onClick={() => setActiveTab('process')}
        >
          전체 처리
        </button>
      </div>

      <div className="content">
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>처리 중...</p>
          </div>
        )}

        {error && (
          <div className="error">
            <strong>오류:</strong> {error}
          </div>
        )}

        {activeTab === 'search' && (
          <div className="form-section">
            <h2>블로그 검색</h2>
            <div className="form-group">
              <label>검색 키워드</label>
              <input
                type="text"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                placeholder="예: 아임웹 홈페이지 제작"
              />
            </div>
            <div className="form-group">
              <label>가져올 개수</label>
              <input
                type="number"
                value={searchCount}
                onChange={(e) => setSearchCount(parseInt(e.target.value))}
                min="1"
                max="10"
              />
            </div>
            <button onClick={handleSearch} disabled={loading || !searchKeyword}>
              검색
            </button>
          </div>
        )}

        {activeTab === 'crawl' && (
          <div className="form-section">
            <h2>블로그 크롤링 (단일)</h2>
            <div className="form-group">
              <label>블로그 URL</label>
              <input
                type="text"
                value={crawlUrl}
                onChange={(e) => setCrawlUrl(e.target.value)}
                placeholder="https://blog.naver.com/..."
              />
            </div>
            <div className="form-group">
              <label>블로그 제목 (선택사항)</label>
              <input
                type="text"
                value={crawlTitle}
                onChange={(e) => setCrawlTitle(e.target.value)}
                placeholder="블로그 제목"
              />
            </div>
            <button onClick={handleCrawl} disabled={loading || !crawlUrl}>
              크롤링
            </button>
          </div>
        )}

        {activeTab === 'crawl-bulk' && (
          <div className="form-section">
            <h2>블로그 크롤링 (리스트)</h2>
            <div className="form-group">
              <label>블로그 URL 리스트 (한 줄에 하나씩)</label>
              <textarea
                value={crawlUrls}
                onChange={(e) => setCrawlUrls(e.target.value)}
                placeholder="https://blog.naver.com/...&#10;https://blog.naver.com/...&#10;https://blog.naver.com/..."
                rows="5"
              />
            </div>
            <div className="form-group">
              <label>블로그 제목 리스트 (선택사항, 한 줄에 하나씩)</label>
              <textarea
                value={crawlTitles}
                onChange={(e) => setCrawlTitles(e.target.value)}
                placeholder="제목1&#10;제목2&#10;제목3"
                rows="5"
              />
            </div>
            <button onClick={handleCrawlBulk} disabled={loading || !crawlUrls}>
              크롤링
            </button>
          </div>
        )}

        {activeTab === 'analyze' && (
          <div className="form-section">
            <h2>키워드 분석</h2>
            <div className="form-group">
              <label>분석할 텍스트</label>
              <textarea
                value={analyzeText}
                onChange={(e) => setAnalyzeText(e.target.value)}
                placeholder="분석할 텍스트를 입력하세요..."
                rows="10"
              />
            </div>
            <div className="form-group">
              <label>상위 N개 키워드</label>
              <input
                type="number"
                value={analyzeTopN}
                onChange={(e) => setAnalyzeTopN(parseInt(e.target.value))}
                min="1"
                max="100"
              />
            </div>
            <button onClick={handleAnalyze} disabled={loading || !analyzeText}>
              분석
            </button>
          </div>
        )}

        {activeTab === 'process' && (
          <div className="form-section">
            <h2>전체 처리 (검색 + 크롤링 + 분석)</h2>
            <div className="form-group">
              <label>검색 키워드</label>
              <input
                type="text"
                value={processKeyword}
                onChange={(e) => setProcessKeyword(e.target.value)}
                placeholder="예: 아임웹 홈페이지 제작"
              />
            </div>
            <div className="form-group">
              <label>처리할 블로그 개수</label>
              <input
                type="number"
                value={processCount}
                onChange={(e) => setProcessCount(parseInt(e.target.value))}
                min="1"
                max="10"
              />
            </div>
            <button onClick={handleProcess} disabled={loading || !processKeyword}>
              전체 처리
            </button>
          </div>
        )}

        {result && (
          <div className="result">
            <h3>결과</h3>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  )
}

export default App

