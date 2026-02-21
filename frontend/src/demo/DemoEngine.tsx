/**
 * Demo Engine
 * 
 * Single owner of timers for demo mode.
 * Uses setTimeout recursion (no stacking on rerender) and cleans up on unmount.
 * Produces:
 * - Market ticks (YES/NO prices, stability, volume jitter)
 * - Agent activity events
 * - Launch feed updates (Launchpad)
 * - Breach simulation (Breach Console)
 * - Export progress simulation (Export Console)
 */

import React from "react";
import { isDemoModeEnabled } from "./demoMode";
import { demoStore } from "./demoStore";
import type { DemoVerificationRun, DemoCertificate, DemoReplayScore } from "./demoStore";

// Mulberry32 seeded random number generator for reproducible demo behavior
function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n));
}

function randBetween(r: () => number, min: number, max: number) {
  return min + (max - min) * r();
}

function pick<T>(r: () => number, items: T[]): T {
  return items[Math.floor(r() * items.length)];
}

export function DemoEngine({ children }: { children: React.ReactNode }) {
  const enabled = isDemoModeEnabled();
  const timers = React.useRef<{
    market?: number;
    agent?: number;
    launchFeed?: number;
    breach?: number;
    export?: number;
    verification?: number;
  }>({});

  React.useEffect(() => {
    if (!enabled) {
      if (timers.current.market) window.clearTimeout(timers.current.market);
      if (timers.current.agent) window.clearTimeout(timers.current.agent);
      if (timers.current.launchFeed) window.clearTimeout(timers.current.launchFeed);
      if (timers.current.breach) window.clearTimeout(timers.current.breach);
      if (timers.current.export) window.clearTimeout(timers.current.export);
      if (timers.current.verification) window.clearTimeout(timers.current.verification);
      timers.current = {};
      return;
    }

    const r = mulberry32(1337);

    // --- Market Ticks ---
    const tickMarkets = () => {
      const keys = demoStore.listOutcomeKeys();
      const now = Date.now();

      for (const key of keys) {
        const [marketIdStr, outcomeId] = key.split(":");
        const marketId: string | number = marketIdStr;
        const snap = demoStore.readOutcome(marketId, outcomeId as any);
        if (!snap) continue;

        const step = (r() - 0.5) * 0.035;
        const nextPrice = clamp(snap.price + step, 0.02, 0.98);

        const stabStep = (r() - 0.5) * 3.2;
        const nextStability = clamp(snap.stability + stabStep, 0, 100);

        const volJitter = Math.floor((r() - 0.5) * 8000);
        const nextVolume = Math.max(0, snap.volume + volJitter);

        demoStore.updateOutcome(
          marketId,
          outcomeId as any,
          (prev) => ({
            ...prev,
            prevPrice: prev.price,
            price: nextPrice,
            stability: nextStability,
            volume: nextVolume,
            updatedAt: now,
          })
        );
      }
    };

    const scheduleMarket = () => {
      const delay = Math.floor(randBetween(r, 2000, 5000));
      timers.current.market = window.setTimeout(() => {
        tickMarkets();
        scheduleMarket();
      }, delay);
    };

    // --- Agent Events ---
    const agentTemplates = [
      () => `LEVIATHAN deployed to ORB_SALVAGE_F7`,
      () => `VIPER withdrew from VEN_OIL_TANKER`,
      () => `AMBASSADOR shifted strategy to minimise exposure`,
      () => `SENTINEL increased liquidity provisioning`,
      () => `ARCHON rotated allocation into high-stability theatres`,
    ];

    const scheduleAgent = () => {
      timers.current.agent = window.setTimeout(() => {
        const text = pick(r, agentTemplates)();
        demoStore.pushAgentEvent({
          id: `a_${Math.random().toString(16).slice(2)}`,
          ts: Date.now(),
          text,
        });
        scheduleAgent();
      }, 5000);
    };

    // --- Launch Feed ---
    const launchActors = ["whale_0x8f", "megalodon", "anon_7x42", "vault_ops", "relay_node"];
    const timelines = ["ORB_SALVAGE_F7", "VEN_OIL_TANKER", "ARCTIC_CABLE", "L2_SEQUENCER", "QUANT_HAZARD"];

    const scheduleLaunchFeed = () => {
      const delay = Math.floor(randBetween(r, 4000, 7000));
      timers.current.launchFeed = window.setTimeout(() => {
        const actor = pick(r, launchActors);
        const roll = r();

        if (roll < 0.55) {
          demoStore.pushLaunchFeed({
            id: `lf_${Math.random().toString(16).slice(2)}`,
            ts: Date.now(),
            kind: "launch",
            actor,
            message: `launched fork on ${pick(r, timelines)} - yield estimate $${Math.floor(randBetween(r, 120, 520))}/hour`,
            accent: "success",
          });
        } else if (roll < 0.85) {
          demoStore.pushLaunchFeed({
            id: `lf_${Math.random().toString(16).slice(2)}`,
            ts: Date.now(),
            kind: "milestone",
            actor,
            message: `fork reached ${Math.floor(randBetween(r, 50, 220))} trades - liquidity stabilising`,
            accent: "info",
          });
        } else {
          demoStore.pushLaunchFeed({
            id: `lf_${Math.random().toString(16).slice(2)}`,
            ts: Date.now(),
            kind: "warning",
            actor,
            message: `stability dropped to ${Math.floor(randBetween(r, 35, 58))}% on ${pick(r, timelines)}`,
            accent: "danger",
            cta: { label: "Inject Shield", action: "inject_shield" },
          });
        }

        scheduleLaunchFeed();
      }, delay);
    };

    // --- Breach Simulation ---
    const breachTypes: Array<"PARADOX" | "STABILITY" | "ORACLE" | "SENSOR"> = ["PARADOX", "STABILITY", "ORACLE", "SENSOR"];
    const severities: Array<"CRITICAL" | "HIGH" | "MEDIUM"> = ["CRITICAL", "HIGH", "MEDIUM"];
    const carriers = ["VIPER", "SENTINEL", "ARCHON", "AMBASSADOR", "LEVIATHAN"];

    const seedBreaches = () => {
      const existing = demoStore.getBreachesActive();
      if (existing.length > 0) return;

      const active = [
        {
          id: `b_${Math.random().toString(16).slice(2)}`,
          type: "PARADOX" as const,
          timeline: "ORB_SALVAGE_F7",
          severity: "CRITICAL" as const,
          ts: Date.now() - 4 * 60 * 1000,
          logicGap: 68,
          stability: 22,
          carrier: "VIPER",
          sanity: 18,
          status: "ACTIVE" as const,
        },
        {
          id: `b_${Math.random().toString(16).slice(2)}`,
          type: "STABILITY" as const,
          timeline: "VEN_OIL_TANKER",
          severity: "HIGH" as const,
          ts: Date.now() - 11 * 60 * 1000,
          logicGap: 31,
          stability: 44,
          carrier: "SENTINEL",
          sanity: 62,
          status: "ACTIVE" as const,
        },
      ];
      const history = [
        { id: "h1", time: "14:28:45", type: "STABILITY" as const, timeline: "VEN_OIL_TANKER", severity: "HIGH" as const, resolution: "Shield injected", impact: "-8% stability" },
        { id: "h2", time: "14:11:03", type: "ORACLE" as const, timeline: "L2_SEQUENCER", severity: "MEDIUM" as const, resolution: "Oracle failover", impact: "-2% stability" },
      ];
      demoStore.setBreaches(active, history);
    };

    const tickBreaches = () => {
      const active = demoStore.getBreachesActive();

      // Mutate existing breaches
      for (const b of active) {
        const delta = (r() - 0.5) * 8;
        demoStore.updateBreach(b.id, (prev) => ({
          ...prev,
          stability: clamp(prev.stability + delta, 5, 95),
          logicGap: clamp(prev.logicGap + (r() - 0.5) * 6, 5, 95),
          sanity: clamp(prev.sanity + (r() - 0.5) * 4, 5, 95),
        }));
      }

      // Occasionally add new breach
      if (r() < 0.08 && active.length < 4) {
        const newBreach = {
          id: `b_${Math.random().toString(16).slice(2)}`,
          type: pick(r, breachTypes),
          timeline: pick(r, timelines),
          severity: pick(r, severities),
          ts: Date.now(),
          logicGap: Math.floor(randBetween(r, 25, 75)),
          stability: Math.floor(randBetween(r, 20, 60)),
          carrier: pick(r, carriers),
          sanity: Math.floor(randBetween(r, 30, 70)),
          status: "ACTIVE" as const,
        };
        const { active: currActive, history } = { active: demoStore.getBreachesActive(), history: demoStore.getBreachesHistory() };
        demoStore.setBreaches([...currActive, newBreach], history);
      }

      // Occasionally resolve a breach
      if (r() < 0.05 && active.length > 0) {
        const toResolve = active[Math.floor(r() * active.length)];
        demoStore.moveBreachToHistory(toResolve.id, "Auto-resolved", "-3% stability (contained)");
      }
    };

    const scheduleBreach = () => {
      const delay = Math.floor(randBetween(r, 4000, 7000));
      timers.current.breach = window.setTimeout(() => {
        seedBreaches();
        tickBreaches();
        scheduleBreach();
      }, delay);
    };

    // --- Export Simulation ---
    const partners = ["Boston Dynamics", "Agility Robotics", "Covariant.ai", "Figure AI", "1X Technologies"];
    const theatres = ["orbital_salvage_v1", "warehouse_pick_v3", "dock_sort_v2", "assembly_line_v1"];
    const formats: Array<"PyTorch (.pt)" | "ROS Bag (.bag)" | "TFRecord (.tfrecord)" | "JSON (Canonical)"> = ["PyTorch (.pt)", "ROS Bag (.bag)", "TFRecord (.tfrecord)", "JSON (Canonical)"];

    const seedExports = () => {
      const active = demoStore.getExportsActive();
      if (active.length > 0) return;

      const newActive = [
        {
          id: `e_${Math.random().toString(16).slice(2)}`,
          partner: "Boston Dynamics",
          status: "PROCESSING" as const,
          theatre: "orbital_salvage_v1",
          episodes: 1247,
          samplingRate: 0.5,
          format: "PyTorch (.pt)" as const,
          sizeGb: 2.4,
          progress: 68,
          etaSec: 192,
        },
        {
          id: `e_${Math.random().toString(16).slice(2)}`,
          partner: "Agility Robotics",
          status: "QUEUED" as const,
          theatre: "warehouse_pick_v3",
          episodes: 802,
          samplingRate: 0.4,
          format: "ROS Bag (.bag)" as const,
          sizeGb: 1.1,
          progress: 0,
          etaSec: 0,
        },
        {
          id: `e_${Math.random().toString(16).slice(2)}`,
          partner: "Covariant.ai",
          status: "PROCESSING" as const,
          theatre: "dock_sort_v2",
          episodes: 2150,
          samplingRate: 0.6,
          format: "TFRecord (.tfrecord)" as const,
          sizeGb: 3.7,
          progress: 41,
          etaSec: 420,
        },
      ];
      demoStore.setExports(newActive);
    };

    const tickExports = () => {
      const active = demoStore.getExportsActive();

      for (const x of active) {
        if (x.status === "PROCESSING") {
          const progressIncrement = Math.floor(randBetween(r, 2, 8));
          const newProgress = Math.min(100, x.progress + progressIncrement);
          const etaReduction = Math.floor(randBetween(r, 15, 45));

          // Update export in place
          const updated = active.map((e) =>
            e.id === x.id
              ? { ...e, progress: newProgress, etaSec: Math.max(0, e.etaSec - etaReduction) }
              : e
          );
          demoStore.setExports(updated);

          // If completed, replace with new queued job
          if (newProgress >= 100) {
            const newJob = {
              id: `e_${Math.random().toString(16).slice(2)}`,
              partner: pick(r, partners),
              status: "QUEUED" as const,
              theatre: pick(r, theatres),
              episodes: Math.floor(randBetween(r, 500, 2500)),
              samplingRate: Math.round(randBetween(r, 0.3, 0.7) * 10) / 10,
              format: pick(r, formats),
              sizeGb: parseFloat(randBetween(r, 0.5, 4.5).toFixed(1)),
              progress: 0,
              etaSec: 0,
            };
            const completed = active.map((e) => (e.id === x.id ? { ...e, status: "COMPLETED" as const } : e));
            demoStore.setExports([...completed, newJob]);
          }
        }
      }

      // Occasionally add new queued export
      if (r() < 0.1 && active.filter((x) => x.status === "QUEUED").length < 2) {
        const newJob = {
          id: `e_${Math.random().toString(16).slice(2)}`,
          partner: pick(r, partners),
          status: "QUEUED" as const,
          theatre: pick(r, theatres),
          episodes: Math.floor(randBetween(r, 500, 2500)),
          samplingRate: Math.round(randBetween(r, 0.3, 0.7) * 10) / 10,
          format: pick(r, formats),
          sizeGb: parseFloat(randBetween(r, 0.5, 4.5).toFixed(1)),
          progress: 0,
          etaSec: 0,
        };
        demoStore.setExports([...active, newJob]);
      }
    };

    const scheduleExport = () => {
      const delay = Math.floor(randBetween(r, 1500, 3000));
      timers.current.export = window.setTimeout(() => {
        seedExports();
        tickExports();
        scheduleExport();
      }, delay);
    };

    // --- Verification Simulation ---

    function makeReplayScores(rng: () => number, count: number, baseTs: string): DemoReplayScore[] {
      const scores: DemoReplayScore[] = [];
      for (let i = 0; i < count; i++) {
        scores.push({
          id: `rs_${Math.random().toString(16).slice(2)}`,
          ground_truth_id: `gt_${Math.random().toString(16).slice(2)}`,
          precision: parseFloat(randBetween(rng, 0.65, 0.98).toFixed(3)),
          recall: parseFloat(randBetween(rng, 0.60, 0.95).toFixed(3)),
          reply_accuracy: parseFloat(randBetween(rng, 0.70, 0.99).toFixed(3)),
          claims_total: Math.floor(randBetween(rng, 15, 40)),
          claims_supported: Math.floor(randBetween(rng, 10, 35)),
          changes_total: Math.floor(randBetween(rng, 5, 20)),
          changes_surfaced: Math.floor(randBetween(rng, 3, 18)),
          scoring_model: "gpt-4o-2025-03-26",
          scoring_latency_ms: Math.floor(randBetween(rng, 120, 850)),
          scored_at: baseTs,
        });
      }
      return scores;
    }

    function makeCertificate(rng: () => number, id: string, constructId: string, replayCount: number, createdAt: string): DemoCertificate {
      const replays = makeReplayScores(rng, replayCount, createdAt);
      const avgPrecision = replays.reduce((s, rs) => s + rs.precision, 0) / replays.length;
      const avgRecall = replays.reduce((s, rs) => s + rs.recall, 0) / replays.length;
      const avgAccuracy = replays.reduce((s, rs) => s + rs.reply_accuracy, 0) / replays.length;
      return {
        id,
        construct_id: constructId,
        domain: "prediction-markets",
        replay_count: replayCount,
        precision: parseFloat(avgPrecision.toFixed(3)),
        recall: parseFloat(avgRecall.toFixed(3)),
        reply_accuracy: parseFloat(avgAccuracy.toFixed(3)),
        composite_score: parseFloat(((avgPrecision + avgRecall + avgAccuracy) / 3).toFixed(3)),
        brier: parseFloat(randBetween(rng, 0.08, 0.28).toFixed(3)),
        sample_size: Math.floor(randBetween(rng, 200, 800)),
        ground_truth_source: "polymarket-resolved",
        methodology_version: "v2.1.0",
        scoring_model: "gpt-4o-2025-03-26",
        created_at: createdAt,
        replay_scores: replays,
      };
    }

    const seedVerification = () => {
      if (demoStore.getVerificationRuns().length > 0) return;

      const now = Date.now();
      const runs: DemoVerificationRun[] = [
        {
          run_id: "vr_completed_1",
          status: "COMPLETED",
          progress: 90,
          total: 90,
          construct_id: "osint-oracle-v3",
          repo_url: "https://github.com/echelon/osint-oracle",
          error: null,
          certificate_id: "cert_1",
          created_at: new Date(now - 24 * 3600_000).toISOString(),
          updated_at: new Date(now - 23 * 3600_000).toISOString(),
        },
        {
          run_id: "vr_completed_2",
          status: "COMPLETED",
          progress: 75,
          total: 75,
          construct_id: "sentiment-probe-v2",
          repo_url: "https://github.com/echelon/sentiment-probe",
          error: null,
          certificate_id: "cert_2",
          created_at: new Date(now - 48 * 3600_000).toISOString(),
          updated_at: new Date(now - 47 * 3600_000).toISOString(),
        },
        {
          run_id: "vr_scoring_1",
          status: "SCORING",
          progress: 47,
          total: 90,
          construct_id: "geo-resolver-v1",
          repo_url: "https://github.com/echelon/geo-resolver",
          error: null,
          certificate_id: null,
          created_at: new Date(now - 2 * 3600_000).toISOString(),
          updated_at: new Date(now - 5 * 60_000).toISOString(),
        },
        {
          run_id: "vr_failed_1",
          status: "FAILED",
          progress: 12,
          total: 80,
          construct_id: "osint-oracle-v2",
          repo_url: "https://github.com/echelon/osint-oracle",
          error: "Oracle timeout after 30s — HTTP oracle did not respond",
          certificate_id: null,
          created_at: new Date(now - 72 * 3600_000).toISOString(),
          updated_at: new Date(now - 71 * 3600_000).toISOString(),
        },
        {
          run_id: "vr_pending_1",
          status: "PENDING",
          progress: 0,
          total: 0,
          construct_id: "trade-classifier-v4",
          repo_url: "https://github.com/echelon/trade-classifier",
          error: null,
          certificate_id: null,
          created_at: new Date(now - 30_000).toISOString(),
          updated_at: new Date(now - 30_000).toISOString(),
        },
      ];

      for (const run of runs) {
        demoStore.addVerificationRun(run);
      }

      // 3 certificates linked to completed runs
      const cert1 = makeCertificate(r, "cert_1", "osint-oracle-v3", 4, new Date(now - 23 * 3600_000).toISOString());
      const cert2 = makeCertificate(r, "cert_2", "sentiment-probe-v2", 3, new Date(now - 47 * 3600_000).toISOString());
      const cert3 = makeCertificate(r, "cert_3", "geo-resolver-v0", 5, new Date(now - 96 * 3600_000).toISOString());

      demoStore.addCertificate(cert1);
      demoStore.addCertificate(cert2);
      demoStore.addCertificate(cert3);
    };

    const tickVerification = () => {
      const runs = demoStore.getVerificationRuns();
      const now = new Date().toISOString();

      for (const run of runs) {
        if (run.status === "PENDING") {
          // PENDING → INGESTING (set total)
          const total = Math.floor(randBetween(r, 60, 120));
          demoStore.updateVerificationRun(run.run_id, (prev) => ({
            ...prev,
            status: "INGESTING",
            total,
            progress: 0,
            updated_at: now,
          }));
        } else if (run.status === "INGESTING") {
          // Increment progress; transition to SCORING at 30%
          const increment = Math.floor(randBetween(r, 3, 8));
          const newProgress = Math.min(run.total, run.progress + increment);
          const threshold = Math.floor(run.total * 0.3);
          demoStore.updateVerificationRun(run.run_id, (prev) => ({
            ...prev,
            progress: newProgress,
            status: newProgress >= threshold ? "SCORING" : "INGESTING",
            updated_at: now,
          }));
        } else if (run.status === "SCORING") {
          // Increment progress; transition to CERTIFYING at 90%
          const increment = Math.floor(randBetween(r, 2, 5));
          const newProgress = Math.min(run.total, run.progress + increment);
          const threshold = Math.floor(run.total * 0.9);
          demoStore.updateVerificationRun(run.run_id, (prev) => ({
            ...prev,
            progress: newProgress,
            status: newProgress >= threshold ? "CERTIFYING" : "SCORING",
            updated_at: now,
          }));
        } else if (run.status === "CERTIFYING") {
          // CERTIFYING → COMPLETED with generated certificate
          const certId = `cert_${Math.random().toString(16).slice(2)}`;
          const cert = makeCertificate(r, certId, run.construct_id, Math.floor(randBetween(r, 3, 5)), now);
          demoStore.addCertificate(cert);
          demoStore.updateVerificationRun(run.run_id, (prev) => ({
            ...prev,
            status: "COMPLETED",
            progress: prev.total,
            certificate_id: certId,
            updated_at: now,
          }));
        }
      }
    };

    const scheduleVerification = () => {
      const delay = Math.floor(randBetween(r, 2000, 3000));
      timers.current.verification = window.setTimeout(() => {
        seedVerification();
        tickVerification();
        scheduleVerification();
      }, delay);
    };

    // Start all schedules
    scheduleMarket();
    scheduleAgent();
    scheduleLaunchFeed();
    scheduleBreach();
    scheduleExport();
    scheduleVerification();

    return () => {
      if (timers.current.market) window.clearTimeout(timers.current.market);
      if (timers.current.agent) window.clearTimeout(timers.current.agent);
      if (timers.current.launchFeed) window.clearTimeout(timers.current.launchFeed);
      if (timers.current.breach) window.clearTimeout(timers.current.breach);
      if (timers.current.export) window.clearTimeout(timers.current.export);
      if (timers.current.verification) window.clearTimeout(timers.current.verification);
      timers.current = {};
    };
  }, [enabled]);

  return <>{children}</>;
}
