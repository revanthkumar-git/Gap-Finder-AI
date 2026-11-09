import { useEffect, useRef, useState } from "react";
import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || "/api" });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const groqKey = sessionStorage.getItem("groqApiKey");
  if (groqKey) config.headers["X-Groq-API-Key"] = groqKey;
  return config;
});

type Topic = { id: number; name: string; exam_weight: number };
type Question = { id: number; topic: string; kind: string; prompt: string; options: string[]; citations: string[] };
type Gap = { topic: string; score_pct: number; level: string; evidence: string };
type AnswerReview = { question: string; submitted_answer: string; correct: boolean; points_earned: number; points_possible: number; correct_answer: string; explanation: string; citations: string[] };
type ReportData = { attempt_id: number; correct_count: number; total: number; score_points: number; max_points: number; score_pct: number; topics: Gap[]; answers: AnswerReview[] };
type AttemptSummary = { id: number; correct_count: number; total: number; score_points: number; max_points: number; score_pct: number };
type PlanData = { topic: string; hours: number; level: string; suggestion: string; days: number };
type ChatMessage = { role: "user" | "assistant"; content: string };

function messageOf(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    return typeof detail === "string" ? detail : error.message;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const passwordRevealTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [name, setName] = useState("");
  const [registering, setRegistering] = useState(false);
  const [section, setSection] = useState("Overview");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [topics, setTopics] = useState<Topic[]>([]);
  const [documents, setDocuments] = useState<{ id: number; filename: string; kind: string }[]>([]);
  const [numQuestions, setNumQuestions] = useState<5 | 10 | 15 | 20>(10);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [report, setReport] = useState<ReportData | null>(null);
  const [attempts, setAttempts] = useState<AttemptSummary[]>([]);
  const [plan, setPlan] = useState<PlanData[]>([]);
  const [schedule, setSchedule] = useState<{ day: number; topic: string; hours: number }[]>([]);
  const [chatText, setChatText] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [groqKey, setGroqKey] = useState(() => sessionStorage.getItem("groqApiKey") || "");
  const [showGroqKey, setShowGroqKey] = useState(false);
  const groqKeyRevealTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [keyNotice, setKeyNotice] = useState("");
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    const [topicResponse, documentResponse, progressResponse] = await Promise.all([
      api.get("/topics"),
      api.get("/documents"),
      api.get("/dashboard/progress"),
    ]);
    setTopics(topicResponse.data);
    setDocuments(documentResponse.data);
    setAttempts(progressResponse.data.attempts);
    if (progressResponse.data.attempts.length && !report) {
      const latest = progressResponse.data.attempts[0];
      const latestReport = await api.get(`/gap-report/${latest.id}`);
      setReport(latestReport.data);
    }
  };

  useEffect(() => {
    if (token) loadData().catch((e) => setError(messageOf(e)));
  }, [token]);

  useEffect(() => () => {
    if (passwordRevealTimer.current) clearTimeout(passwordRevealTimer.current);
    if (groqKeyRevealTimer.current) clearTimeout(groqKeyRevealTimer.current);
  }, []);

  const revealForOneSecond = (
    setVisible: (visible: boolean) => void,
    timer: React.MutableRefObject<ReturnType<typeof setTimeout> | null>,
  ) => {
    if (timer.current) clearTimeout(timer.current);
    setVisible(true);
    timer.current = setTimeout(() => {
      setVisible(false);
      timer.current = null;
    }, 1000);
  };

  const authenticate = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      const { data } = await api.post(registering ? "/auth/register" : "/auth/login", {
        email,
        password,
        name,
      });
      localStorage.setItem("token", data.token);
      setToken(data.token);
      setNotice(`Welcome${data.user.name ? `, ${data.user.name}` : ""}.`);
    } catch (e) {
      setError(messageOf(e));
    }
  };

  const upload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.set("file", file);
    form.set("kind", (document.getElementById("document-kind") as HTMLSelectElement).value);
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const { data } = await api.post("/documents/upload", form);
      setNotice(`Indexed ${data.filename} (${data.chunks} source chunks).`);
      await loadData();
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setLoading(false);
      event.target.value = "";
    }
  };

  const generateQuiz = async () => {
    setLoading(true);
    setError("");
    setReport(null);
    try {
      const { data } = await api.post("/quiz/generate", { num_questions: numQuestions, question_types: ["mcq", "short_answer"] });
      setQuestions(data.questions);
      setAnswers({});
      setSection("Quiz");
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setLoading(false);
    }
  };

  const submitQuiz = async () => {
    setLoading(true);
    try {
      const { data } = await api.post("/quiz/submit", {
        answers: questions.map((question) => ({ question_id: question.id, answer: answers[question.id] || "" })),
      });
      const result = await api.get(`/gap-report/${data.attempt_id}`);
      setReport(result.data);
      const progress = await api.get("/dashboard/progress");
      setAttempts(progress.data.attempts);
      setQuestions([]);
      setSection("Report");
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setLoading(false);
    }
  };

  const createPlan = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true);
    try {
      const { data } = await api.post("/study-plan/generate", {
        days: Number(form.get("days")),
        hours_per_day: Number(form.get("hours")),
      });
      setPlan(data.items);
      setSchedule(data.schedule);
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setLoading(false);
    }
  };

  const askAssistant = async (event: React.FormEvent) => {
    event.preventDefault();
    const message = chatText.trim();
    if (!message || loading) return;
    const history = chatMessages.slice(-8);
    setChatMessages([...chatMessages, { role: "user", content: message }]);
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/chat", { message, history });
      setChatMessages((messages) => [...messages, { role: "assistant", content: data.reply }]);
      setChatText("");
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <main className="auth-page">
        <form className="auth-card" onSubmit={authenticate}>
          <div className="brand-mark">GD</div>
          <p className="eyebrow">YOUR PERSONAL REVISION COACH</p>
          <h1>GapFinder AI</h1>
          <p className="muted">Find knowledge gaps. Focus your revision. Improve with every retest.</p>
          {registering && <label>Name<input value={name} onChange={(e) => setName(e.target.value)} required /></label>}
          <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
          <label>Password<span className="secret-input"><input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} minLength={registering ? 8 : 1} required /><button type="button" className="secret-toggle" onClick={() => revealForOneSecond(setShowPassword, passwordRevealTimer)} aria-label="Reveal password for one second" aria-pressed={showPassword} title="Reveal password for one second"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" />{!showPassword && <path d="m4 4 16 16" />}</svg></button></span></label>
          {error && <p className="error">{error}</p>}
          <button className="primary full" disabled={loading}>{registering ? "Create account" : "Sign in"}</button>
          <button type="button" className="link-button" onClick={() => setRegistering(!registering)}>
            {registering ? "Already registered? Sign in" : "New here? Create an account"}
          </button>
        </form>
      </main>
    );
  }

  const saveGroqKey = (event: React.FormEvent) => {
    event.preventDefault();
    const key = groqKey.trim();
    if (!key) {
      setError("Enter a Groq API key, or clear the saved key.");
      return;
    }
    sessionStorage.setItem("groqApiKey", key);
    setGroqKey(key);
    setError("");
    setKeyNotice("Key saved for this browser tab. It is not stored on the server.");
  };

  const clearGroqKey = () => {
    sessionStorage.removeItem("groqApiKey");
    setGroqKey("");
    setKeyNotice("Browser key cleared. The server will use its configured key, if any.");
  };

  const nav = ["Overview", "Materials", "Quiz", "Report", "Study plan", "Study assistant", "Settings"];
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark small">GF</div><div><b>GapFinder AI</b><small>AI revision coach</small></div></div>
        <nav>{nav.map((item) => <button key={item} className={section === item ? "nav-item active" : "nav-item"} onClick={() => { setSection(item); setError(""); }}>{item}</button>)}</nav>
        <button className="nav-item signout" onClick={() => { localStorage.removeItem("token"); setToken(""); setChatMessages([]); }}>Sign out</button>
      </aside>
      <main className="content">
        <header className="topbar"><div><p className="eyebrow">GAPFINDER AI</p><h1>{section}</h1></div><div className="avatar">S</div></header>
        {error && <div className="alert error">{error}</div>}
        {notice && <div className="alert success">{notice}</div>}
        {section === "Settings" && <section className="card settings-card"><p className="eyebrow">AI PROVIDER</p><h2>Groq API key</h2><p className="muted">Enter a Groq key to enable AI-generated quizzes, syllabus analysis, exam-paper weighting, and the study assistant. The key stays in this browser tab and is sent only to this app's API; it is not saved to the server.</p><form className="settings-form" onSubmit={saveGroqKey}><label>API key<span className="secret-input"><input type={showGroqKey ? "text" : "password"} autoComplete="new-password" spellCheck={false} value={groqKey} onChange={(event) => { setGroqKey(event.target.value); setKeyNotice(""); }} placeholder="gsk_…" /><button type="button" className="secret-toggle" onClick={() => revealForOneSecond(setShowGroqKey, groqKeyRevealTimer)} aria-label="Reveal Groq API key for one second" aria-pressed={showGroqKey} title="Reveal key for one second"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" />{!showGroqKey && <path d="m4 4 16 16" />}</svg></button></span></label><div className="settings-actions"><button className="primary" disabled={loading}>Save key for this tab</button><button type="button" className="secondary" onClick={clearGroqKey}>Clear key</button></div></form>{keyNotice && <p className="key-notice" role="status">{keyNotice}</p>}<p className="security-note">Use a trusted HTTPS connection before entering a key on a hosted site. A key placed in a browser is available to that browser session.</p></section>}
        {section === "Overview" && <section>
          <div className="welcome"><div><p className="eyebrow light">YOUR NEXT BEST STEP</p><h2>Study smarter, not longer.</h2><p>Upload your materials, diagnose what needs work, and get a plan that adapts.</p><button className="light-button" onClick={() => setSection("Materials")}>Add study materials →</button></div><div className="welcome-icon">✦</div></div>
          <div className="stats"><article><span>Uploaded materials</span><strong>{documents.length}</strong><small>Private to your account</small></article><article><span>Mapped topics</span><strong>{topics.length}</strong><small>From your syllabus</small></article><article><span>Latest result</span><strong>{attempts.length ? `${attempts[0].score_points}/${attempts[0].max_points} pts` : "—"}</strong><small>{attempts.length ? `${attempts[0].score_pct}% · ${attempts.length} recent attempt${attempts.length === 1 ? "" : "s"}` : "Take a quiz to begin"}</small></article></div>
          <div className="card"><h2>Topic map</h2>{topics.length ? <div className="topic-list">{topics.map((topic) => <div key={topic.id}><span>{topic.name}</span><span>{Math.round(topic.exam_weight * 100)}% exam weight</span></div>)}</div> : <p className="muted">Upload a syllabus to build your topic map.</p>}</div>
        </section>}
        {section === "Materials" && <section className="grid-two">
          <div className="card"><p className="eyebrow">SOURCE LIBRARY</p><h2>Upload study material</h2><p className="muted">PDF or TXT, up to 20 MB. Your sources are isolated to your account.</p><label>Document type<select id="document-kind"><option value="syllabus">Syllabus</option><option value="notes">Textbook or notes</option><option value="past_paper">Past exam paper</option></select></label><label className="upload-zone">＋<span>{loading ? "Processing…" : "Choose PDF or TXT file"}</span><input type="file" accept=".pdf,.txt" onChange={upload} disabled={loading} /></label></div>
          <div className="card"><p className="eyebrow">YOUR SOURCES</p><h2>Uploaded materials</h2>{documents.length ? documents.map((doc) => <div className="document-row" key={doc.id}><span className="file-icon">PDF</span><div><b>{doc.filename}</b><small>{doc.kind.replace("_", " ")}</small></div></div>) : <p className="muted">Your documents will appear here.</p>}</div>
        </section>}
        {section === "Quiz" && <section className="card"><p className="eyebrow">KNOWLEDGE CHECK</p><h2>Diagnostic quiz</h2><p className="muted">Questions are generated from retrieved material, include source citations, and are worth 10 points each.</p>
          {!questions.length ? <><label className="question-count">Number of questions<select value={numQuestions} onChange={(event) => setNumQuestions(Number(event.target.value) as 5 | 10 | 15 | 20)}><option value={5}>5 questions</option><option value={10}>10 questions</option><option value={15}>15 questions</option><option value={20}>20 questions</option></select></label><button className="primary" onClick={generateQuiz} disabled={loading || !topics.length}>{loading ? "Generating…" : `Generate ${numQuestions}-question quiz`}</button></> : <><div className="quiz-total">{questions.length} questions · {questions.length * 10} points possible</div><div className="question-list">{questions.map((q, index) => <article className="question" key={q.id}><p className="eyebrow">QUESTION {index + 1} · {q.topic} · 10 POINTS</p><h3>{q.prompt}</h3>{q.options.map((option) => <label className="option" key={option}><input type="radio" name={`q-${q.id}`} value={option} checked={answers[q.id] === option} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} />{option}</label>)}{q.kind === "short_answer" && <input placeholder="Type your answer" value={answers[q.id] || ""} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} />}{q.citations.map((citation) => <small className="citation" key={citation}>↳ {citation}</small>)}</article>)}</div><button className="primary" onClick={submitQuiz} disabled={loading}>{loading ? "Scoring…" : "Submit answers"}</button></>}</section>}
        {section === "Report" && <section className="card"><p className="eyebrow">YOUR PRIMARY OUTPUT</p><h2>Knowledge gap report</h2>{report ? <><div className="score-banner"><strong>{report.score_points}/{report.max_points} points · {report.score_pct}%</strong><span>{report.correct_count} correct out of {report.total}</span></div><section className="mastery-chart" aria-label="Visual topic mastery chart"><div className="mastery-heading"><div><p className="eyebrow">GAP ILLUSTRATION</p><h3>Topic mastery at a glance</h3></div><div className="mastery-legend"><span><i className="weak-dot" />Needs focus</span><span><i className="medium-dot" />Improving</span><span><i className="strong-dot" />Strong</span></div></div><div className="mastery-rows">{report.topics.map((gap) => { const score = Math.max(0, Math.min(100, gap.score_pct)); return <div className={`mastery-row ${gap.level}`} key={gap.topic}><div className="mastery-label"><span>{gap.topic}</span><b>{Math.round(score)}%</b></div><div className="mastery-track" role="meter" aria-label={`${gap.topic} mastery`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(score)}><span className="mastery-fill" style={{ width: `${score}%` }} /></div></div>; })}</div><div className="mastery-scale"><span>0%</span><span>50%</span><span>100%</span></div></section>{report.topics.map((gap) => <article className={`gap ${gap.level}`} key={gap.topic}><div className="gap-title"><span>{gap.level === "weak" ? "🔴" : gap.level === "medium" ? "🟡" : "🟢"} {gap.topic}</span><b>{Math.round(gap.score_pct)}/100</b></div><p>{gap.evidence}</p></article>)}<h2 className="review-heading">Answer review</h2>{report.answers.map((answer, index) => <article className="question" key={`${answer.question}-${index}`}><h3>{answer.correct ? "✓" : "✕"} {answer.question}</h3><p className={answer.correct ? "points-correct" : "points-missed"}>{answer.points_earned}/{answer.points_possible} points</p><p>Your answer: {answer.submitted_answer || "No answer"}</p><p>Expected: {answer.correct_answer}</p><p>{answer.explanation}</p>{answer.citations.map((citation) => <small className="citation" key={citation}>↳ {citation}</small>)}</article>)}</> : <p className="muted">Complete a diagnostic quiz to see topic mastery and evidence.</p>}</section>}
        {section === "Study plan" && <section className="card"><p className="eyebrow">ADAPTIVE REVISION</p><h2>Your study plan</h2><form className="plan-form" onSubmit={createPlan}><label>Days<input name="days" type="number" min="1" max="60" defaultValue="5" required /></label><label>Hours per day<input name="hours" type="number" min="0.5" max="12" step="0.5" defaultValue="2" required /></label><button className="primary" disabled={loading}>Generate plan</button></form>{plan.map((item) => <article className="plan-item" key={item.topic}><div><b>{item.topic}</b><small>{item.level} area · suggested {item.days} days</small><p>{item.suggestion}</p></div><strong>{item.hours}h</strong></article>)}{schedule.length > 0 && <><h2 className="review-heading">Daily timetable</h2>{[...new Set(schedule.map((item) => item.day))].map((day) => <div className="day-row" key={day}><b>Day {day}</b><span>{schedule.filter((session) => session.day === day).map((session) => `${session.topic} (${session.hours}h)`).join(" · ")}</span></div>)}</>}</section>}
        {section === "Study assistant" && <section className="card chat-card"><div className="chat-heading"><div><p className="eyebrow">GROUNDED IN YOUR NOTES</p><h2>Study assistant</h2><p className="muted">Ask follow-up questions. Answers use your uploaded material and include citations.</p></div><button type="button" className="secondary" onClick={() => setChatMessages([])} disabled={!chatMessages.length || loading}>New conversation</button></div><div className="chat-history" aria-live="polite">{!chatMessages.length && <p className="chat-empty">Your conversation will appear here. Ask a question to get started.</p>}{chatMessages.map((message, index) => <article className={`chat-message ${message.role}`} key={`${index}-${message.role}`}><span className="chat-role">{message.role === "user" ? "You" : "Study assistant"}</span><p>{message.content}</p></article>)}{loading && <div className="chat-message assistant"><span className="chat-role">Study assistant</span><p>Looking through your study materials…</p></div>}</div><form className="chat-form" onSubmit={askAssistant}><textarea value={chatText} onChange={(e) => setChatText(e.target.value)} placeholder="Ask a question or follow up…" required /><button className="primary" disabled={loading || !chatText.trim()}>{loading ? "Thinking…" : "Send"}</button></form></section>}
      </main>
    </div>
  );
}
