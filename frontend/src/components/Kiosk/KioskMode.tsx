import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import {
  MicrophoneIcon,
  SpeakerWaveIcon,
  HomeIcon,
  QuestionMarkCircleIcon,
  DocumentTextIcon,
  ScaleIcon,
  UserGroupIcon,
  EyeIcon,
  MagnifyingGlassMinusIcon,
  MagnifyingGlassPlusIcon
} from '@heroicons/react/24/outline';
import type { Message, ChatResponse } from '../../types';
import { ApiService, generateSessionId } from '../../services/api';

// Translation system for Nigerian languages
const translations = {
  en: {
    welcome: "Welcome to",
    title: "The Supreme Court",
    subtitle: "of Nigeria",
    description: "Explore the history, structure and significance of the Supreme Court of Nigeria. Get information about access, legal precedents, and citizen services.",
    placeholder: "Ask me anything about the Supreme Court of Nigeria...",
    askSconia: "Ask SCONIA",
    categories: {
      constitutional: "Search the Constitution",
      historical: "Origins, Timelines & Past Events",
      judicial: "Meet the Justices",
      administrative: "Find an Office/Department",
      procedural: "Court Procedures"
    },
    settings: {
      language: "Language",
      fontSize: "Font Size",
      highContrast: "High Contrast",
      close: "Close"
    },
    accessibility: {
      mainMenu: "Main menu",
      voiceInput: "Voice input",
      settings: "Accessibility settings",
      home: "Return to home"
    },
    ui: {
      home: "Home",
      sconiaChat: "SCONIA Chat",
      stopSpeaking: "Stop Speaking",
      sources: "Sources:",
      thinking: "SCONIA is thinking...",
      inputPlaceholder: "Type your question here...",
      send: "Send"
    }
  },
  ha: {
    welcome: "Maraba zuwa",
    title: "Kotun Koli",
    subtitle: "ta Najeriya",
    description: "Binciki tarihi, tsarin da mahimmancin Kotun Koli ta Najeriya. Samu bayanai game da shiga, ka'idodin shari'a, da ayyukan jama'a.",
    placeholder: "Tambaye ni komai game da Kotun Koli ta Najeriya...",
    askSconia: "Tambaya SCONIA",
    categories: {
      constitutional: "Binciki Kundin Tsarin Mulki",
      historical: "Asali, Lokaci da Abubuwan da suka gabata",
      judicial: "Saduwa da Alkalai",
      administrative: "Nemo Ofis/Sashe",
      procedural: "Hanyoyin Kotu"
    },
    settings: {
      language: "Harshe",
      fontSize: "Girman Rubutu",
      highContrast: "Babban Bambanci",
      close: "Rufe"
    },
    accessibility: {
      mainMenu: "Babban menu",
      voiceInput: "Shigar da murya",
      settings: "Saitunan dama",
      home: "Koma gida"
    },
    ui: {
      home: "Gida",
      sconiaChat: "SCONIA Hira",
      stopSpeaking: "Daina Magana",
      sources: "Majiyoyi:",
      thinking: "SCONIA yana tunani...",
      inputPlaceholder: "Rubuta tambayarka a nan...",
      send: "Aiko"
    }
  },
  yo: {
    welcome: "Kaabo si",
    title: "Ile-ejo Giga-giga",
    subtitle: "ti Naijiria",
    description: "Ṣawari itan-akọọlẹ, eto ati pataki ti Ile-ejo Giga-giga ti Naijiria. Gba alaye nipa wiwọle, awọn ofin, ati awọn iṣẹ ara ilu.",
    placeholder: "Beere ohunkohun nipa Ile-ejo Giga-giga ti Naijiria...",
    askSconia: "Beere SCONIA",
    categories: {
      constitutional: "Wa ninu Ofin-ipilẹ",
      historical: "Ipilẹṣẹ, Akoko ati Awọn iṣẹlẹ ti tẹlẹ",
      judicial: "Pade awọn Adajọ",
      administrative: "Wa Ọfiisi/Ẹka kan",
      procedural: "Awọn ilana Ile-ejo"
    },
    settings: {
      language: "Ede",
      fontSize: "Iwọn Kikọ",
      highContrast: "Iyatọ Giga",
      close: "Pa"
    },
    accessibility: {
      mainMenu: "Akojọ aṣayan akọkọ",
      voiceInput: "Titẹ ohun sii",
      settings: "Awọn eto iraye si",
      home: "Pada si ile"
    },
    ui: {
      home: "Ile",
      sconiaChat: "SCONIA Ibaraẹnisọrọ",
      stopSpeaking: "Duro Sisọrọ",
      sources: "Awọn orisun:",
      thinking: "SCONIA n ronu...",
      inputPlaceholder: "Ko ibeere rẹ nibi...",
      send: "Fi ranṣẹ"
    }
  },
  ig: {
    welcome: "Nnọọ na",
    title: "Ụlọ Ikpe Kasị Elu",
    subtitle: "nke Naịjirịa",
    description: "Nyochaa akụkọ ihe mere eme, nhazi na mkpa nke Ụlọ Ikpe Kasị Elu nke Naịjirịa. Nweta ozi gbasara ịbanye, iwu iwu, na ọrụ ụmụ amaala.",
    placeholder: "Jụọ m ihe ọ bụla gbasara Ụlọ Ikpe Kasị Elu nke Naịjirịa...",
    askSconia: "Jụọ SCONIA",
    categories: {
      constitutional: "Chọọ na Constitution",
      historical: "Mmalite, Oge na Ihe ndị gara aga",
      judicial: "Zute ndị Ọka Ikpe",
      administrative: "Chọta Ọfịs/Ngalaba",
      procedural: "Usoro Ụlọ Ikpe"
    },
    settings: {
      language: "Asụsụ",
      fontSize: "Nha Edemede",
      highContrast: "Elu Contrast",
      close: "Mechi"
    },
    accessibility: {
      mainMenu: "Menu isi",
      voiceInput: "Ntinye olu",
      settings: "Ntọala nnweta",
      home: "Laghachi n’ụlọ"
    },
    ui: {
      home: "Ụlọ",
      sconiaChat: "SCONIA Nkwurịta",
      stopSpeaking: "Kwụsị ikwu",
      sources: "Isi iyi:",
      thinking: "SCONIA na-eche...",
      inputPlaceholder: "Dee ajụjụ gị ebe a...",
      send: "Zipu"
    }
  }
};

