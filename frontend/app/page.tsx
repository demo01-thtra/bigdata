import Link from 'next/link';
import {
  Zap,
  Database,
  BarChart3,
  Brain,
  AlertTriangle,
  ArrowRight,
  Server,
  Monitor,
  GitBranch,
  Check,
} from 'lucide-react';

/* ── Data ── */

const COLORS = {
  red: '#D02020',
  blue: '#1040C0',
  yellow: '#F0C020',
  black: '#121212',
  canvas: '#F0F0F0',
  muted: '#E0E0E0',
} as const;

const shapeColors = [COLORS.red, COLORS.blue, COLORS.yellow];

const techStack = [
  { name: 'Apache Kafka', desc: 'Message streaming (KRaft mode)', icon: Server },
  { name: 'PySpark', desc: 'Structured Streaming + ML inference', icon: Zap },
  { name: 'FastAPI', desc: 'REST API + SSE real-time', icon: GitBranch },
  { name: 'PostgreSQL', desc: 'Transactional database', icon: Database },
  { name: 'Next.js 14', desc: 'React App Router dashboard', icon: Monitor },
  { name: 'scikit-learn', desc: 'RandomForest model (F1 0.99)', icon: Brain },
];

const features = [
  {
    icon: Brain,
    title: 'Machine Learning',
    desc: 'RandomForest đạt F1 = 0.9966, kết hợp SMOTE xử lý mất cân bằng dữ liệu trên 6.3 triệu giao dịch.',
    accent: COLORS.blue,
    shape: 'circle' as const,
  },
  {
    icon: AlertTriangle,
    title: 'Rule-Based Detection',
    desc: '8 luật phát hiện chuyên sâu: blacklist, high-amount, balance-error, rapid transactions, suspicious IP, …',
    accent: COLORS.red,
    shape: 'square' as const,
  },
  {
    icon: Zap,
    title: 'Real-Time Streaming',
    desc: 'PySpark Structured Streaming xử lý hàng nghìn giao dịch/giây qua Apache Kafka micro-batch.',
    accent: COLORS.yellow,
    shape: 'triangle' as const,
  },
  {
    icon: BarChart3,
    title: 'Dashboard trực quan',
    desc: 'Biểu đồ timeline, fraud-by-type, bảng giao dịch phân trang và cảnh báo SSE real-time.',
    accent: COLORS.blue,
    shape: 'circle' as const,
  },
];

const stats = [
  { value: '6.3M+', label: 'Giao dịch PaySim', shape: 'circle' },
  { value: '99.99%', label: 'Accuracy', shape: 'square' },
  { value: '0.9966', label: 'F1-Score', shape: 'rotate-square' },
  { value: '<2s', label: 'Latency', shape: 'triangle' },
];

const pipeline = [
  { label: 'PaySim CSV', sub: 'Producer', bg: COLORS.red },
  { label: 'Kafka', sub: 'Topics', bg: COLORS.yellow },
  { label: 'PySpark', sub: 'ML + Rules', bg: COLORS.blue },
  { label: 'Kafka', sub: 'Output', bg: COLORS.yellow },
  { label: 'FastAPI', sub: 'REST + SSE', bg: COLORS.red },
  { label: 'PostgreSQL', sub: 'Database', bg: COLORS.blue },
  { label: 'Next.js', sub: 'Dashboard', bg: COLORS.red },
];

const teamMembers = [
  { name: 'Nguyễn Đăng Khoa', mssv: '1150080099', color: COLORS.red },
  { name: 'Châu Thị Ngọc Quyên', mssv: '1150080113', color: COLORS.blue },
  { name: 'Hoàng Thanh Trà', mssv: '1150080120', color: COLORS.yellow },
  { name: 'Trần Thị Ngọc Huyền', mssv: '1150080138', color: COLORS.red },
];

