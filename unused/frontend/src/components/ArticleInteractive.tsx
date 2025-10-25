import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/ArticleInteractive.css';

interface Argument {
  title: string;
  content: string;
  type: 'pro' | 'con';
}

interface Question {
  id: number;
  text: string;
  options: string[];
  answer: number;
  explanation: string;
}

interface ArticleData {
  id: number;
  title: string;
  zh_title?: string;
  source: string;
  pub_date: string;
  description: string;
  image?: string | null;
  content?: string;
}

interface InteractiveContent {
  [key: string]: {
    summary: string;
    keyTopics: string[];
    backgroundInfo: string;
    proArguments: Argument[];
    conArguments: Argument[];
    questions: Question[];
  };
}

interface Props {
  articleId: number;
  onBack: () => void;
}

const difficultyLabels = {
  easy: 'Elementary Level (Grades 3-5)',
  mid: 'Middle School Level (Grades 6-8)',
  hard: 'High School Level (Grades 9-12)',
};

const ArticleInteractive: React.FC<Props> = ({ articleId, onBack }) => {
  const [article, setArticle] = useState<ArticleData | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<'easy' | 'mid' | 'hard'>('mid');
  const [loading, setLoading] = useState(true);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});

  // Placeholder content for different difficulty levels
  const interactiveContent: InteractiveContent = {
    easy: {
      summary: 'Big tech companies like Meta, Nvidia, and OpenAI are working together to make computers work better for artificial intelligence (AI). They want to use a common way for computers to talk to each other called Ethernet, which is like the internet cables you might have at home. Right now, most AI computers use a special system called InfiniBand that is very fast but expensive. The companies think Ethernet can be just as good and cheaper. Many engineers already know how to use Ethernet, so it might be easier to build big AI systems. They will meet regularly to decide how to make Ethernet work best for AI. Some companies have already made new products using Ethernet for AI. This could help make AI technology available to more people.',
      keyTopics: ['computers', 'AI', 'Ethernet', 'companies', 'work together', 'fast', 'cheaper', 'engineers', 'systems', 'technology'],
      backgroundInfo: 'Computers need to talk to each other very quickly. AI computers especially need super fast connections. For a long time, one special type of connection called InfiniBand was the fastest. But it costs a lot of money. Now some companies think regular Ethernet could work just as well and cost much less. Ethernet is already used in homes and offices everywhere, so people know how to use it already.',
      proArguments: [
        {
          title: 'Better for Everyone',
          content: 'Ethernet is cheaper and easier to understand. Many people already know how it works. This means more companies can use AI.',
          type: 'pro'
        },
        {
          title: 'Works Well',
          content: 'Ethernet is already proven technology used everywhere in the world. Companies have been using it for many years successfully.',
          type: 'pro'
        }
      ],
      conArguments: [
        {
          title: 'Maybe Not Fast Enough',
          content: 'InfiniBand is super specialized for AI work. Ethernet might not be as fast for the biggest AI computers.',
          type: 'con'
        },
        {
          title: 'Takes Time to Change',
          content: 'Companies have already spent lots of money on InfiniBand systems. Changing to Ethernet could be complicated and expensive.',
          type: 'con'
        }
      ],
      questions: [
        {
          id: 1,
          text: 'What are the big companies trying to improve for AI?',
          options: ['A) Computer games', 'B) How computers talk to each other', 'C) Phone batteries', 'D) Television screens'],
          answer: 1,
          explanation: 'The companies are working on how computers communicate in AI systems.'
        },
        {
          id: 2,
          text: 'What common technology do they want to use?',
          options: ['A) Bluetooth', 'B) Wi-Fi', 'C) Ethernet', 'D) Radio waves'],
          answer: 2,
          explanation: 'They want to use Ethernet for AI computer connections because it is common and cheaper.'
        },
        {
          id: 3,
          text: 'Which system do most AI computers use now?',
          options: ['A) InfiniBand', 'B) USB', 'C) HDMI', 'D) Thunderbolt'],
          answer: 0,
          explanation: 'InfiniBand is currently used in about 80% of AI systems, but it is very expensive.'
        },
        {
          id: 4,
          text: 'Why might Ethernet be better according to the article?',
          options: ['A) It\'s cheaper and more familiar', 'B) It\'s newer and shinier', 'C) It works only at night', 'D) It needs special cables'],
          answer: 0,
          explanation: 'Ethernet is more cost-effective and engineers already know how to use it, making it more accessible.'
        },
        {
          id: 5,
          text: 'What will the companies do regularly?',
          options: ['A) Play video games', 'B) Have meetings to decide standards', 'C) Build new phones', 'D) Design car engines'],
          answer: 1,
          explanation: 'They will meet regularly to define how Ethernet should work best for AI applications.'
        }
      ]
    },
    mid: {
      summary: 'The Open Compute Project has launched a major initiative called Ethernet for Scale-Up Networking (ESUN) that brings together technology giants including Meta, Nvidia, AMD, Cisco, and OpenAI. This collaboration aims to develop open standards for high-performance Ethernet networks specifically designed for artificial intelligence clusters. Currently, InfiniBand dominates the AI networking market, handling approximately 80% of connections between GPUs and AI accelerators in data centers. However, the ESUN group believes Ethernet offers significant advantages including maturity, cost-effectiveness, and better interoperability between different systems. Unlike proprietary systems like InfiniBand, Ethernet\'s widespread familiarity among engineers could simplify managing massive AI workloads. The initiative builds on previous work from OCP\'s SUE-Transport program and will focus on defining standards for switch behavior, protocol headers, error handling, and lossless data transfer. Several companies have already developed Ethernet-based AI products, such as Broadcom\'s Tomahawk Ultra switch and Nvidia\'s Spectrum-X platform. While Ethernet shows promise, it must prove it can match InfiniBand\'s performance under demanding AI workloads where latency and reliability are critical.',
      keyTopics: ['Open Compute Project', 'ESUN', 'InfiniBand', 'AI clusters', 'GPUs', 'interoperability', 'standards', 'data centers', 'latency', 'workloads'],
      backgroundInfo: 'As artificial intelligence systems become more complex, they require massive computing power distributed across thousands of processors working together. These processors need extremely fast and reliable ways to communicate with each other. Currently, most high-performance AI systems use InfiniBand technology for these connections, but it\'s expensive and proprietary. Ethernet is the standard networking technology used in most offices and homes, but it hasn\'t been optimized for the extreme demands of AI computing until now.',
      proArguments: [
        {
          title: 'Democratizing AI Infrastructure',
          content: 'Ethernet could democratize AI infrastructure by making it more affordable and accessible. Its open standards would allow different vendors\' equipment to work together seamlessly, reducing vendor lock-in. Cost savings from using standardized components could accelerate AI adoption across industries.',
          type: 'pro'
        },
        {
          title: 'Established Expertise',
          content: 'The widespread knowledge of Ethernet among IT professionals would make AI systems easier to maintain and scale. Organizations already have existing infrastructure and expertise they can leverage.',
          type: 'pro'
        }
      ],
      conArguments: [
        {
          title: 'Performance Challenges',
          content: 'InfiniBand has proven performance advantages for high-performance computing that Ethernet may struggle to match. Ethernet may introduce higher latency or reliability issues under extreme AI workloads.',
          type: 'con'
        },
        {
          title: 'Switching Costs',
          content: 'The established infrastructure and expertise around InfiniBand creates significant switching costs. Coordination required between multiple standards bodies could slow innovation.',
          type: 'con'
        }
      ],
      questions: [
        {
          id: 1,
          text: 'What percentage of AI infrastructure does InfiniBand currently dominate?',
          options: ['A) About 50%', 'B) About 65%', 'C) About 80%', 'D) About 95%'],
          answer: 2,
          explanation: 'InfiniBand accounts for roughly 80% of the infrastructure connecting GPUs and accelerators in AI systems.'
        },
        {
          id: 2,
          text: 'Which organization is leading the ESUN initiative?',
          options: ['A) IEEE', 'B) Ultra Ethernet Consortium', 'C) Open Compute Project', 'D) Internet Engineering Task Force'],
          answer: 2,
          explanation: 'The Open Compute Project (OCP) announced the ESUN initiative and is coordinating the effort.'
        },
        {
          id: 3,
          text: 'What previous OCP program does ESUN build upon?',
          options: ['A) AI-Transport', 'B) SUE-Transport', 'C) GPU-Networking', 'D) Data-Center Connect'],
          answer: 1,
          explanation: 'ESUN builds on earlier work under OCP\'s SUE-Transport program that explored Ethernet for multi-processor systems.'
        },
        {
          id: 4,
          text: 'What is a key advantage of Ethernet over InfiniBand mentioned in the article?',
          options: ['A) Higher maximum speed', 'B) Better security features', 'C) Widespread familiarity among engineers', 'D) Smaller physical size'],
          answer: 2,
          explanation: 'Ethernet\'s widespread familiarity among engineers could help reduce complexity in managing AI workloads.'
        },
        {
          id: 5,
          text: 'Which organizations will ESUN coordinate with according to the article?',
          options: ['A) W3C and ISO', 'B) Ultra Ethernet Consortium and IEEE', 'C) ITU and IETF', 'D) ANSI and ECMA'],
          answer: 1,
          explanation: 'ESUN plans to coordinate with the Ultra Ethernet Consortium and IEEE 802.3 standards body.'
        }
      ]
    },
    hard: {
      summary: 'The Open Compute Project\'s groundbreaking Ethernet for Scale-Up Networking (ESUN) initiative represents a strategic challenge to InfiniBand\'s long-standing dominance in high-performance AI networking. This coalition of industry titans—including Meta, Nvidia, AMD, Cisco, and OpenAI—seeks to establish open Ethernet standards capable of supporting the immense data transfer requirements of contemporary artificial intelligence clusters. InfiniBand currently commands approximately 80% market share in AI infrastructure interconnects, having established itself as the de facto standard for low-latency, high-throughput communication between GPUs and accelerators. The ESUN consortium posits that Ethernet\'s technological maturity, cost-efficiency, and inherent interoperability present a compelling alternative that could democratize AI infrastructure while reducing total cost of ownership. This initiative builds substantively upon OCP\'s prior SUE-Transport research into Ethernet transport mechanisms for multiprocessor architectures. The working group will concentrate on standardizing critical elements including switch behavioral specifications, protocol header frameworks, sophisticated error handling methodologies, and guaranteed lossless data transfer capabilities. Concurrently, they will investigate how network topology influences load balancing algorithms and memory ordering consistency within distributed GPU systems. ESUN intends to maintain strategic alignment with both the Ultra Ethernet Consortium and IEEE 802.3 standards body to ensure ecosystem-wide coherence. Early market indicators demonstrate momentum, with Broadcom\'s Tomahawk Ultra switch achieving 77 billion packets per second throughput and Nvidia\'s Spectrum-X platform integrating Ethernet with specialized acceleration hardware. Nevertheless, the fundamental challenge remains: can Ethernet demonstrate performance parity with InfiniBand under the most demanding AI workloads where nanosecond-level latency and absolute reliability are non-negotiable? ESUN\'s ultimate success will hinge on balancing the virtues of open standards against the uncompromising performance requirements of cutting-edge artificial intelligence applications.',
      keyTopics: ['proprietary systems', 'interoperability', 'latency sensitivity', 'ecosystem alignment', 'load balancing algorithms', 'memory ordering consistency', 'throughput', 'total cost of ownership', 'vendor lock-in', 'performance parity'],
      backgroundInfo: 'The exponential growth of artificial intelligence, particularly in large language models and generative AI, has created unprecedented demands on data center networking infrastructure. AI training clusters now routinely comprise thousands of GPUs requiring continuous, high-bandwidth, low-latency communication. InfiniBand, developed in the late 1990s, has dominated this space due to its superior performance characteristics, but as a proprietary technology, it creates vendor dependency and higher costs. Ethernet, while ubiquitous in general computing, has historically been inadequate for the rigorous demands of AI workloads due to higher latency and less deterministic performance. The ESUN initiative represents a concerted effort to bridge this performance gap while leveraging Ethernet\'s economies of scale and open standards advantage.',
      proArguments: [
        {
          title: 'Economic Transformation',
          content: 'The transition to Ethernet-based AI networking could fundamentally reshape the economic landscape of artificial intelligence infrastructure. By leveraging an open standards approach, ESUN could dramatically reduce total cost of ownership while increasing flexibility in system design and vendor selection. Ethernet\'s ubiquitous presence in IT ecosystems means existing expertise and tooling can be repurposed, accelerating implementation timelines. The interoperability between different vendors\' equipment could foster healthier competition and innovation.',
          type: 'pro'
        },
        {
          title: 'Architectural Flexibility',
          content: 'As AI workloads become more diverse, Ethernet\'s flexibility could prove advantageous for hybrid workloads that combine AI with traditional computing tasks. The long-term strategic benefit includes reducing dependency on single-vendor solutions and creating a more resilient AI infrastructure ecosystem. Open standards enable ecosystem-wide optimization without proprietary constraints.',
          type: 'pro'
        }
      ],
      conArguments: [
        {
          title: 'Technical & Architectural Barriers',
          content: 'Significant technical barriers threaten ESUN\'s objectives. InfiniBand\'s architectural advantages—including native support for remote direct memory access (RDMA), superior congestion control mechanisms, and deterministic latency—have been refined over decades specifically for high-performance computing. Ethernet must overcome fundamental architectural limitations to achieve comparable performance, potentially requiring complex software-defined networking overlays that introduce their own management complexity.',
          type: 'con'
        },
        {
          title: 'Ecosystem Entrenchment',
          content: 'The entrenched ecosystem around InfiniBand, including specialized expertise, optimized software stacks, and proven reliability at scale, creates substantial switching costs and resistance to change. The coordination required across multiple standards bodies and competing corporate interests could result in compromised specifications that satisfy nobody. The risk exists that by attempting to be everything to everyone, Ethernet-for-AI might deliver mediocre performance that excels in neither cost nor capability.',
          type: 'con'
        }
      ],
      questions: [
        {
          id: 1,
          text: 'What fundamental architectural advantage of InfiniBand poses the greatest challenge for Ethernet in AI workloads?',
          options: ['A) Higher maximum bandwidth capacity', 'B) Native support for remote direct memory access', 'C) Compatibility with existing data center infrastructure', 'D) Reduced power consumption characteristics'],
          answer: 1,
          explanation: 'InfiniBand\'s native RDMA support provides significant latency advantages that Ethernet must match through additional protocol layers or architectural changes.'
        },
        {
          id: 2,
          text: 'How does the ESUN initiative aim to address potential fragmentation in Ethernet standards development?',
          options: ['A) By creating a single governing authority for all networking standards', 'B) Through coordination with Ultra Ethernet Consortium and IEEE', 'C) By mandating exclusive use of specific vendor implementations', 'D) Through legislative lobbying for standardized protocols'],
          answer: 1,
          explanation: 'ESUN plans to coordinate with both the Ultra Ethernet Consortium and IEEE 802.3 to ensure alignment across the Ethernet ecosystem.'
        },
        {
          id: 3,
          text: 'What economic phenomenon could Ethernet\'s adoption potentially create in AI infrastructure markets?',
          options: ['A) Increased vendor lock-in and proprietary solutions', 'B) Reduction in total cost of ownership through competition', 'C) Higher software licensing fees for network management', 'D) Decreased need for specialized IT personnel'],
          answer: 1,
          explanation: 'Open Ethernet standards could reduce TCO by enabling multi-vendor competition and leveraging existing Ethernet expertise.'
        },
        {
          id: 4,
          text: 'What technical aspect of network design will ESUN specifically investigate regarding GPU systems?',
          options: ['A) Thermal management of network switches', 'B) Power efficiency metrics for different topologies', 'C) Impact on load balancing and memory ordering', 'D) Electromagnetic interference between components'],
          answer: 2,
          explanation: 'ESUN will study how network design affects load balancing and memory ordering consistency within GPU-based systems.'
        },
        {
          id: 5,
          text: 'What strategic consideration might delay enterprise adoption of Ethernet for mission-critical AI workloads?',
          options: ['A) Lack of physical cabling standards', 'B) Unproven reliability under extreme scale conditions', 'C) Incompatibility with existing server hardware', 'D) Higher initial acquisition costs compared to InfiniBand'],
          answer: 1,
          explanation: 'Enterprises may hesitate until Ethernet demonstrates reliability comparable to InfiniBand under production AI workloads at extreme scale.'
        }
      ]
    }
  };

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`http://localhost:8008/api/articles/${articleId}`);
        setArticle(response.data);
      } catch (err) {
        console.error('Failed to load article', err);
      } finally {
        setLoading(false);
      }
    };

    fetchArticle();
  }, [articleId]);

  const handleAnswerSelect = (questionId: number, answerIndex: number) => {
    setSelectedAnswers({
      ...selectedAnswers,
      [questionId]: answerIndex,
    });
  };

  if (loading) {
    return (
      <div className="article-interactive-wrapper">
        <button onClick={onBack} className="interactive-back-button">
          ← Back to Articles
        </button>
        <div className="loading">Loading article...</div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="article-interactive-wrapper">
        <button onClick={onBack} className="interactive-back-button">
          ← Back to Articles
        </button>
        <div className="error">Article not found</div>
      </div>
    );
  }

  const content = interactiveContent[selectedDifficulty];

  return (
    <div className="article-interactive-wrapper">
      <button onClick={onBack} className="interactive-back-button">
        ← Back to Articles
      </button>

      {/* Header */}
      <div className="interactive-header">
        <h1>{article.title}</h1>
        <p>Choose your education level to customize the content</p>
      </div>

      {/* Difficulty Level Control */}
      <div className="interactive-controls">
        <div className="control-group">
          <label>📚 Education Level:</label>
          <div className="difficulty-buttons">
            {(Object.keys(difficultyLabels) as Array<'easy' | 'mid' | 'hard'>).map((level) => (
              <button
                key={level}
                className={`difficulty-btn ${selectedDifficulty === level ? 'active' : ''}`}
                onClick={() => setSelectedDifficulty(level)}
              >
                {difficultyLabels[level]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="interactive-content">
        {/* Summary */}
        <section className="interactive-section">
          <h2 className="interactive-section-title">
            <span className="section-icon">📖</span>
            Summary
          </h2>
          <div className="summary-box">
            <p>{content.summary}</p>
          </div>
        </section>

        {/* Key Topics */}
        <section className="interactive-section">
          <h2 className="interactive-section-title">
            <span className="section-icon">🎯</span>
            Key Topics
          </h2>
          <div className="keywords-container">
            {content.keyTopics.map((topic, index) => (
              <span key={index} className="keyword-tag">
                {topic}
              </span>
            ))}
          </div>
        </section>

        {/* Background Information */}
        {selectedDifficulty !== 'easy' && (
          <section className="interactive-section">
            <h2 className="interactive-section-title">
              <span className="section-icon">📚</span>
              Background Information
            </h2>
            <div className="background-box">
              <p>{content.backgroundInfo}</p>
            </div>
          </section>
        )}

        {/* Different Perspectives */}
        {selectedDifficulty !== 'easy' && (
          <section className="interactive-section">
            <h2 className="interactive-section-title">
              <span className="section-icon">💭</span>
              Different Perspectives
            </h2>
            <div className="perspectives-grid">
              <div className="perspective-column">
                <h3 className="perspective-title pro">✅ Supporting Arguments</h3>
                {content.proArguments.map((arg, index) => (
                  <div key={index} className="argument-box pro">
                    <h4>{arg.title}</h4>
                    <p>{arg.content}</p>
                  </div>
                ))}
              </div>
              <div className="perspective-column">
                <h3 className="perspective-title con">❌ Counter Arguments</h3>
                {content.conArguments.map((arg, index) => (
                  <div key={index} className="argument-box con">
                    <h4>{arg.title}</h4>
                    <p>{arg.content}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Quiz */}
        <section className="interactive-section">
          <h2 className="interactive-section-title">
            <span className="section-icon">❓</span>
            Check Your Understanding
          </h2>
          <div className="quiz-container">
            {content.questions.map((question, qIndex) => (
              <div key={question.id} className="quiz-item">
                <div className="quiz-header">
                  <span className="question-number">Q{qIndex + 1}</span>
                  <p className="question-text">{question.text}</p>
                </div>

                <div className="options-container">
                  {question.options.map((option, optIndex) => (
                    <label key={optIndex} className="option">
                      <input
                        type="radio"
                        name={`q${question.id}`}
                        checked={selectedAnswers[question.id] === optIndex}
                        onChange={() => handleAnswerSelect(question.id, optIndex)}
                      />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>

                {selectedAnswers[question.id] !== undefined && (
                  <div className={`answer-feedback ${selectedAnswers[question.id] === question.answer ? 'correct' : 'incorrect'}`}>
                    <div className="feedback-header">
                      {selectedAnswers[question.id] === question.answer ? (
                        <>
                          <span className="feedback-icon">✓</span>
                          <strong>Correct!</strong>
                        </>
                      ) : (
                        <>
                          <span className="feedback-icon">✗</span>
                          <strong>Not quite right</strong>
                        </>
                      )}
                    </div>
                    <p className="feedback-text">{question.explanation}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default ArticleInteractive;
