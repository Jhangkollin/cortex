'use client'

import { motion } from 'framer-motion'

const PLATFORM_FEATURES = [
  'AI Answer Engine',
  'Brand Knowledge Base',
  'Brand Answer Management',
  'Hosting',
  'JSON-LD Generation',
  'Sitemap Management',
  'Reporting Dashboard',
  'API Access',
]

const REVENUE_MODELS = [
  {
    title: 'Brand Cooperation Reward',
    rate: '20%',
    rateLabel: 'of brand payment',
    description:
      'Earn a reward when you refer, propose, or help a brand onboard any Mlytics AEO plan — including co-purchasing or direct order on behalf of the brand.',
    example: 'Example: Brand purchases PAYG Starter (NT$30,000) → you earn NT$6,000',
    settlement: 'Quarterly settlement · Counted 60 days after brand payment clears',
  },
  {
    title: 'Media Answer Revenue Share',
    rate: 'NT$300',
    rateLabel: '/ Published Media Answer',
    description:
      'Earn per published Media Answer generated within your content environment. Revenue scales directly with your content volume.',
    example: 'Example: 100 Published Media Answers → NT$30,000',
    settlement: 'Monthly usage count · Settled the following month',
  },
]

const PARTNER_BENEFITS = [
  'Participate in brand AEO budget allocation',
  'Earn Brand Cooperation Rewards on referrals',
  'Earn continuous revenue from Media Answers',
  'Access the full Mlytics AEO Platform',
  'Transparent usage & revenue reports',
  'Turn existing content assets into recurring commercial value',
]

const MLYTICS_HANDLES = [
  'Brand plan design & consulting',
  'AEO Platform operation & maintenance',
  'Brand Knowledge Base management',
  'Brand Answer management',
  'Customer success & technical support',
]

const BRAND_ACQUISITION_CHANNELS = [
  'Developed directly by Mlytics',
  'Referred by a media partner',
  'Assisted purchase by a media partner',
]

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-80px' },
  transition: { duration: 0.5, delay, ease: 'easeOut' },
})

const cardFadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-60px' },
  transition: { duration: 0.4, delay, ease: 'easeOut' },
})

