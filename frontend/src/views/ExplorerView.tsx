import React, { useState, useEffect, useCallback } from 'react'
import {
  Code2,
  FileText,
  Search,
  FileCode,
  RefreshCw,
} from 'lucide-react'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { fetchRepositoryFiles, fetchRepositoryFileContent } from '../services/api'
import type { RepositoryItem, RepositoryFileItem } from '../types/api'

interface ExplorerViewProps {
  activeRepo: RepositoryItem | null
}

export const ExplorerView: React.FC<ExplorerViewProps> = ({ activeRepo }) => {
  const [files, setFiles] = useState<RepositoryFileItem[]>([])
  const [filteredFiles, setFilteredFiles] = useState<RepositoryFileItem[]>([])
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [loadingFiles, setLoadingFiles] = useState(false)
  const [loadingContent, setLoadingContent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadFileContent = useCallback(async (path: string) => {
    if (!activeRepo) return
    setSelectedFilePath(path)
    setLoadingContent(true)
    try {
      const data = await fetchRepositoryFileContent(activeRepo.repository_id, path)
      setFileContent(data.content)
    } catch {
      setFileContent('# Unable to load file content from backend.')
    } finally {
      setLoadingContent(false)
    }
  }, [activeRepo])

  useEffect(() => {
    if (!activeRepo) return
    const loadFiles = async () => {
      setLoadingFiles(true)
      setError(null)
      try {
        const data = await fetchRepositoryFiles(activeRepo.repository_id)
        setFiles(data.files || [])
        setFilteredFiles(data.files || [])
        if (data.files && data.files.length > 0) {
          loadFileContent(data.files[0].path)
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to fetch repository files')
      } finally {
        setLoadingFiles(false)
      }
    }
    loadFiles()
  }, [activeRepo, loadFileContent])

  const handleSearch = (q: string) => {
    setSearchQuery(q)
    if (!q.trim()) {
      setFilteredFiles(files)
    } else {
      setFilteredFiles(
        files.filter((f) => f.path.toLowerCase().includes(q.toLowerCase()))
      )
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Code2 className="w-5 h-5 text-indigo-600" />
            Repository Code Explorer
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Browse repository source code and structural Tree-Sitter AST modules in {activeRepo?.name || 'repository'}.
          </p>
        </div>

        <Badge variant="brand" size="sm">
          {activeRepo?.language || 'Python'} &bull; Tree-Sitter Active
        </Badge>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Explorer Container */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[680px]">
        {/* Left: File Tree */}
        <div className="lg:col-span-4 h-full">
          <Card className="h-full flex flex-col">
            <div className="p-3 border-b border-slate-200">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="Filter files..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-900 focus:bg-white focus:outline-indigo-600"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
              {loadingFiles ? (
                <div className="p-8 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-slate-400" />
                  <span>Loading repository tree...</span>
                </div>
              ) : filteredFiles.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-400">
                  No matching files found.
                </div>
              ) : (
                filteredFiles.map((file) => {
                  const isSelected = selectedFilePath === file.path
                  return (
                    <button
                      key={file.path}
                      onClick={() => loadFileContent(file.path)}
                      className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-mono transition-colors flex items-center justify-between cursor-pointer ${
                        isSelected
                          ? 'bg-indigo-50 text-indigo-700 font-semibold border border-indigo-100'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                      }`}
                    >
                      <span className="truncate flex items-center gap-1.5">
                        <FileCode className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                        <span className="truncate">{file.path}</span>
                      </span>
                      <span className="text-[10px] text-slate-400 flex-shrink-0 font-normal">
                        {(file.size_bytes / 1024).toFixed(1)}k
                      </span>
                    </button>
                  )
                })
              )}
            </div>

            <div className="p-2.5 border-t border-slate-100 bg-slate-50 text-[11px] text-slate-500 flex items-center justify-between">
              <span>{files.length} indexed files</span>
              <span className="font-mono">{activeRepo?.repository_id}</span>
            </div>
          </Card>
        </div>

        {/* Right: Code Viewer */}
        <div className="lg:col-span-8 h-full">
          <Card className="h-full flex flex-col">
            <div className="p-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-mono">
                <FileText className="w-4 h-4 text-indigo-600" />
                <span className="font-semibold text-slate-900">{selectedFilePath || 'Select a file'}</span>
              </div>
              <Badge variant="neutral" size="sm">
                UTF-8
              </Badge>
            </div>

            <div className="flex-1 overflow-auto p-4 bg-white font-mono text-xs text-slate-800 leading-relaxed">
              {loadingContent ? (
                <div className="h-full flex items-center justify-center text-slate-400 gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Loading file content...</span>
                </div>
              ) : fileContent ? (
                <pre className="overflow-x-auto whitespace-pre">{fileContent}</pre>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400">
                  Select a file from the explorer on the left to inspect its source code.
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