/* ── Tiny shape helper ── */
function CornerShape({ color, type }: { color: string; type: 'circle' | 'square' | 'triangle' }) {
  const base = 'absolute top-3 right-3 w-3 h-3';
  if (type === 'circle') return <div className={`${base} rounded-full`} style={{ backgroundColor: color }} />;
  if (type === 'square') return <div className={`${base} rounded-none`} style={{ backgroundColor: color }} />;
  return <div className={`${base}`} style={{ backgroundColor: color, clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)' }} />;
}

/* ── Page ── */
export default function Home() {
  return (
    <div className="-mx-4 sm:-mx-6 lg:-mx-8 -mt-8 font-outfit" style={{ backgroundColor: COLORS.canvas, color: COLORS.black }}>

      {/* ═══════════════════════════ HERO ═══════════════════════════ */}
      <section className="border-b-4 border-[#121212]">
        <div className="mx-auto grid max-w-7xl lg:grid-cols-2">
          {/* Left — text */}
          <div className="flex flex-col justify-center px-6 py-16 sm:px-10 sm:py-24 lg:py-32 lg:pr-12">
            <p className="mb-4 text-sm font-bold uppercase tracking-widest" style={{ color: COLORS.red }}>
              Big Data Fraud Detection
            </p>

            <h1 className="text-4xl font-black uppercase leading-[0.9] tracking-tighter sm:text-6xl lg:text-7xl xl:text-8xl">
              Real-Time
              <br />
              <span style={{ color: COLORS.blue }}>Fraud</span>{' '}
              <span style={{ color: COLORS.red }}>Detection</span>
            </h1>

            <p className="mt-6 max-w-lg text-base font-medium leading-relaxed sm:text-lg" style={{ color: '#444' }}>
              Hệ thống phát hiện gian lận thời gian thực — kết hợp <strong className="text-[#121212]">Machine Learning</strong> và{' '}
              <strong className="text-[#121212]">Rule-Based Detection</strong> trên nền tảng Big Data,
              xử lý hàng triệu giao dịch với độ chính xác 99.99%.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                href="/dashboard"
                className="bauhaus-btn-press inline-flex items-center gap-2 rounded-none border-2 border-[#121212] bg-[#D02020] px-8 py-3.5 text-sm font-bold uppercase tracking-wider text-white shadow-[4px_4px_0px_0px_#121212] hover:bg-[#D02020]/90 md:border-4 md:shadow-[6px_6px_0px_0px_#121212]"
              >
                Vào Dashboard
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/alerts"
                className="bauhaus-btn-press inline-flex items-center gap-2 rounded-none border-2 border-[#121212] bg-white px-8 py-3.5 text-sm font-bold uppercase tracking-wider text-[#121212] shadow-[4px_4px_0px_0px_#121212] hover:bg-gray-100 md:border-4 md:shadow-[6px_6px_0px_0px_#121212]"
              >
                Xem Alerts
              </Link>
            </div>
          </div>

          {/* Right — geometric composition */}
          <div
            className="relative hidden overflow-hidden border-l-4 border-[#121212] lg:flex items-center justify-center"
            style={{ backgroundColor: COLORS.blue }}
          >
            {/* Dot grid overlay */}
            <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(#fff 2px, transparent 2px)', backgroundSize: '20px 20px' }} />

            {/* Large circle */}
            <div className="absolute h-72 w-72 rounded-full border-4 border-white/30" style={{ top: '15%', left: '10%' }} />
            <div className="absolute h-56 w-56 rounded-full" style={{ top: '20%', left: '15%', backgroundColor: COLORS.red, opacity: 0.85 }} />

            {/* Rotated square */}
            <div className="absolute h-40 w-40 rotate-45 border-4 border-white/40" style={{ bottom: '20%', right: '15%' }} />
            <div className="absolute h-32 w-32 rotate-45" style={{ bottom: '23%', right: '18%', backgroundColor: COLORS.yellow, opacity: 0.9 }} />

            {/* Center triangle */}
            <div
              className="absolute h-24 w-24"
              style={{
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                backgroundColor: 'white',
                clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)',
              }}
            />

            {/* Small accent shapes */}
            <div className="absolute h-8 w-8 rounded-full bg-[#F0C020]" style={{ top: '12%', right: '20%' }} />
            <div className="absolute h-6 w-6 bg-white" style={{ bottom: '15%', left: '25%' }} />
          </div>
        </div>
      </section>

      {/* ═══════════════════════════ STATS ═══════════════════════════ */}
      <section className="border-b-4 border-[#121212]" style={{ backgroundColor: COLORS.yellow }}>
        <div className="mx-auto grid max-w-7xl grid-cols-2 divide-x-2 divide-[#121212] sm:divide-x-4 lg:grid-cols-4">
          {stats.map((s, i) => (
            <div key={s.label} className="relative px-4 py-8 text-center sm:px-6 sm:py-10">
              {/* Geometric stat badge */}
              <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center">
                {s.shape === 'circle' && (
                  <div className="flex h-14 w-14 items-center justify-center rounded-full border-2 border-[#121212] bg-white shadow-[3px_3px_0px_0px_#121212] md:border-4 md:shadow-[4px_4px_0px_0px_#121212]">
                    <span className="text-xs font-bold">{i + 1}</span>
                  </div>
                )}
                {s.shape === 'square' && (
                  <div className="flex h-14 w-14 items-center justify-center rounded-none border-2 border-[#121212] bg-white shadow-[3px_3px_0px_0px_#121212] md:border-4 md:shadow-[4px_4px_0px_0px_#121212]">
                    <span className="text-xs font-bold">{i + 1}</span>
                  </div>
                )}
                {s.shape === 'rotate-square' && (
                  <div className="flex h-12 w-12 rotate-45 items-center justify-center rounded-none border-2 border-[#121212] bg-white shadow-[3px_3px_0px_0px_#121212] md:border-4 md:shadow-[4px_4px_0px_0px_#121212]">
                    <span className="-rotate-45 text-xs font-bold">{i + 1}</span>
                  </div>
                )}
                {s.shape === 'triangle' && (
                  <div className="relative h-14 w-14">
                    <div className="absolute inset-0" style={{ backgroundColor: COLORS.black, clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)' }} />
                    <div className="absolute inset-[4px]" style={{ backgroundColor: 'white', clipPath: 'polygon(50% 8%, 4% 100%, 96% 100%)' }} />
                    <span className="absolute inset-0 flex items-center justify-center pt-3 text-xs font-bold">{i + 1}</span>
                  </div>
                )}
              </div>
              <p className="text-2xl font-black uppercase tracking-tighter sm:text-3xl">{s.value}</p>
              <p className="mt-1 text-xs font-bold uppercase tracking-widest">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════ ARCHITECTURE ═══════════════════════════ */}
      <section className="border-b-4 border-[#121212] py-12 px-4 sm:py-16 sm:px-6 lg:py-24 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <h2 className="text-center text-3xl font-black uppercase tracking-tighter sm:text-4xl lg:text-5xl">
            Kiến trúc hệ thống
          </h2>
          <p className="mx-auto mt-3 max-w-lg text-center text-sm font-medium uppercase tracking-wider" style={{ color: '#666' }}>
            Pipeline end-to-end: từ dữ liệu thô đến dashboard real-time
          </p>

          {/* Pipeline blocks */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-3 sm:gap-4">
            {pipeline.map((step, i) => (
              <div key={`${step.label}-${step.sub}`} className="flex items-center gap-3 sm:gap-4">
                <div
                  className="bauhaus-btn-press rounded-none border-2 border-[#121212] px-4 py-3 text-center shadow-[3px_3px_0px_0px_#121212] transition-transform duration-200 hover:-translate-y-1 sm:px-6 sm:py-4 md:border-4 md:shadow-[6px_6px_0px_0px_#121212]"
                  style={{ backgroundColor: step.bg, color: step.bg === COLORS.yellow ? COLORS.black : 'white' }}
                >
                  <p className="text-sm font-bold uppercase tracking-wider sm:text-base">{step.label}</p>
                  <p className="text-[10px] font-medium uppercase tracking-widest opacity-80 sm:text-xs">{step.sub}</p>
                </div>
                {i < pipeline.length - 1 && (
                  <ArrowRight className="h-5 w-5 shrink-0 sm:h-6 sm:w-6" style={{ color: COLORS.black }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════ FEATURES ═══════════════════════════ */}
      <section className="border-b-4 border-[#121212] py-12 px-4 sm:py-16 sm:px-6 lg:py-24 lg:px-8" style={{ backgroundColor: 'white' }}>
        <div className="mx-auto max-w-7xl">
          <h2 className="text-center text-3xl font-black uppercase tracking-tighter sm:text-4xl lg:text-5xl">
            Tính năng nổi bật
          </h2>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:gap-8">
            {features.map((f) => (
              <div
                key={f.title}
                className="group relative rounded-none border-2 border-[#121212] bg-white p-6 shadow-[4px_4px_0px_0px_#121212] transition-transform duration-200 hover:-translate-y-1 sm:p-8 md:border-4 md:shadow-[8px_8px_0px_0px_#121212]"
              >
                {/* Corner decoration */}
                <CornerShape color={f.accent} type={f.shape} />

                {/* Icon container */}
                <div
                  className="mb-5 flex h-14 w-14 items-center justify-center rounded-none border-2 border-[#121212] shadow-[3px_3px_0px_0px_#121212] md:border-4"
                  style={{ backgroundColor: f.accent }}
                >
                  <f.icon className="h-7 w-7 text-white" strokeWidth={2.5} />
                </div>

                <h3 className="text-xl font-bold uppercase tracking-tight">{f.title}</h3>
                <p className="mt-3 text-sm font-medium leading-relaxed" style={{ color: '#444' }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════ TECH STACK ═══════════════════════════ */}
      <section className="border-b-4 border-[#121212] py-12 px-4 sm:py-16 sm:px-6 lg:py-24 lg:px-8" style={{ backgroundColor: COLORS.blue }}>
        <div className="mx-auto max-w-7xl">
          <h2 className="text-center text-3xl font-black uppercase tracking-tighter text-white sm:text-4xl lg:text-5xl">
            Tech Stack
          </h2>

          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 lg:gap-6">
            {techStack.map((t, i) => (
              <div
                key={t.name}
                className="group flex items-center gap-4 rounded-none border-2 border-[#121212] bg-white p-4 shadow-[4px_4px_0px_0px_#121212] transition-transform duration-200 hover:-translate-y-1 sm:p-5 md:border-4 md:shadow-[6px_6px_0px_0px_#121212]"
              >
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-none border-2 border-[#121212] md:border-4"
                  style={{ backgroundColor: shapeColors[i % 3] }}
                >
                  <t.icon className="h-6 w-6" style={{ color: shapeColors[i % 3] === COLORS.yellow ? COLORS.black : 'white' }} strokeWidth={2.5} />
                </div>
                <div>
                  <p className="font-bold uppercase tracking-wide">{t.name}</p>
                  <p className="text-xs font-medium" style={{ color: '#666' }}>{t.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════ TEAM ═══════════════════════════ */}
      <section className="border-b-4 border-[#121212] py-12 px-4 sm:py-16 sm:px-6 lg:py-24 lg:px-8" style={{ backgroundColor: COLORS.red }}>
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-3xl font-black uppercase tracking-tighter text-white sm:text-4xl lg:text-5xl">
            Nhóm thực hiện
          </h2>
          <p className="mt-3 text-sm font-bold uppercase tracking-widest text-white/80">
            Đồ án Big Data — Hệ thống phát hiện gian lận thời gian thực
          </p>

          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {teamMembers.map((m) => (
              <div
                key={m.name}
                className="relative rounded-none border-2 border-[#121212] bg-white p-6 shadow-[4px_4px_0px_0px_#121212] transition-transform duration-200 hover:-translate-y-1 sm:p-8 md:border-4 md:shadow-[6px_6px_0px_0px_#121212]"
              >
                {/* Avatar shape */}
                <div
                  className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border-2 border-[#121212] text-2xl font-black text-white md:border-4"
                  style={{ backgroundColor: m.color }}
                >
                  {m.name.charAt(0)}
                </div>
                <p className="text-base font-bold uppercase tracking-tight">{m.name}</p>
                <p className="mt-1 text-xs font-medium uppercase tracking-wider" style={{ color: '#666' }}>{m.mssv}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════ FINAL CTA ═══════════════════════════ */}
      <section className="relative overflow-hidden border-b-4 border-[#121212] py-16 px-6 text-center sm:py-24" style={{ backgroundColor: COLORS.yellow }}>
        {/* Decorative shapes */}
        <div className="pointer-events-none absolute -left-16 -top-16 h-48 w-48 rounded-full opacity-30" style={{ backgroundColor: COLORS.red }} />
        <div className="pointer-events-none absolute -bottom-10 -right-10 h-36 w-36 rotate-45 opacity-30" style={{ backgroundColor: COLORS.blue }} />

        <h2 className="relative text-3xl font-black uppercase tracking-tighter sm:text-4xl lg:text-5xl">
          Sẵn sàng khám phá?
        </h2>
        <p className="relative mt-3 text-sm font-bold uppercase tracking-widest" style={{ color: '#444' }}>
          Truy cập dashboard để xem hệ thống hoạt động real-time
        </p>
        <Link
          href="/dashboard"
          className="bauhaus-btn-press relative mt-8 inline-flex items-center gap-2 rounded-none border-2 border-[#121212] bg-[#121212] px-10 py-4 text-sm font-bold uppercase tracking-wider text-white shadow-[4px_4px_0px_0px_#D02020] hover:bg-[#121212]/90 md:border-4 md:shadow-[6px_6px_0px_0px_#D02020]"
        >
          Mở Dashboard
          <ArrowRight className="h-4 w-4" />
        </Link>
      </section>

      {/* ═══════════════════════════ FOOTER ═══════════════════════════ */}
      <section className="px-6 py-10 text-center" style={{ backgroundColor: COLORS.black }}>
        <div className="flex items-center justify-center gap-2">
          <div className="h-4 w-4 rounded-full" style={{ backgroundColor: COLORS.red }} />
          <div className="h-4 w-4 rounded-none" style={{ backgroundColor: COLORS.blue }} />
          <div className="h-4 w-4" style={{ backgroundColor: COLORS.yellow, clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)' }} />
        </div>
        <p className="mt-3 text-xs font-bold uppercase tracking-widest text-white/60">
          Fraud Detection System &copy; 2025 — Đồ án Big Data
        </p>
      </section>
    </div>
  );
}