const t = (key: string, lang: 'en' | 'ha' | 'yo' | 'ig' = 'en'): string => {
  const keys = key.split('.');
  let value: any = translations[lang];
  for (const k of keys) {
    value = value?.[k];
  }
  return value || key;
};

interface KioskModeProps {
  onExitKiosk?: () => void;
}

const KioskMode: React.FC<KioskModeProps> = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  const [currentInput, setCurrentInput] = useState('');
  const [showMainMenu, setShowMainMenu] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState<'en' | 'ha' | 'yo' | 'ig'>(() => {
    // Load saved language preference from localStorage
    const savedLanguage = localStorage.getItem('sconia-language');
    return (savedLanguage as 'en' | 'ha' | 'yo' | 'ig') || 'en';
  });
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [highContrastMode, setHighContrastMode] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState<string[]>(['Home']);
  const [inactivityTimer, setInactivityTimer] = useState<NodeJS.Timeout | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-reset timer for inactivity
  const resetInactivityTimer = () => {
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
    }
    const timer = setTimeout(() => {
      setShowMainMenu(true);
      setMessages([]);
      setCurrentInput('');
      setBreadcrumbs(['Home']);
      if (synthesis.current) {
        synthesis.current.cancel();
      }
    }, 300000); // 5 minutes
    setInactivityTimer(timer);
  };

  // Handle user activity
  useEffect(() => {
    const handleActivity = () => resetInactivityTimer();
    
    document.addEventListener('mousedown', handleActivity);
    document.addEventListener('keydown', handleActivity);
    document.addEventListener('touchstart', handleActivity);
    
    resetInactivityTimer();
    
    return () => {
      document.removeEventListener('mousedown', handleActivity);
      document.removeEventListener('keydown', handleActivity);
      document.removeEventListener('touchstart', handleActivity);
      if (inactivityTimer) {
        clearTimeout(inactivityTimer);
      }
    };
  }, []);

  // Apply accessibility classes
  useEffect(() => {
    const root = document.documentElement;
    
    // Font size
    root.classList.remove('text-small', 'text-medium', 'text-large');
    root.classList.add(`text-${fontSize}`);
    
    // High contrast
    if (highContrastMode) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }
    
    return () => {
      root.classList.remove('text-small', 'text-medium', 'text-large', 'high-contrast');
    };
  }, [fontSize, highContrastMode]);

  // Handle browser back button to prevent exiting kiosk
  useEffect(() => {
    // Push initial state to history when kiosk loads
    window.history.pushState({ kioskMode: true, view: showMainMenu ? 'menu' : 'chat' }, '', window.location.href);

    const handlePopState = (event: PopStateEvent) => {
      // Prevent going back outside of kiosk
      if (!event.state || !event.state.kioskMode) {
        // Push back to kiosk state
        window.history.pushState({ kioskMode: true, view: 'menu' }, '', window.location.href);
        setShowMainMenu(true);
        setMessages([]);
        return;
      }

      // Handle internal kiosk navigation
      if (event.state.view === 'menu' && !showMainMenu) {
        handleBackToMenu();
      } else if (event.state.view === 'menu') {
        // Already in menu, stay there
        setShowMainMenu(true);
        setMessages([]);
      }
    };

    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [showMainMenu]);

  // Voice recognition setup
  const recognition = useRef<any | null>(null);
  const synthesis = useRef<SpeechSynthesis | null>(null);

  useEffect(() => {
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      recognition.current = new SpeechRecognition();
      recognition.current.continuous = false;
      recognition.current.interimResults = false;
      const langMap = { 'en': 'en-NG', 'ha': 'ha-NG', 'yo': 'yo-NG', 'ig': 'ig-NG' };
      recognition.current.lang = langMap[currentLanguage] || 'en-NG';

      recognition.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setCurrentInput(transcript);
        setIsListening(false);
      };

      recognition.current.onerror = () => {
        setIsListening(false);
        toast.error('Voice recognition failed. Please try again.');
      };
    }

    // Initialize speech synthesis
    synthesis.current = window.speechSynthesis;

    return () => {
      if (recognition.current) {
        recognition.current.stop();
      }
      if (synthesis.current) {
        synthesis.current.cancel();
      }
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Save language preference to localStorage
  useEffect(() => {
    localStorage.setItem('sconia-language', currentLanguage);
  }, [currentLanguage]);

  const getMainMenuOptions = () => [
    {
      category: "CONSTITUTIONAL",
      title: t('categories.constitutional', currentLanguage),
      shortDescription: "Learn about fundamental rights, constitutional law, and the foundation of Nigeria's legal system.",
      icon: ScaleIcon,
      query: "What are the fundamental rights guaranteed by the Nigerian Constitution?"
    },
    {
      category: "HISTORICAL",
      title: t('categories.historical', currentLanguage),
      shortDescription: "Discover the origins, evolution, and landmark moments in Nigerian Supreme Court history.",
      icon: DocumentTextIcon,
      query: "Tell me about the history and origins of the Supreme Court of Nigeria"
    },
    {
      category: "JUDICIAL",
      title: t('categories.judicial', currentLanguage),
      shortDescription: "Meet current and past justices, learn about their backgrounds and notable decisions.",
      icon: UserGroupIcon,
      query: "Tell me about the current Supreme Court justices"
    },
    {
      category: "ADMINISTRATIVE",
      title: t('categories.administrative', currentLanguage),
      shortDescription: "Find court offices, departments, services, and administrative information.",
      icon: QuestionMarkCircleIcon,
      query: "Tell me about the Supreme Court of Nigeria structure and departments"
    },
    {
      category: "PROCEDURAL",
      title: t('categories.procedural', currentLanguage),
      shortDescription: "Understand court procedures, filing processes, and how cases progress through the system.",
      icon: DocumentTextIcon,
      query: "Tell me about Supreme Court procedures and how cases are handled"
    }
  ];

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    setShowMainMenu(false);
    // Update browser history when entering chat
    window.history.pushState({ kioskMode: true, view: 'chat' }, '', window.location.href);
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setCurrentInput('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await ApiService.sendMessage({
        query: content,
        session_id: sessionId
      });
      
      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        quickOptions: response.quick_options
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Speak the response if synthesis is available
      if (synthesis.current && !isSpeaking) {
        speakText(response.answer);
      }

    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to get response. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const speakText = (text: string) => {
    if (!synthesis.current) return;

    // Clean text for speech (remove markdown and special characters)
    const cleanText = text
      .replace(/[#*_`]/g, '')
      .replace(/\n+/g, '. ')
      .replace(/\s+/g, ' ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.8;
    utterance.pitch = 1;
    utterance.volume = 0.8;
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthesis.current.speak(utterance);
  };

  const startListening = () => {
    if (!recognition.current) {
      toast.error('Voice recognition not supported');
      return;
    }

    setIsListening(true);
    recognition.current.start();
  };

  const stopSpeaking = () => {
    if (synthesis.current) {
      synthesis.current.cancel();
      setIsSpeaking(false);
    }
  };

  const handleMainMenuClick = (option: ReturnType<typeof getMainMenuOptions>[0]) => {
    handleSendMessage(option.query);
  };

  const handleBackToMenu = () => {
    setShowMainMenu(true);
    setMessages([]);
    setCurrentInput('');
    stopSpeaking();
    // Update browser history
    window.history.pushState({ kioskMode: true, view: 'menu' }, '', window.location.href);
  };

  if (showMainMenu) {
    return (
      <div className="min-h-screen bg-[linear-gradient(236deg,#2A805B_7.46%,#143830_92.54%)] p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <p className="text-caption text-green-200 mb-1 tracking-wider uppercase">{t('welcome', currentLanguage)}</p>
            <h1 className="text-heading-1 text-white mb-1 font-heading-1">
              {t('title', currentLanguage)}
            </h1>
            <h2 className="text-heading-2 text-white mb-4 font-heading-2">
              {t('subtitle', currentLanguage)}
            </h2>
            <p className="text-body text-green-100 max-w-xl mx-auto leading-relaxed mb-6 font-body">
              {t('description', currentLanguage)}
            </p>

            {/* Search Bar */}
            <div className="max-w-3xl mx-auto mb-8">
              <div className="flex items-center gap-4 bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-3 hover:shadow-3xl transition-all duration-300">
                <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-green-600 to-green-700 rounded-2xl flex-shrink-0">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>

                <input
                  type="text"
                  value={currentInput}
                  onChange={(e) => setCurrentInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(currentInput)}
                  placeholder={t('placeholder', currentLanguage)}
                  aria-label={t('placeholder', currentLanguage)}
                  className="flex-1 py-4 px-2 bg-transparent text-gray-800 placeholder-gray-400 focus:outline-none text-body font-body border-none"
                />

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleSendMessage(currentInput)}
                  disabled={!currentInput.trim()}
                  className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 px-6 py-3 rounded-2xl text-white text-body-bold font-body-bold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg flex-shrink-0"
                >
                  {t('askSconia', currentLanguage)}
                </motion.button>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Main Menu Grid */}
        <div className="max-w-4xl mx-auto" role="main">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" role="navigation" aria-label={t('accessibility.mainMenu', currentLanguage)}>
            {getMainMenuOptions().map((option, index) => (
              <motion.button
                key={`${option.title}-${index}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleMainMenuClick(option)}
                aria-describedby={`desc-${index}`}
                className={`bg-green-700/60 backdrop-blur-sm border border-green-500/30 rounded-lg p-6 hover:bg-green-600/70 transition-all duration-300 text-left group min-h-[160px] min-w-[250px] flex flex-col focus:ring-2 focus:ring-white focus:ring-offset-2 focus:outline-none ${highContrastMode ? 'contrast-more border-2' : ''}`}
              >
                <div className="text-caption font-caption text-green-200 tracking-wider opacity-70 mb-3">
                  {option.category}
                </div>
                <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-green-100 flex-1">
                  {option.title}
                </h3>
                <p id={`desc-${index}`} className="text-sm text-green-200 leading-relaxed opacity-80">
                  {option.shortDescription}
                </p>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Voice Input Button */}
        <div className="fixed bottom-8 right-8 z-50">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={startListening}
            disabled={isListening}
            aria-label={isListening ? 'Listening...' : t('accessibility.voiceInput', currentLanguage)}
            aria-pressed={isListening}
            className={`min-w-[64px] min-h-[64px] w-16 h-16 rounded-full shadow-lg flex items-center justify-center text-white transition-all focus:ring-2 focus:ring-white focus:ring-offset-2 focus:outline-none ${
              isListening
                ? 'bg-red-500 animate-pulse'
                : `bg-green-600 hover:bg-green-700 ${highContrastMode ? 'border-2 border-white' : ''}`
            }`}
          >
            <MicrophoneIcon className="w-7 h-7" aria-hidden="true" />
            <span className="sr-only">
              {isListening ? 'Listening for voice input' : 'Start voice input'}
            </span>
          </motion.button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(236deg,#2A805B_7.46%,#143830_92.54%)] flex flex-col">
      {/* Header */}
      <div className={`bg-white/10 backdrop-blur-sm border-b border-white/20 px-6 py-4 flex items-center ${highContrastMode ? 'contrast-more' : ''}`}>
        <nav aria-label="breadcrumb" className="sr-only">
          <ol>
            {breadcrumbs.map((crumb, idx) => (
              <li key={idx}>{crumb}</li>
            ))}
          </ol>
        </nav>
        <div className="flex items-center">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleBackToMenu}
            className="flex items-center space-x-2 px-6 py-3 bg-white/20 backdrop-blur-sm text-white rounded-xl hover:bg-white/30 transition-colors border border-white/30"
          >
            <HomeIcon className="w-6 h-6" />
            <span className="text-body-bold font-body-bold">{t('ui.home', currentLanguage)}</span>
          </motion.button>
        </div>

        <div className="flex-1 flex justify-center">
          <h1 className="text-heading-2 font-heading-2 text-white">{t('ui.sconiaChat', currentLanguage)}</h1>
        </div>

        <div className="flex items-center space-x-4">
          {/* Accessibility Toolbar */}
          <div className="flex items-center space-x-2" role="toolbar" aria-label={t('accessibility.settings', currentLanguage)}>
            {/* Language selector */}
            <label className="sr-only" htmlFor="lang-select">{t('settings.language', currentLanguage)}</label>
            <div className="relative">
              <select
                id="lang-select"
                aria-label={t('settings.language', currentLanguage)}
                className="px-3 py-2 rounded-lg bg-white/20 text-white border border-white/30 min-w-[120px]"
                value={currentLanguage}
                onChange={(e) => setCurrentLanguage(e.target.value as any)}
              >
                <option value="en">English</option>
                <option value="ha">Hausa</option>
                <option value="yo">Yoruba</option>
                <option value="ig">Igbo</option>
              </select>
            </div>

            {/* Font size controls */}
            <div className="flex items-center space-x-1">
              <button
                type="button"
                aria-label="Decrease font size"
                className="p-2 rounded-lg bg-white/20 text-white border border-white/30"
                onClick={() => setFontSize(prev => prev === 'large' ? 'medium' : 'small')}
              >
                <MagnifyingGlassMinusIcon className="w-5 h-5" />
              </button>
              <button
                type="button"
                aria-label="Increase font size"
                className="p-2 rounded-lg bg-white/20 text-white border border-white/30"
                onClick={() => setFontSize(prev => prev === 'small' ? 'medium' : 'large')}
              >
                <MagnifyingGlassPlusIcon className="w-5 h-5" />
              </button>
            </div>

            {/* High contrast toggle */}
            <button
              type="button"
              aria-pressed={highContrastMode}
              aria-label={t('settings.highContrast', currentLanguage)}
              className={`p-2 rounded-lg border ${highContrastMode ? 'bg-yellow-300 text-black border-yellow-400' : 'bg-white/20 text-white border-white/30'}`}
              onClick={() => setHighContrastMode(!highContrastMode)}
            >
              <EyeIcon className="w-5 h-5" />
            </button>
          </div>
          {isSpeaking && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={stopSpeaking}
              className="flex items-center space-x-2 px-4 py-2 bg-red-500/80 backdrop-blur-sm text-white rounded-lg hover:bg-red-600/80 transition-colors border border-red-400/30"
            >
              <SpeakerWaveIcon className="w-5 h-5" />
              <span>{t('ui.stopSpeaking', currentLanguage)}</span>
            </motion.button>
          )}
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-3xl rounded-2xl p-6 ${
                  message.type === 'user'
                    ? 'bg-green-600 text-white shadow-lg'
                    : 'bg-white/95 backdrop-blur-sm shadow-lg border border-white/20'
                }`}>
                  <div className="text-body font-body leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </div>

                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200/50">
                      <p className="text-body-bold font-body-bold text-gray-700 mb-3">{t('ui.sources', currentLanguage)}</p>
                      <div className="space-y-2">
                        {message.sources.map((source, index) => {
                          // Create a meaningful title from document_id or use title if not generic
                          const getSourceTitle = () => {
                            if (source.title && !source.title.startsWith('Legal Reference')) {
                              return source.title;
                            }
                            
                            // Extract meaningful name from document_id
                            if (source.document_id) {
                              const idParts = source.document_id.split('_');
                              if (idParts.includes('constitution')) {
                                return 'Constitution of Nigeria 1999';
                              } else if (idParts.includes('case')) {
                                return 'Supreme Court Case Law';
                              } else if (idParts.includes('procedure')) {
                                return 'Court Procedures';
                              }
                              // Fallback: capitalize and join parts
                              return idParts.map(part => 
                                part.charAt(0).toUpperCase() + part.slice(1)
                              ).join(' ');
                            }
                            
                            return `${source.document_type?.charAt(0).toUpperCase() + source.document_type?.slice(1)} Document`;
                          };
                          
                          return (
                          <div key={index} className="bg-gray-50 rounded-lg p-3 border-l-4 border-green-500">
                            <div className="flex justify-between items-start mb-1">
                              <h4 className="text-sm font-semibold text-gray-800 flex-1">
                                {getSourceTitle()}
                              </h4>
                              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full ml-2 flex-shrink-0">
                                {Math.round((source.relevance_score / 1.2) * 100)}% relevant
                              </span>
                            </div>
                            {source.content_snippet && (
                              <p className="text-xs text-gray-600 leading-relaxed mt-2">
                                "{source.content_snippet.length > 150 
                                  ? source.content_snippet.substring(0, 150).trim() + '...' 
                                  : source.content_snippet.trim()
                                }"
                              </p>
                            )}
                            <div className="mt-2 flex items-center justify-between">
                              {source.document_type && (
                                <span className="inline-block text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded">
                                  {source.document_type.replace('_', ' ').toUpperCase()}
                                </span>
                              )}
                              {source.document_id && (
                                <span className="text-xs text-gray-400 font-mono">
                                  ID: {source.document_id.split('_').slice(-1)[0]}
                                </span>
                              )}
                            </div>
                          </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  
                  {message.quickOptions && message.quickOptions.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200/50">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {message.quickOptions.map((option, index) => (
                          <motion.button
                            key={index}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => handleSendMessage(option.text)}
                            className="px-4 py-3 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-left text-body-bold font-body-bold border border-green-200"
                          >
                            {option.text}
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-white/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-500"></div>
                  <span className="text-body font-body text-gray-700">{t('ui.thinking', currentLanguage)}</span>
                </div>
              </div>
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white/10 backdrop-blur-sm border-t border-white/20 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(currentInput)}
                placeholder={t('ui.inputPlaceholder', currentLanguage)}
                className="w-full px-6 py-4 text-body font-body bg-white/95 backdrop-blur-sm border border-white/30 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent shadow-lg"
                disabled={isLoading}
              />
            </div>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={startListening}
              disabled={isListening || isLoading}
              className={`p-4 rounded-xl transition-colors ${
                isListening
                  ? 'bg-red-500 text-white animate-pulse shadow-lg'
                  : 'bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 border border-white/30'
              }`}
            >
              <MicrophoneIcon className="w-6 h-6" />
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleSendMessage(currentInput)}
              disabled={!currentInput.trim() || isLoading}
              className="px-8 py-4 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-body-bold font-body-bold shadow-lg"
            >
              {t('ui.send', currentLanguage)}
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KioskMode;