export function PartnershipContent() {
  return (
    <>
      {/* Hero */}
      <div
        className="pt-32 pb-16 text-center"
        style={{ background: '#1A3D3A', borderBottom: '1px solid rgba(168,197,195,0.12)' }}
      >
        <div className="max-w-3xl mx-auto px-6">
          <span
            className="inline-block text-xs font-semibold uppercase tracking-widest mb-4 px-3 py-1.5 rounded-full"
            style={{
              background: 'rgba(34,93,89,0.4)',
              color: '#A8C5C3',
              border: '1px solid rgba(34,93,89,0.6)',
            }}
          >
            Mlytics Media Partner Program
          </span>

          <h1 className="text-4xl md:text-5xl font-bold text-white leading-tight mb-4">
            Turn your content into<br />an AI revenue engine.
          </h1>

          <p className="text-base max-w-xl mx-auto" style={{ color: '#A8C5C3' }}>
            The Mlytics AEO Platform lets media partners transform existing content assets into
            Answer assets — and earn from every brand that participates.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href="/book-a-demo"
              className="px-6 py-3 rounded-full text-sm font-semibold text-white transition-all hover:opacity-90"
              style={{ background: '#225D59' }}
            >
              Become a Partner
            </a>
            <a
              href="mailto:partnership@mlytics.com"
              className="px-6 py-3 rounded-full text-sm font-semibold transition-all"
              style={{
                background: 'rgba(34,93,89,0.2)',
                color: '#A8C5C3',
                border: '1px solid rgba(34,93,89,0.6)',
              }}
            >
              Contact Us
            </a>
          </div>
        </div>
      </div>

      {/* How it works */}
      <section style={{ background: '#FAFAFA' }} className="py-20">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div className="text-center mb-12" {...fadeUp()}>
            <h2 className="text-2xl md:text-3xl font-bold mb-4" style={{ color: '#1A1A1A' }}>
              How the partnership works
            </h2>
            <p className="text-sm max-w-xl mx-auto" style={{ color: '#6B6B6B' }}>
              Mlytics handles the platform and brand delivery. You bring your audience and content —
              and share in the revenue.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Mlytics handles */}
            <motion.div
              className="rounded-2xl p-6"
              style={{ background: '#F7FAFA', border: '1px solid rgba(34,93,89,0.1)' }}
              {...cardFadeUp(0.1)}
            >
              <h3 className="text-base font-semibold mb-4" style={{ color: '#225D59' }}>
                Mlytics handles
              </h3>
              <ul className="space-y-2">
                {MLYTICS_HANDLES.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm" style={{ color: '#6B6B6B' }}>
                    <span className="mt-0.5 text-[#225D59]">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* Platform features */}
            <motion.div
              className="rounded-2xl p-6"
              style={{ background: '#F7FAFA', border: '1px solid rgba(34,93,89,0.1)' }}
              {...cardFadeUp(0.2)}
            >
              <h3 className="text-base font-semibold mb-4" style={{ color: '#225D59' }}>
                Partner platform access
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {PLATFORM_FEATURES.map((f) => (
                  <div
                    key={f}
                    className="text-xs font-medium px-3 py-2 rounded-lg"
                    style={{ background: 'rgba(34,93,89,0.08)', color: '#225D59' }}
                  >
                    {f}
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Brand acquisition channels */}
            <motion.div
              className="rounded-2xl p-6"
              style={{ background: '#F7FAFA', border: '1px solid rgba(34,93,89,0.1)' }}
              {...cardFadeUp(0.3)}
            >
              <h3 className="text-base font-semibold mb-4" style={{ color: '#225D59' }}>
                How brands join
              </h3>
              <ul className="space-y-2">
                {BRAND_ACQUISITION_CHANNELS.map((c) => (
                  <li key={c} className="flex items-start gap-2 text-sm" style={{ color: '#6B6B6B' }}>
                    <span className="mt-0.5 text-[#225D59]">✓</span>
                    {c}
                  </li>
                ))}
              </ul>
              <p className="text-xs mt-4" style={{ color: '#9B9B9B' }}>
                All brands are served by Mlytics on the AEO platform regardless of acquisition channel.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Revenue Models */}
      <section
        className="py-20"
        style={{ background: '#1A3D3A', borderTop: '1px solid rgba(168,197,195,0.12)' }}
      >
        <div className="max-w-5xl mx-auto px-6">
          <motion.div className="text-center mb-12" {...fadeUp()}>
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
              Two ways to earn
            </h2>
            <p className="text-sm max-w-lg mx-auto" style={{ color: '#A8C5C3' }}>
              Revenue scales with your content and your brand network — both streams run in parallel.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {REVENUE_MODELS.map((m, i) => (
              <motion.div
                key={m.title}
                className="rounded-2xl p-7"
                style={{ background: 'rgba(34,93,89,0.15)', border: '1px solid rgba(168,197,195,0.15)' }}
                {...cardFadeUp(i * 0.15)}
              >
                <h3 className="text-xl font-bold text-white mb-1">{m.title}</h3>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-3xl font-bold" style={{ color: '#A8C5C3' }}>{m.rate}</span>
                  <span className="text-sm" style={{ color: '#A8C5C3' }}>{m.rateLabel}</span>
                </div>
                <p className="text-sm leading-relaxed mb-4" style={{ color: '#C8DDD9' }}>
                  {m.description}
                </p>
                <div
                  className="text-xs px-3 py-2 rounded-lg mb-3"
                  style={{ background: 'rgba(168,197,195,0.1)', color: '#A8C5C3' }}
                >
                  {m.example}
                </div>
                <p className="text-xs" style={{ color: '#6B9E9A' }}>{m.settlement}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Answer definition */}
      <section style={{ background: '#FAFAFA' }} className="py-16">
        <div className="max-w-3xl mx-auto px-6">
          <motion.h2
            className="text-xl md:text-2xl font-bold mb-6 text-center"
            style={{ color: '#1A1A1A' }}
            {...fadeUp()}
          >
            What counts as a Published Media Answer?
          </motion.h2>

          <div className="grid sm:grid-cols-2 gap-4">
            <motion.div
              className="rounded-xl p-5"
              style={{ background: '#F0F7F6', border: '1px solid rgba(34,93,89,0.1)' }}
              {...cardFadeUp(0.1)}
            >
              <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: '#225D59' }}>
                Counts as 1 answer
              </p>
              <ul className="space-y-1.5 text-sm" style={{ color: '#4A4A4A' }}>
                <li>✓ Media Answer generation completed</li>
                <li>✓ Media Answer officially published</li>
              </ul>
            </motion.div>

            <motion.div
              className="rounded-xl p-5"
              style={{ background: '#FFF8F8', border: '1px solid rgba(180,60,60,0.08)' }}
              {...cardFadeUp(0.2)}
            >
              <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: '#9B4444' }}>
                Not counted twice
              </p>
              <ul className="space-y-1.5 text-sm" style={{ color: '#4A4A4A' }}>
                <li>✗ Re-generation of unpublished content</li>
                <li>✗ Draft-stage edits</li>
                <li>✗ Manual edits to existing content</li>
                <li>✗ Quality-optimisation re-generations</li>
              </ul>
            </motion.div>
          </div>

          <motion.p
            className="text-xs text-center mt-6"
            style={{ color: '#6B6B6B' }}
            {...fadeUp(0.3)}
          >
            Published Media Answers are retained for 6 months from the publication date.
          </motion.p>
        </div>
      </section>

      {/* Partner Benefits */}
      <section
        className="py-20"
        style={{ background: '#1A3D3A', borderTop: '1px solid rgba(168,197,195,0.12)' }}
      >
        <div className="max-w-3xl mx-auto px-6 text-center">
          <motion.h2
            className="text-2xl md:text-3xl font-bold text-white mb-10"
            {...fadeUp()}
          >
            Partner benefits
          </motion.h2>

          <ul className="grid sm:grid-cols-2 gap-4 text-left">
            {PARTNER_BENEFITS.map((b, i) => (
              <motion.li
                key={b}
                className="flex items-start gap-3"
                {...cardFadeUp(i * 0.08)}
              >
                <span className="mt-0.5 text-[#A8C5C3]">✓</span>
                <span className="text-sm font-medium" style={{ color: '#C8DDD9' }}>{b}</span>
              </motion.li>
            ))}
          </ul>
        </div>
      </section>

      {/* CTA */}
      <section style={{ background: '#FAFAFA' }} className="py-20 text-center">
        <div className="max-w-2xl mx-auto px-6">
          <motion.div {...fadeUp()}>
            <h2 className="text-2xl md:text-3xl font-bold mb-4" style={{ color: '#1A1A1A' }}>
              Ready to join the program?
            </h2>
            <p className="text-sm mb-8" style={{ color: '#6B6B6B' }}>
              Tell us about your platform and we&apos;ll map out your revenue potential together.
            </p>
            <a
              href="/book-a-demo"
              className="inline-block px-8 py-3 rounded-full text-sm font-semibold text-white transition-all hover:opacity-90"
              style={{ background: '#225D59' }}
            >
              Get in Touch
            </a>
          </motion.div>
        </div>
      </section>
    </>
  )
}
