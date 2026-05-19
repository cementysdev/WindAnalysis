/**
 * Types for parsing and displaying config.yml structure
 */

export interface ParsedConfig {
  general_information: GeneralInformation;
  validation_criteria: ValidationCriteria;
  render_template?: boolean;
  template_path?: string;
  output_path?: string;
  log_data?: LogData;
  dynamic_fields: DynamicFields;
}

export interface GeneralInformation {
  name?: string;
  description?: string;
  park_name: string;
  client_name?: string;
  client_location?: string;
  client_contact?: string;
  number_wtg?: number;
  model_wtg?: string;
  nominal_power?: string;
  v_rated?: number;
  constructor?: string;
  author_name?: string;
  author_email?: string;
  author_phone?: string;
  writer_name?: string;
  writer_email?: string;
  writer_phone?: string;
  verificator_name?: string;
  verificator_email?: string;
  verificator_phone?: string;
  date_archive?: string;
}

export interface ValidationCriteria {
  consecutive_hours?: CriterionValue;
  cut_in_to_cut_out?: CriterionValue;
  nominal_power_hours?: CriterionValue;
  local_restarts?: CriterionValue;
  availability?: CriterionValue;
  // SCADA specific
  eba_cut_in_cut_out?: CriterionValue;
  eba_manufacturer?: CriterionValue;
  data_availability?: CriterionValue;
}

export interface CriterionValue {
  value: number | string;
  unit: string;
  specification?: any;
  description?: string | null;
}

export interface LogData {
  wtg_ok?: any[];
  authorized_stop?: any[];
  unauthorized_stop?: any[];
}

export interface DynamicFields {
  turbines: TurbineConfiguration[];
}

export interface TurbineConfiguration {
  turbine_id: string;
  general_information: TurbineGeneralInfo;
  mapping_operation_data: Record<string, string | null>;
  mapping_log_data: Record<string, string | string[]>;
  test_start: string;
  test_end: string;
}

export interface TurbineGeneralInfo {
  model: string;
  nominal_power: number;
  constructor: string;
  path_operation_data: string;
  path_log_data: string;
  path_guaranteed_power_curve?: string | null;
}
