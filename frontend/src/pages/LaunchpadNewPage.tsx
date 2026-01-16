import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ArrowLeft, Check, Sparkles } from 'lucide-react';
import { setHomePreference } from '../lib/userPrefs';
import type { LaunchCategory } from '../types/launchpad';

type WizardStep = 1 | 2 | 3;

/**
 * LaunchpadNewPage Component
 * 
 * 3-step wizard for creating a new timeline launch.
 * Saves draft to localStorage and redirects to /launchpad on completion.
 */
export function LaunchpadNewPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<WizardStep>(1);
  const [category, setCategory] = useState<LaunchCategory | null>(null);
  const [title, setTitle] = useState('');
  const [tags, setTags] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleNext = () => {
    if (step === 1 && category) {
      setStep(2);
    } else if (step === 2 && title.trim()) {
      setStep(3);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep((s) => (s - 1) as WizardStep);
    }
  };

  const handleSubmit = async () => {
    if (!category || !title.trim()) return;

    setIsSubmitting(true);

    try {
      // Parse tags
      const tagArray = tags
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      // Create draft launch card
      const draft: {
        id: string;
        title: string;
        phase: 'draft';
        category: LaunchCategory;
        createdAt: string;
        updatedAt: string;
        qualityScore: number;
        forkTargetRange: [number, number];
        tags: string[];
      } = {
        id: `launch_draft_${Date.now()}`,
        title: title.trim(),
        phase: 'draft',
        category,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        qualityScore: 0, // New drafts start at 0
        forkTargetRange: [4, 8], // Default range
        tags: tagArray,
      };

      // Save to localStorage
      const existingDrafts = JSON.parse(
        localStorage.getItem('launchpad_drafts') || '[]'
      );
      existingDrafts.push(draft);
      localStorage.setItem('launchpad_drafts', JSON.stringify(existingDrafts));

      // Set home preference to launchpad when user completes wizard
      setHomePreference('launchpad');

      // Redirect to launchpad
      navigate('/launchpad');
    } catch (error) {
      console.error('Failed to create draft:', error);
      setIsSubmitting(false);
    }
  };

  const canProceedStep1 = category !== null;
  const canProceedStep2 = title.trim().length > 0;
  const canSubmit = category !== null && title.trim().length > 0;

  return (
    <div className="h-full flex flex-col gap-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex-shrink-0">
        <h1 className="text-2xl font-bold text-terminal-text uppercase tracking-wide mb-2">
          Create New Timeline
        </h1>
        <p className="text-sm text-terminal-muted">
          Step {step} of 3: {step === 1 ? 'Choose Category' : step === 2 ? 'Enter Details' : 'Review'}
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2 flex-1">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition ${
                s < step
                  ? 'bg-[#00D4FF] text-black'
                  : s === step
                  ? 'bg-[#00D4FF]/20 border-2 border-[#00D4FF] text-[#00D4FF]'
                  : 'bg-terminal-bg border border-terminal-border text-terminal-muted'
              }`}
            >
              {s < step ? <Check className="w-4 h-4" /> : s}
            </div>
            {s < 3 && (
              <div
                className={`h-0.5 flex-1 transition ${
                  s < step ? 'bg-[#00D4FF]' : 'bg-terminal-border'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {/* Step 1: Choose Category */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-terminal-text uppercase tracking-wide mb-4">
              Choose Category
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => setCategory('theatre')}
                className={`p-6 bg-[#111111] border-2 rounded-lg transition text-left ${
                  category === 'theatre'
                    ? 'border-[#00D4FF] bg-[#00D4FF]/10'
                    : 'border-[#1A1A1A] hover:border-[#333]'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="w-12 h-12 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: `${'#00D4FF'}20` }}
                  >
                    <Sparkles className="w-6 h-6" style={{ color: '#00D4FF' }} />
                  </div>
                  <h3 className="text-lg font-bold text-terminal-text">THEATRE</h3>
                </div>
                <p className="text-sm text-terminal-muted">
                  Interactive simulation with agents, forks, and decision points
                </p>
              </button>

              <button
                onClick={() => setCategory('osint')}
                className={`p-6 bg-[#111111] border-2 rounded-lg transition text-left ${
                  category === 'osint'
                    ? 'border-[#9932CC] bg-[#9932CC]/10'
                    : 'border-[#1A1A1A] hover:border-[#333]'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="w-12 h-12 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: `${'#9932CC'}20` }}
                  >
                    <Sparkles className="w-6 h-6" style={{ color: '#9932CC' }} />
                  </div>
                  <h3 className="text-lg font-bold text-terminal-text">OSINT</h3>
                </div>
                <p className="text-sm text-terminal-muted">
                  Open source intelligence feed with evidence and sentiment tracking
                </p>
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Enter Details */}
        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-terminal-text uppercase tracking-wide mb-4">
              Enter Details
            </h2>

            <div>
              <label className="block text-sm font-semibold text-terminal-text uppercase tracking-wide mb-2">
                Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter timeline title..."
                className="w-full px-4 py-3 bg-terminal-bg border border-terminal-border rounded focus:border-[#00D4FF] focus:outline-none text-terminal-text"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-terminal-text uppercase tracking-wide mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="e.g., geopolitics, shipping, middle-east"
                className="w-full px-4 py-3 bg-terminal-bg border border-terminal-border rounded focus:border-[#00D4FF] focus:outline-none text-terminal-text"
              />
              <p className="text-xs text-terminal-muted mt-2">
                Separate multiple tags with commas
              </p>
            </div>
          </div>
        )}

        {/* Step 3: Review */}
        {step === 3 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-terminal-text uppercase tracking-wide mb-4">
              Review
            </h2>

            <div className="bg-[#111111] border border-[#1A1A1A] rounded-lg p-6 space-y-4">
              <div>
                <span className="text-xs text-terminal-muted uppercase tracking-wide">Category</span>
                <p className="text-lg font-semibold text-terminal-text mt-1">
                  {category?.toUpperCase()}
                </p>
              </div>
              <div>
                <span className="text-xs text-terminal-muted uppercase tracking-wide">Title</span>
                <p className="text-lg font-semibold text-terminal-text mt-1">{title}</p>
              </div>
              {tags.trim() && (
                <div>
                  <span className="text-xs text-terminal-muted uppercase tracking-wide">Tags</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {tags
                      .split(',')
                      .map((t) => t.trim())
                      .filter((t) => t.length > 0)
                      .map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs bg-terminal-bg border border-terminal-border rounded"
                        >
                          {tag}
                        </span>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between gap-4 flex-shrink-0 pt-4 border-t border-terminal-border">
        <button
          onClick={handleBack}
          disabled={step === 1}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded transition ${
            step === 1
              ? 'bg-terminal-bg border border-terminal-border text-terminal-muted cursor-not-allowed'
              : 'bg-terminal-bg border border-terminal-border text-terminal-text hover:border-[#00D4FF] hover:text-[#00D4FF]'
          }`}
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        {step < 3 ? (
          <button
            onClick={handleNext}
            disabled={
              (step === 1 && !canProceedStep1) || (step === 2 && !canProceedStep2)
            }
            className={`flex items-center gap-2 px-6 py-2 text-sm font-semibold rounded transition ${
              (step === 1 && !canProceedStep1) || (step === 2 && !canProceedStep2)
                ? 'bg-terminal-bg border border-terminal-border text-terminal-muted cursor-not-allowed'
                : 'bg-[#00D4FF]/20 border border-[#00D4FF] text-[#00D4FF] hover:bg-[#00D4FF]/30'
            }`}
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || isSubmitting}
            className={`flex items-center gap-2 px-6 py-2 text-sm font-semibold rounded transition ${
              !canSubmit || isSubmitting
                ? 'bg-terminal-bg border border-terminal-border text-terminal-muted cursor-not-allowed'
                : 'bg-[#00D4FF]/20 border border-[#00D4FF] text-[#00D4FF] hover:bg-[#00D4FF]/30'
            }`}
          >
            {isSubmitting ? 'Creating...' : 'CREATE DRAFT'}
            <Check className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
