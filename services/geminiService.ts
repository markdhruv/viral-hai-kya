import type {
    CampaignAnalysisResult,
    CTA,
    MarketingObjective,
    CampaignGoalDetails
} from '../types';

// Slightly longer than the server's own 45s cap, so the server normally wins
// and gets to return its clearer message.
const REQUEST_TIMEOUT_MS = 50000;

export const analyzeCampaignsWithGemini = async (
  campaigns: string[],
  keywords: string[],
  ctas: CTA[],
  objective: MarketingObjective,
  details: CampaignGoalDetails
): Promise<CampaignAnalysisResult[]> => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaigns, keywords, ctas, objective, details }),
      signal: controller.signal,
    });

    if (!response.ok) {
      // The server sends a human-readable `error`; pass it straight through
      // rather than burying it in wrapper text.
      const data = await response.json().catch(() => null);
      throw new Error(
        data?.error || 'The analysis service returned an error (' + response.status + '). Please try again.'
      );
    }

    return (await response.json()) as CampaignAnalysisResult[];

  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error("That took too long. Google's AI may be busy - please try again in a minute.");
    }
    if (error instanceof TypeError) {
      throw new Error('Could not reach the analysis service. Check your connection and try again.');
    }
    throw error instanceof Error ? error : new Error(String(error));

  } finally {
    clearTimeout(timer);
  }
};
