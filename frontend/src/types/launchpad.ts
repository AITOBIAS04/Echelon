/**
 * Launchpad Types
 * 
 * Types for the Launchpad feature, which allows users to discover,
 * create, and manage new timeline launches.
 */

/**
 * Launch phase lifecycle states
 */
export type LaunchPhase = 'draft' | 'sandbox' | 'pilot' | 'graduated' | 'failed';

/**
 * Launch category classification
 */
export type LaunchCategory = 'theatre' | 'osint';

/**
 * Launch card representing a timeline launch in various stages
 */
export interface LaunchCard {
  /** Unique identifier for the launch */
  id: string;
  
  /** Display title */
  title: string;
  
  /** Current phase in the launch lifecycle */
  phase: LaunchPhase;
  
  /** Category classification */
  category: LaunchCategory;
  
  /** ISO timestamp when launch was created */
  createdAt: string;
  
  /** ISO timestamp when launch was last updated */
  updatedAt: string;
  
  /** Quality score from 0-100 (composite metric) */
  qualityScore: number;
  
  /** Expected fork count range [min, max] */
  forkTargetRange: [number, number];
  
  /** Episode length in seconds (optional) */
  episodeLengthSec?: number;
  
  /** Tags for filtering and discovery */
  tags: string[];
  
  /** ID of the founder who created this launch (optional) */
  founderId?: string;
  
  /** Whether this launch is eligible for export */
  exportEligible?: boolean;
  
  /** Short description for preview cards */
  shortDescription?: string;
}

/**
 * Launchpad feed structure organizing launches by category
 */
export interface LaunchpadFeed {
  /** Trending launches (high quality score, recent activity) */
  trending: LaunchCard[];
  
  /** Draft launches (user's own or public drafts) */
  drafts: LaunchCard[];
  
  /** Recently graduated launches (moved to production) */
  recentlyGraduated: LaunchCard[];
}
