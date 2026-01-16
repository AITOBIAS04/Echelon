/**
 * Export Types
 * ============
 * 
 * TypeScript interfaces for Echelon data exports, including export jobs,
 * filters, scopes, and dataset schemas.
 */

/**
 * ExportDatasetKind
 * 
 * Types of datasets that can be exported from Echelon.
 */
export type ExportDatasetKind = 'rlmf' | 'human_judgement' | 'audit_trace';

/**
 * ExportScope
 * 
 * Defines the scope of data to export (which timelines, theatres, date range).
 */
export interface ExportScope {
  /** Scope level: user's data, workspace, or global */
  scope: 'my' | 'workspace' | 'global';
  
  /** Specific timeline IDs to include (optional) */
  timelineIds?: string[];
  
  /** Specific theatre IDs to include (optional) */
  theatreIds?: string[];
  
  /** Start date for export (ISO 8601 format) */
  dateFrom?: string;
  
  /** End date for export (ISO 8601 format) */
  dateTo?: string;
}

/**
 * ExportFilter
 * 
 * Filters to apply when exporting data.
 */
export interface ExportFilter {
  /** Type of dataset to export */
  kind: ExportDatasetKind;
  
  /** Seed tier filter (optional) */
  seedTier?: 'tier1' | 'tier2' | 'tier3';
  
  /** Only include timelines with active paradoxes */
  paradoxOnly?: boolean;
  
  /** Only include out-of-distribution episodes */
  oodOnly?: boolean;
  
  /** Minimum number of forks required */
  minForkCount?: number;
  
  /** Maximum episode duration in seconds */
  maxEpisodeDurationSec?: number;
}

/**
 * ExportJob
 * 
 * Represents an export job that processes and generates a dataset.
 */
export interface ExportJob {
  /** Unique job identifier */
  id: string;
  
  /** Type of dataset being exported */
  kind: ExportDatasetKind;
  
  /** Current status of the export job */
  status: 'queued' | 'running' | 'completed' | 'failed';
  
  /** ISO timestamp when job was created */
  createdAt: string;
  
  /** ISO timestamp when job completed (optional) */
  completedAt?: string;
  
  /** Scope of data to export */
  scope: ExportScope;
  
  /** Filters to apply to the export */
  filter: ExportFilter;
  
  /** Number of rows in the exported dataset (optional) */
  rowCount?: number;
  
  /** Size of the exported file in bytes (optional) */
  byteSize?: number;
  
  /** Error message if job failed (optional) */
  error?: string;
  
  /** URL to download the exported dataset (optional, may be empty in demo) */
  downloadUrl?: string;
}

/**
 * DatasetSchemaField
 * 
 * Describes a field in a dataset schema.
 */
export interface DatasetSchemaField {
  /** Field name */
  name: string;
  
  /** Field data type */
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  
  /** Human-readable description of the field */
  description: string;
}

/**
 * DatasetPreview
 * 
 * Preview of a dataset including schema and sample rows.
 */
export interface DatasetPreview {
  /** Type of dataset */
  kind: ExportDatasetKind;
  
  /** Schema version identifier (e.g., 'human_judgement_v0.1') */
  schemaVersion: string;
  
  /** Schema fields describing the dataset structure */
  fields: DatasetSchemaField[];
  
  /** Sample rows from the dataset (maximum 20 rows) */
  sampleRows: Record<string, any>[];
}
