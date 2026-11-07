import React, { useState } from 'react';
import { ChevronDownIcon } from './icons';

const objectives: { name: string; rewards: string }[] = [
  { name: 'Create Awareness', rewards: 'Simple, catchy, a strong emotional hook. Memorability over detail.' },
  { name: 'Drive Consideration', rewards: 'Informative, benefit-led, trustworthy. Hype is penalised.' },
  { name: 'Drive Sales', rewards: 'Urgency, scarcity, an unmistakable ask. A passive tone fails.' },
  { name: 'Build Loyalty', rewards: 'Warmth, gratitude, exclusivity. Selling hard is penalised.' },
];

const weights: { name: string; weight: string; what: string }[] = [
  { name: 'Objective fit', weight: '0.25', what: 'Does this serve the goal you picked?' },
  { name: 'Clarity & impact', weight: '0.20', what: 'Active voice, strong verbs, no jargon.' },
  { name: 'Emotion', weight: '0.20', what: 'Raw emotional charge, independent of intent.' },
  { name: 'CTA strength', weight: '0.15', what: 'Is the ask clear, urgent and persuasive?' },
  { name: 'Trend relevance', weight: '0.10', what: 'Does it connect to your keywords?' },
  { name: 'Shareability', weight: '0.10', what: 'Would anyone pass this on?' },
];

export const Methodology: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <section className="mt-6 bg-white dark:bg-slate-800 rounded-xl shadow-lg">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        className="w-full flex justify-between items-center p-6 text-left text-sm font-medium text-slate-700 dark:text-slate-300"
      >
        <span>How this scores your campaign</span>
        <ChevronDownIcon className={`h-5 w-5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="px-6 pb-6 space-y-6 text-sm text-slate-600 dark:text-slate-300">
          <p>
            Most copy checkers grade a message in a vacuum. That is the wrong question. A line
            that is perfect for a loyalty email is a bad line for a conversion ad, so every
            message here is scored against the objective you choose.
          </p>

          <div>
            <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">
              What each objective rewards
            </h3>
            <dl className="space-y-1.5">
              {objectives.map((o) => (
                <div key={o.name} className="sm:flex sm:gap-3">
                  <dt className="font-medium text-slate-700 dark:text-slate-200 sm:w-44 sm:shrink-0">
                    {o.name}
                  </dt>
                  <dd className="text-slate-600 dark:text-slate-400">{o.rewards}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div>
            <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">
              The six scores, and what each is worth
            </h3>
            <dl className="space-y-1.5">
              {weights.map((w) => (
                <div key={w.name} className="flex gap-3">
                  <dt className="font-mono text-xs text-indigo-600 dark:text-indigo-400 pt-0.5 w-10 shrink-0">
                    {w.weight}
                  </dt>
                  <dd>
                    <span className="font-medium text-slate-700 dark:text-slate-200">{w.name}</span>
                    <span className="text-slate-500 dark:text-slate-400"> — {w.what}</span>
                  </dd>
                </div>
              ))}
            </dl>
            <p className="mt-3">
              The weights are uneven on purpose. Objective fit counts for most because a
              well-written message aimed at the wrong goal still fails. Shareability counts for
              least because it is the most situational — a B2B renewal email is not supposed
              to go viral.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">
              What this is not
            </h3>
            <p>
              This is a structured second opinion, not a prediction. The scores come from a
              language model reasoning about copy, not from campaign performance data, so
              nothing here is validated against real outcomes.
            </p>
            <p className="mt-2">
              What it is good for: catching a vague CTA, spotting a tone that fights the
              objective, and forcing a decision about what a campaign is actually for before it
              ships. Treat a low score as a reason to look harder, not as a verdict.
            </p>
          </div>
        </div>
      )}
    </section>
  );
};
