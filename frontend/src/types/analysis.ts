export type WorkflowType = "runtest" | "scada";

export interface AnalyzeRequest {
  folder_path?: string;     // Legacy mode
  session_id?: string;      // New session mode
  workflow_type: WorkflowType;
  template_path?: string;
  output_path?: string;
  render_template?: boolean;
}

export interface UploadResponse {
  session_id: string;
  original_filename: string;
  workflow_type: WorkflowType;
  config_preview: any;
  created_at: string;
  message: string;
}

export interface SessionSummary {
  session_id: string;
  created_at: string;
  workflow_type: WorkflowType;
  park_name?: string;
  status: string;
  charts_count: number;
  tables_count: number;
}

export interface SessionDetail {
  metadata: Record<string, any>;
  charts: ChartData[];
  tables: TableData[];
}

export interface ChartData {
  name: string;
  plotly_json: any;  // Format Plotly JSON
}

export interface TableData {
  name: string;
  columns: string[];
  rows: Record<string, any>[];
}

export interface AnalyzeResponse {
  status: "success" | "error";
  message: string;
  charts: ChartData[];
  tables: TableData[];
  report_path?: string;
  metadata: {
    park_name?: string;
    turbines?: string[];
    test_start?: string;
    test_end?: string;
    criteria?: Record<string, { value: any; unit: string }>;
  };
}
