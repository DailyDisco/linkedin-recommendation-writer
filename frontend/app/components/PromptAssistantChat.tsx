import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';

import { Send, Bot, User, Loader2, MessageSquare } from 'lucide-react';
import { apiClient } from '@/services/api';
import type { ContributorInfo } from '../types/index';
import type { RecommendationFormData } from '../hooks/useRecommendationState';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface PromptAssistantChatProps {
  contributor: ContributorInfo;
  formData: RecommendationFormData;
}

export const PromptAssistantChat: React.FC<PromptAssistantChatProps> = ({
  contributor,
  formData,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: `Hi! I'm here to help with high-level brainstorming for ${contributor.username}'s recommendation. Ask me for different angles to take, or for help understanding what makes a recommendation effective. For quick suggestions as you type, use the AI-powered text areas above.`,
      timestamp: new Date(),
    },
  ]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: currentMessage.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);

    try {
      const response = await apiClient.chatWithAssistant({
        github_username: contributor.username,
        conversation_history: messages.slice(-5).map(msg => ({
          role: msg.role,
          content: msg.content,
        })),
        user_message: userMessage.content,
        current_form_data: {
          workingRelationship: formData.workingRelationship,
          specificSkills: formData.specificSkills,
          timeWorkedTogether: formData.timeWorkedTogether,
          notableAchievements: formData.notableAchievements,
          recommendation_type: formData.recommendation_type,
          tone: formData.tone,
          length: formData.length,
          github_input: formData.github_input,
          analysis_type: formData.analysis_type,
        },
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.ai_reply,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message to assistant:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (isMinimized) {
    return (
      <div className='fixed bottom-4 right-4 z-50'>
        <Button
          onClick={() => setIsMinimized(false)}
          className='rounded-full w-12 h-12 shadow-lg bg-blue-600 hover:bg-blue-700'
        >
          <MessageSquare className='w-5 h-5' />
        </Button>
      </div>
    );
  }

  return (
    <div className='fixed bottom-4 right-4 w-96 h-[500px] bg-white rounded-lg shadow-xl border border-gray-200 z-50 flex flex-col'>
      {/* Header */}
      <div className='flex items-center justify-between p-4 border-b border-gray-200 bg-blue-50 rounded-t-lg'>
        <div className='flex items-center space-x-2'>
          <Bot className='w-5 h-5 text-blue-600' />
          <h3 className='font-medium text-blue-900'>AI Writing Assistant</h3>
        </div>
        <Button
          onClick={() => setIsMinimized(true)}
          variant='ghost'
          size='sm'
          className='h-6 w-6 p-0 text-blue-600 hover:text-blue-800'
        >
          ×
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea className='flex-1 p-4'>
        <div className='space-y-4'>
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex items-start space-x-2 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <Bot className='w-4 h-4 text-blue-600 mt-1 flex-shrink-0' />
              )}
              <div
                className={`max-w-[80%] p-3 rounded-lg text-sm ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {message.content}
                {message.role === 'assistant' &&
                  index === messages.length - 1 && (
                    <div className='text-xs text-gray-500 mt-2'>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  )}
              </div>
              {message.role === 'user' && (
                <User className='w-4 h-4 text-blue-600 mt-1 flex-shrink-0' />
              )}
            </div>
          ))}
          {isLoading && (
            <div className='flex items-start space-x-2'>
              <Bot className='w-4 h-4 text-blue-600 mt-1 flex-shrink-0' />
              <div className='bg-gray-100 p-3 rounded-lg'>
                <Loader2 className='w-4 h-4 animate-spin text-blue-600' />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className='p-4 border-t border-gray-200'>
        <div className='flex space-x-2'>
          <Input
            ref={inputRef}
            value={currentMessage}
            onChange={e => setCurrentMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder='Ask me anything about writing recommendations...'
            className='flex-1'
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!currentMessage.trim() || isLoading}
            size='sm'
            className='bg-blue-600 hover:bg-blue-700'
          >
            <Send className='w-4 h-4' />
          </Button>
        </div>
        <p className='text-xs text-gray-500 mt-2'>
          Examples: &ldquo;What should I write about working
          relationship?&rdquo; or &ldquo;Help me describe technical
          skills&rdquo;
        </p>
      </div>
    </div>
  );
};
