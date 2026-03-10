import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Settings, User, Bot, Loader2, Play, RefreshCw, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [scenarios, setScenarios] = useState({});
  const [selectedArea, setSelectedArea] = useState('');
  const [selectedScenario, setSelectedScenario] = useState('');
  const [sysPrompt, setSysPrompt] = useState('');

  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [evaluation, setEvaluation] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Fetch scenarios on load
    axios.get(`${API_BASE}/scenarios`)
      .then(res => {
        setScenarios(res.data);
        const initialArea = Object.keys(res.data)[0];
        const initialScenario = Object.keys(res.data[initialArea])[0];
        setSelectedArea(initialArea);
        setSelectedScenario(initialScenario);
      })
      .catch(err => console.error("Failed to load scenarios", err));
  }, []);

  useEffect(() => {
    // When scenario changes, update prompt and reset chat
    if (scenarios[selectedArea] && scenarios[selectedArea][selectedScenario]) {
      const data = scenarios[selectedArea][selectedScenario];
      setSysPrompt(data.prompt);
      setMessages([
        { role: 'system', content: data.prompt },
        { role: 'assistant', content: data.greeting }
      ]);
      setEvaluation(null);
    }
  }, [selectedArea, selectedScenario, scenarios]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const newMsg = { role: 'user', content: inputMessage };
    const updatedMessages = [...messages, newMsg];
    setMessages(updatedMessages);
    setInputMessage('');
    setIsLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        messages: updatedMessages,
        sys_prompt: sysPrompt
      });

      setMessages([...updatedMessages, { role: 'assistant', content: res.data.response }]);
    } catch (err) {
      console.error(err);
      setMessages([...updatedMessages, { role: 'assistant', content: '❌ Error de red al contactar al simulador.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEvaluate = async () => {
    setIsEvaluating(true);
    try {
      const res = await axios.post(`${API_BASE}/evaluate`, {
        messages: messages,
        area: selectedArea,
        scenario: selectedScenario
      });
      setEvaluation(res.data.report);
      setIsSidebarOpen(false); // Make room for evaluation modal
    } catch (err) {
      console.error("Evaluation failed", err);
      alert("Error generating feedback.");
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-slate-950 font-sans overflow-hidden pattern-bg relative">
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-500/10 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 blur-[120px] rounded-full"></div>
      </div>

      {/* Sidebar */}
      <aside className={`transition-all duration-300 z-10 glass-panel border-r border-t-0 border-b-0 border-l-0 ${isSidebarOpen ? 'w-80' : 'w-0 -translate-x-full'} flex flex-col h-full`}>
        <div className="p-6 flex-1 overflow-y-auto">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Bot size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 to-purple-200 tracking-tight">RolPlay.ai</h1>
              <p className="text-xs text-slate-400 font-medium tracking-wide uppercase">Cerebro de Entrenamiento</p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <Settings size={16} className="text-indigo-400" /> Área de Entrenamiento
              </label>
              <select
                className="w-full bg-slate-900/50 border border-slate-700 text-slate-200 rounded-lg p-3 outline-none focus:ring-2 focus:ring-indigo-500 transition-all appearance-none cursor-pointer"
                value={selectedArea}
                onChange={e => setSelectedArea(e.target.value)}
              >
                {Object.keys(scenarios).map(area => (
                  <option key={area} value={area}>{area}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <Play size={16} className="text-indigo-400" /> Escenario y Dificultad
              </label>
              <select
                className="w-full bg-slate-900/50 border border-slate-700 text-slate-200 rounded-lg p-3 outline-none focus:ring-2 focus:ring-indigo-500 transition-all appearance-none cursor-pointer"
                value={selectedScenario}
                onChange={e => setSelectedScenario(e.target.value)}
              >
                {scenarios[selectedArea] && Object.keys(scenarios[selectedArea]).map(scen => (
                  <option key={scen} value={scen}>{scen}</option>
                ))}
              </select>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 backdrop-blur">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Contexto del Simulador</h3>
              <p className="text-sm text-slate-300/80 leading-relaxed italic line-clamp-6">"{sysPrompt}"</p>
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-slate-800/50">
          {messages.length > 4 && !evaluation && (
            <button
              onClick={handleEvaluate}
              disabled={isEvaluating}
              className="w-full glass-button text-white font-medium py-3 px-4 rounded-xl flex items-center justify-center gap-2 group"
            >
              {isEvaluating ? <Loader2 size={18} className="animate-spin" /> : <AlertCircle size={18} className="group-hover:scale-110 transition-transform" />}
              <span>Finalizar y Evaluar</span>
            </button>
          )}
          {evaluation && (
            <button
              onClick={() => {
                setEvaluation(null);
                setMessages([
                  { role: 'system', content: sysPrompt },
                  { role: 'assistant', content: scenarios[selectedArea][selectedScenario].greeting }
                ]);
              }}
              className="w-full bg-slate-800 hover:bg-slate-700 text-white font-medium py-3 px-4 rounded-xl flex items-center justify-center gap-2 border border-slate-700 transition-all"
            >
              <RefreshCw size={18} />
              <span>Reiniciar Simulación</span>
            </button>
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <main className="flex-1 flex flex-col h-full relative z-10">

        {/* Toggle Sidebar Button */}
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="absolute top-6 left-6 z-20 w-10 h-10 rounded-full bg-slate-900/80 border border-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors backdrop-blur-md"
        >
          <Settings size={18} />
        </button>

        {evaluation && (
          <div className="absolute inset-0 z-50 bg-slate-950/80 backdrop-blur-sm p-8 flex items-center justify-center animate-in fade-in duration-300">
            <div className="glass-panel w-full max-w-2xl max-h-[90vh] rounded-2xl overflow-hidden flex flex-col">
              <div className="p-6 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                <h2 className="text-xl font-bold text-white flex items-center gap-2"><AlertCircle className="text-indigo-400" /> Reporte de Desempeño</h2>
                <button onClick={() => setEvaluation(null)} className="text-slate-400 hover:text-white">✕</button>
              </div>
              <div className="p-6 overflow-y-auto prose prose-invert prose-indigo max-w-none text-slate-300">
                <div dangerouslySetInnerHTML={{ __html: evaluation.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
              </div>
              <div className="p-6 border-t border-slate-800 bg-slate-900/30 flex justify-end">
                <button
                  onClick={() => {
                    setEvaluation(null);
                    setMessages([
                      { role: 'system', content: sysPrompt },
                      { role: 'assistant', content: scenarios[selectedArea][selectedScenario].greeting }
                    ]);
                  }}
                  className="glass-button px-6 py-2 rounded-lg text-white font-medium flex items-center gap-2"
                >
                  <RefreshCw size={16} /> Reintentar Nivel
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-4 sm:p-8 space-y-6 pt-20 pb-32 max-w-4xl mx-auto w-full scroll-smooth">
          {messages.map((msg, idx) => {
            if (msg.role === 'system') return null;
            const isUser = msg.role === 'user';
            return (
              <div key={idx} className={`flex gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'} items-end animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border shadow-lg ${isUser ? 'bg-gradient-to-br from-indigo-500 to-purple-600 border-indigo-400/50' : 'bg-slate-800 border-slate-700'}`}>
                  {isUser ? <User size={18} className="text-white" /> : <Bot size={18} className="text-indigo-300" />}
                </div>
                <div className={`max-w-[80%] rounded-2xl p-4 sm:p-5 shadow-sm text-[15px] leading-relaxed relative ${isUser ? 'bg-indigo-600/90 text-white rounded-br-sm backdrop-blur-md border border-indigo-500/50' : 'glass-panel text-slate-200 rounded-bl-sm'}`}>
                  {msg.content}
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex gap-4 items-end animate-in fade-in duration-300">
              <div className="w-10 h-10 rounded-full bg-slate-800 border-slate-700 flex items-center justify-center shrink-0 border shadow-lg">
                <Bot size={18} className="text-indigo-400" />
              </div>
              <div className="glass-panel text-slate-300 rounded-2xl rounded-bl-sm p-5 flex items-center gap-2 shadow-sm">
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 w-full p-6 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent pt-12">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSendMessage} className="relative group">
              <input
                type="text"
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                placeholder="Escribe tu respuesta para manejar la situación..."
                disabled={isLoading || evaluation}
                className="w-full bg-slate-900/60 backdrop-blur-xl border border-slate-700/80 text-white rounded-2xl pl-6 pr-16 py-4 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all shadow-xl disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!inputMessage.trim() || isLoading || evaluation}
                className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl flex items-center justify-center transition-all disabled:opacity-50 disabled:hover:bg-indigo-600 shadow-md shadow-indigo-600/20"
              >
                {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} className="translate-x-[-1px] translate-y-[1px]" />}
              </button>
            </form>
            <p className="text-center text-xs text-slate-500 mt-3 font-medium tracking-wide">RolPlay.ai Simulator v2.0 - Powered by Google Gemini</p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
