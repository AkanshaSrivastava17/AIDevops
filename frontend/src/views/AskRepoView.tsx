import React, { useState, useEffect, useRef } from 'react'
import {
  MessageSquareText,
  Send,
  Plus,
  ThumbsUp,
  ThumbsDown,
  Bookmark,
  Bot,
  User as UserIcon,
  Layers
} from 'lucide-react'
import type { Conversation, DemoPersona } from '../types/api'
import {
  fetchConversations,
  createConversation,
  fetchConversation,
  sendConversationMessage,
  submitMessageFeedback,
  saveMessageNote,
  fetchKnowledgeMap
} from '../services/api'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { CitationChip } from '../components/ui/CitationChip'
import { Tabs } from '../components/ui/Tabs'

interface AskRepoViewProps {
  activeRepoId: string
  activeProjectId: string
  activePersona: DemoPersona | null
}

export const AskRepoView: React.FC<AskRepoViewProps> = ({
  activeRepoId,
  activeProjectId,
  activePersona,
}) => {
  const [activeTab, setActiveTab] = useState<'chat' | 'knowledge'>('chat')
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConvId, setActiveConvId] = useState<string | null>(null)
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)
  const [inputMessage, setInputMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [knowledgeData, setKnowledgeData] = useState<any>(null)
  const [feedbackSuccess, setFeedbackSuccess] = useState<Record<string, string>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 1. Load conversations
  useEffect(() => {
    loadConversations()
  }, [activeProjectId])

  const loadConversations = async () => {
    try {
      const convs = await fetchConversations(activeProjectId)
      setConversations(convs)
      if (convs.length > 0 && !activeConvId) {
        selectConversation(convs[0].id)
      } else if (convs.length === 0) {
        handleNewConversation()
      }
    } catch (err) {
      console.error('Failed to load conversations', err)
    }
  }

  // 2. Select conversation
  const selectConversation = async (id: string) => {
    setActiveConvId(id)
    try {
      const conv = await fetchConversation(id)
      setCurrentConversation(conv)
    } catch (err) {
      console.error('Failed to load conversation details', err)
    }
  }

  // 3. Create new conversation
  const handleNewConversation = async () => {
    try {
      const title = `Discussion ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
      const newConv = await createConversation({
        title,
        project_id: activeProjectId,
        repository_id: activeRepoId,
      })
      setConversations([newConv, ...conversations])
      setActiveConvId(newConv.id)
      setCurrentConversation(newConv)
    } catch (err) {
      console.error('Failed to create conversation', err)
    }
  }

  // 4. Send Message
  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMessage
    if (!text.trim() || !activeConvId || isSending) return

    setIsSending(true)
    setInputMessage('')
    try {
      const res = await sendConversationMessage(activeConvId, text, 'History-RAG')
      // Update local messages
      if (currentConversation) {
        setCurrentConversation({
          ...currentConversation,
          messages: [...currentConversation.messages, res.user_message, res.assistant_message],
        })
      }
    } catch (err) {
      console.error('Failed to send message', err)
    } finally {
      setIsSending(false)
    }
  }

  // 5. Submit Feedback
  const handleFeedback = async (messageId: string, rating: number) => {
    try {
      await submitMessageFeedback(messageId, rating)
      setFeedbackSuccess((prev) => ({ ...prev, [messageId]: rating > 0 ? 'up' : 'down' }))
    } catch (err) {
      console.error('Failed to submit feedback', err)
    }
  }

  // 6. Save as note
  const handleSaveNote = async (messageId: string) => {
    try {
      await saveMessageNote(messageId, 'Key Repo Insight')
      setFeedbackSuccess((prev) => ({ ...prev, [messageId]: 'saved' }))
    } catch (err) {
      console.error('Failed to save note', err)
    }
  }

  // 7. Load Knowledge Map
  useEffect(() => {
    if (activeTab === 'knowledge' && !knowledgeData) {
      fetchKnowledgeMap(activeRepoId)
        .then(setKnowledgeData)
        .catch(console.error)
    }
  }, [activeTab, activeRepoId, knowledgeData])

  // Scroll to bottom on messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentConversation?.messages])

  const starterPrompts = [
    'Where is the VRF model defined in NetBox?',
    'What were the most frequent bugs in IPAM tenancy?',
    'Explain the architectural rationale of DEC-018',
    'Which tests exercise interface IP boundary assignment?',
  ]

  return (
    <div className="space-y-4">
      {/* Top Controls */}
      <div className="flex items-center justify-between">
        <Tabs
          tabs={[
            { id: 'chat', label: 'Cited Q&A Conversation', icon: <MessageSquareText className="w-4 h-4" /> },
            { id: 'knowledge', label: 'Knowledge & Architecture Map', icon: <Layers className="w-4 h-4" /> },
          ]}
          activeTab={activeTab}
          onChange={(id) => setActiveTab(id as any)}
          variant="pills"
        />
        <Button
          variant="secondary"
          size="sm"
          icon={<Plus className="w-3.5 h-3.5" />}
          onClick={handleNewConversation}
        >
          New Conversation
        </Button>
      </div>

      {activeTab === 'chat' ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 min-h-[640px]">
          {/* Left: Conversations list */}
          <div className="md:col-span-1 border border-slate-200 bg-white rounded-xl p-3 flex flex-col h-[640px]">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <span>Past Q&A Threads</span>
              <span className="text-slate-500 font-mono text-[10px]">{conversations.length}</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
              {conversations.map((c) => {
                const isActive = c.id === activeConvId
                return (
                  <button
                    key={c.id}
                    onClick={() => selectConversation(c.id)}
                    className={`w-full text-left p-2.5 rounded-lg text-xs transition-colors flex items-center justify-between group ${
                      isActive
                        ? 'bg-indigo-50 border border-indigo-200/80 text-indigo-900 font-semibold'
                        : 'text-slate-600 hover:bg-slate-50 border border-transparent'
                    }`}
                  >
                    <span className="truncate pr-2">{c.title || 'Conversation'}</span>
                    <span className="text-[10px] text-slate-400 font-mono shrink-0">
                      {c.messages?.length || 0}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Right: Messages Thread */}
          <div className="md:col-span-3 border border-slate-200 bg-white rounded-xl flex flex-col h-[640px] overflow-hidden">
            {/* Conversation Header */}
            <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/60 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900 truncate">
                  {currentConversation?.title || 'Q&A Thread'}
                </span>
                <span className="text-slate-400">•</span>
                <span className="font-mono text-slate-500 text-[11px]">
                  Repo: {currentConversation?.repository_id || activeRepoId}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="brand" size="sm">
                  History-RAG Verified
                </Badge>
              </div>
            </div>

            {/* Message Thread Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5 bg-slate-50/20">
              {currentConversation?.messages && currentConversation.messages.length > 0 ? (
                currentConversation.messages.map((msg) => {
                  const isUser = msg.role === 'user'

                  return (
                    <div
                      key={msg.id}
                      className={`flex gap-3 text-xs leading-relaxed ${isUser ? 'justify-end' : 'justify-start'}`}
                    >
                      {!isUser && (
                        <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                          <Bot className="w-4 h-4" />
                        </div>
                      )}

                      <div
                        className={`max-w-2xl rounded-2xl px-4 py-3 shadow-2xs ${
                          isUser
                            ? 'bg-indigo-600 text-white rounded-tr-xs'
                            : 'bg-white border border-slate-200/90 text-slate-800 rounded-tl-xs space-y-3'
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{msg.content}</p>

                        {/* Citations & Evidence Section */}
                        {!isUser && msg.evidence_refs && msg.evidence_refs.length > 0 && (
                          <div className="pt-2.5 border-t border-slate-100 space-y-1.5">
                            <span className="text-[10px] font-bold uppercase text-slate-400 block tracking-wider">
                              Verified Evidence Citations ({msg.evidence_refs.length})
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {msg.evidence_refs.map((ref) => (
                                <CitationChip key={ref.id} citation={ref} />
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Assistant Feedback & Note Toolbar */}
                        {!isUser && (
                          <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-400">
                            <div className="flex items-center gap-2">
                              <span>Confidence: {( (msg.confidence || 0.9) * 100).toFixed(0)}%</span>
                              <span>•</span>
                              <span className="font-mono">{msg.retrieval_mode || 'History-RAG'}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => handleFeedback(msg.id, 1)}
                                className={`p-1 rounded hover:bg-slate-100 transition-colors ${
                                  feedbackSuccess[msg.id] === 'up' ? 'text-emerald-600' : 'text-slate-400'
                                }`}
                                title="Helpful answer"
                              >
                                <ThumbsUp className="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                onClick={() => handleFeedback(msg.id, -1)}
                                className={`p-1 rounded hover:bg-slate-100 transition-colors ${
                                  feedbackSuccess[msg.id] === 'down' ? 'text-rose-600' : 'text-slate-400'
                                }`}
                                title="Not helpful"
                              >
                                <ThumbsDown className="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                onClick={() => handleSaveNote(msg.id)}
                                className={`p-1 rounded hover:bg-slate-100 transition-colors ${
                                  feedbackSuccess[msg.id] === 'saved' ? 'text-indigo-600' : 'text-slate-400'
                                }`}
                                title="Save as Learning Note"
                              >
                                <Bookmark className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        )}
                      </div>

                      {isUser && (
                        <div className="w-7 h-7 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 font-bold text-xs">
                          {activePersona ? activePersona.avatar : <UserIcon className="w-4 h-4" />}
                        </div>
                      )}
                    </div>
                  )
                })
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
                  <MessageSquareText className="w-10 h-10 text-slate-300 mb-3" />
                  <h4 className="text-sm font-semibold text-slate-700">Ask anything about {activeRepoId}</h4>
                  <p className="text-xs text-slate-500 max-w-sm mt-1">
                    Get cited answers grounded strictly in commits, issues, pull requests, and architectural decisions.
                  </p>

                  <div className="flex flex-wrap justify-center gap-2 mt-5 max-w-md">
                    {starterPrompts.map((prompt, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => handleSendMessage(prompt)}
                        className="text-[11px] bg-white border border-slate-200 hover:border-indigo-300 hover:text-indigo-600 text-slate-600 px-3 py-1.5 rounded-lg shadow-2xs transition-colors"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Box */}
            <div className="p-3 border-t border-slate-200 bg-white">
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleSendMessage()
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={`Ask a question with evidence citations for ${activeRepoId}...`}
                  disabled={isSending}
                  className="flex-1 bg-slate-50 border border-slate-200 focus:border-indigo-500 focus:bg-white rounded-lg px-3.5 py-2.5 text-xs text-slate-900 focus:outline-none transition-colors"
                />
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  disabled={!inputMessage.trim() || isSending}
                  icon={<Send className="w-3.5 h-3.5" />}
                >
                  Send
                </Button>
              </form>
            </div>
          </div>
        </div>
      ) : (
        /* Knowledge & Architecture Map View */
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Repository Knowledge Map</h3>
              <p className="text-xs text-slate-500">
                Connected components, co-changing files, and historical regression density for {activeRepoId}
              </p>
            </div>
            <Badge variant="brand" size="sm">Indexed Graph</Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {knowledgeData?.components ? (
              knowledgeData.components.map((comp: any) => (
                <div
                  key={comp.name}
                  className="p-4 rounded-xl border border-slate-200 bg-white hover:border-indigo-300 transition-all space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-slate-900 text-sm">{comp.name}</span>
                    <Badge variant={comp.risk === 'High' ? 'error' : comp.risk === 'Medium' ? 'warning' : 'success'} size="sm">
                      {comp.risk || 'Normal'} Risk
                    </Badge>
                  </div>
                  <p className="text-slate-500 text-[11px]">{comp.description || 'Core module integration'}</p>
                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[10px] text-slate-400">
                    <span>{comp.files_count || 12} files</span>
                    <span>{comp.tests_count || 8} regression tests</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-3 text-center py-12 text-slate-400 text-xs">
                Loading knowledge map graph topology...
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
