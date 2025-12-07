import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

interface Message {
  role: 'user' | 'model';
  content: string;
}

interface ChatAssistantProps {
  documentId: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const ChartRenderer = ({ data }: { data: any }) => {
  const { type, title, data: chartData, xAxisKey, seriesKey, description } = data;


  // Robust key detection
  let finalXAxisKey = xAxisKey;
  let finalSeriesKey = seriesKey;

  if (chartData && chartData.length > 0) {
    const keys = Object.keys(chartData[0]);
    // If provided keys don't exist in data, try to guess
    if (!keys.includes(xAxisKey)) {
      finalXAxisKey = keys[0]; // Default to first key
    }
    if (!keys.includes(seriesKey)) {
      // Find a key that is not the x-axis key
      const otherKey = keys.find(k => k !== finalXAxisKey);
      finalSeriesKey = otherKey || keys[1] || keys[0];
    }
  }
  const renderChart = () => {
    switch (type) {
      case 'bar':
        return (
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={finalXAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={finalSeriesKey} fill="#8884d8" />
          </BarChart>
        );
      case 'line':
        return (
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={finalXAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={finalSeriesKey} stroke="#8884d8" />
          </LineChart>
        );
      case 'area':
        return (
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={finalXAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey={finalSeriesKey} stroke="#8884d8" fill="#8884d8" />
          </AreaChart>
        );
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent ? percent * 100 : 0).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey={finalSeriesKey}
              nameKey={finalXAxisKey}
            >
              {chartData.map((entry: any, index: number) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        );
      default:
        return <div>Unsupported chart type: {type}</div>;
    }
  };

  return (
    <div className="my-4 p-4 border rounded-lg bg-white shadow-sm">
      {title && <h4 className="text-md font-semibold mb-2 text-center text-gray-800">{title}</h4>}
      <div className="h-[300px] w-full text-gray-800">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
      {description && <p className="text-sm text-gray-500 mt-2 text-center">{description}</p>}
    </div>
  );
};

export default function ChatAssistant({ documentId }: ChatAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'model', content: 'Hello! I am your Teaching Assistant. Ask me anything about this document.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));

      const response = await fetch(`http://localhost:8000/documents/${documentId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          history: history
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      const botMessage: Message = { role: 'model', content: data.response };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { role: 'model', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const parseContent = (content: string) => {
    const parts = [];
    const regex = /\[CHART\]([\s\S]*?)\[\/CHART\]/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ type: 'text', content: content.slice(lastIndex, match.index) });
      }

      try {
        const chartData = JSON.parse(match[1]);
        parts.push({ type: 'chart', data: chartData });
      } catch (e) {
        console.error("Failed to parse chart data", e);
        parts.push({ type: 'text', content: match[0] });
      }

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < content.length) {
      parts.push({ type: 'text', content: content.slice(lastIndex) });
    }

    return parts;
  };

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className={`prose prose-sm ${msg.role === 'user' ? 'prose-invert' : ''} max-w-none`}>
                {parseContent(msg.content).map((part, i) => (
                  part.type === 'text' ? (
                    <ReactMarkdown key={i}>{part.content}</ReactMarkdown>
                  ) : (
                    <ChartRenderer key={i} data={part.data} />
                  )
                ))}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3 text-gray-500 italic">
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about the document..."
            className="flex-1 resize-none border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
