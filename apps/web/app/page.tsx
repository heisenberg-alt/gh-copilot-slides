import Link from 'next/link';
import { ArrowRight, Sparkles, Zap, Download } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-apple bg-accent flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-lg">Slide Builder</span>
          </div>
          <Link
            href="/signin"
            className="btn btn-primary"
          >
            Get Started
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 text-accent text-sm font-medium mb-8 animate-fade-in">
            <Sparkles className="w-4 h-4" />
            Powered by Azure OpenAI
          </div>

          <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-6 animate-fade-up">
            Create stunning presentations
            <br />
            <span className="text-accent">in minutes, not hours</span>
          </h1>

          <p className="text-xl text-text-secondary max-w-2xl mx-auto mb-10 animate-fade-up" style={{ animationDelay: '100ms' }}>
            Describe your topic, and our AI researches, designs, and generates
            beautiful presentations. Export to PowerPoint, PDF, or interactive HTML.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-up" style={{ animationDelay: '200ms' }}>
            <Link href="/signin" className="btn btn-primary text-lg px-8 py-4">
              Start Creating
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="#features" className="btn btn-secondary text-lg px-8 py-4">
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6 bg-surface">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-4">
            How it works
          </h2>
          <p className="text-text-secondary text-center mb-16 max-w-2xl mx-auto">
            Three simple steps to create professional presentations
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="card card-hover">
              <div className="w-12 h-12 rounded-apple-lg bg-accent/10 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-accent">1</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Describe your topic</h3>
              <p className="text-text-secondary">
                Tell us what your presentation is about. Add URLs or upload existing
                templates for reference.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="card card-hover">
              <div className="w-12 h-12 rounded-apple-lg bg-accent/10 flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-xl font-semibold mb-2">AI does the research</h3>
              <p className="text-text-secondary">
                Our AI agents research your topic, curate content, and design
                visually stunning slides.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="card card-hover">
              <div className="w-12 h-12 rounded-apple-lg bg-accent/10 flex items-center justify-center mb-4">
                <Download className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Export anywhere</h3>
              <p className="text-text-secondary">
                Download as PowerPoint, PDF, or interactive HTML. Perfect for
                any presentation scenario.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to create your first presentation?
          </h2>
          <p className="text-text-secondary mb-8">
            Sign in with your Microsoft account to get started.
          </p>
          <Link href="/signin" className="btn btn-primary text-lg px-8 py-4">
            Sign in with Microsoft
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-border">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-text-secondary">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-accent flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span>Slide Builder v2</span>
          </div>
          <p>Powered by Azure OpenAI and Microsoft Entra ID</p>
        </div>
      </footer>
    </div>
  );
}
