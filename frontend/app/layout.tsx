import type { Metadata } from 'next';
import { Inter, Outfit } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });
const outfit = Outfit({
  subsets: ['latin'],
  weight: ['400', '500', '700', '900'],
  variable: '--font-outfit',
});

export const metadata: Metadata = {
  title: 'Fraud Detection Dashboard',
  description: 'Real-time fraud detection and risk management system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} ${outfit.variable} min-h-screen bg-slate-900`}>
        <nav className="sticky top-0 z-50 border-b-4 border-[#121212] bg-[#121212]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <a href="/" className="flex items-center gap-3 group">
                {/* Bauhaus geometric logo — circle, square, triangle */}
                <div className="flex items-center gap-1">
                  <div className="h-5 w-5 rounded-full bg-[#D02020]" />
                  <div className="h-5 w-5 rounded-none bg-[#1040C0]" />
                  <div
                    className="h-5 w-5 bg-[#F0C020]"
                    style={{ clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)' }}
                  />
                </div>
                <span className="text-lg font-bold uppercase tracking-wider text-white">
                  Fraud Detection
                </span>
              </a>
              <div className="flex items-center gap-6">
                <a href="/" className="text-sm font-bold uppercase tracking-wider text-slate-300 hover:text-[#F0C020] transition-colors duration-200">Intro</a>
                <a href="/dashboard" className="text-sm font-bold uppercase tracking-wider text-slate-300 hover:text-[#F0C020] transition-colors duration-200">Dashboard</a>
                <a href="/transactions" className="text-sm font-bold uppercase tracking-wider text-slate-300 hover:text-[#F0C020] transition-colors duration-200">Transactions</a>
                <a href="/alerts" className="text-sm font-bold uppercase tracking-wider text-slate-300 hover:text-[#F0C020] transition-colors duration-200">Alerts</a>
              </div>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
