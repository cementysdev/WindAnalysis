from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Union
import pandas as pd


@dataclass()
class RunTestPipelineConfig:
    root_path: str
    template_path: str = "./assets/template_runtest.docx"
    output_path: str = "./output/runtest_output.docx"
    render_template: bool = True


@dataclass()
class ScadaRunnerConfig:
    root_path: str
    template_path: str = "./assets/template_scada.docx"
    output_path: str = "./output/scada_output.docx"
    render_template: bool = False


@dataclass()
class ScadaYamlSource:
    operation_path: str
    log_path: str
    operation_mapping: dict[str, str]
    log_mapping: dict[str, str]
    timestamp_key: str


@dataclass()
class GeneralInformation:
    name: str = ""
    description: str = ""
    park_name: str = ""
    client_name: str = ""
    client_location: str = ""
    commune: str = ""
    region: str = ""
    country: str = ""
    client_contact: str = ""
    number_wtg: str = ""
    model_wtg: str = ""
    nominal_power: str = ""
    v_rated: str = ""
    constructor: str = ""
    author_name: str = ""
    author_email: str = ""
    author_phone: str = ""
    writer_name: str = ""
    writer_email: str = ""
    writer_phone: str = ""
    verificator_name: str = ""
    verificator_email: str = ""
    verificator_phone: str = ""
    approver_name: str = ""
    approver_email: str = ""
    approver_phone: str = ""
    date_archive: str = ""


@dataclass()
class LogCode:
    manual_stop: list[str] = field(default_factory=list)
    authorized_stop: list[str] = field(default_factory=list)
    unauthorized_stop: list[str] = field(default_factory=list)
    curtailment: list[str] = field(default_factory=list)


@dataclass()
class Criterion:
    value: Optional[Any] = None
    unit: Optional[Any] = None
    specification: str = "=="
    description: bool = True


@dataclass()
class ValidationCriteria:
    validation_criterion: Optional[dict[str, Criterion]] = field(default_factory=dict)


@dataclass()
class TurbineGeneralInformation:
    model: Optional[str] = None
    nominal_power: Optional[float] = None
    constructor: Optional[str] = None
    path_operation_data: Optional[str] = None
    path_log_data: Optional[str] = None
    path_guaranteed_power_curve: Optional[str] = None
    timestamp: str = ""
    hub_height: str = ""
    rotor_diameter: str = ""
    gps_coordinates: list[float] = field(default_factory=list)


@dataclass()
class TurbineMappingOperationData:
    timestamp: Optional[str] = None
    wind_speed: Optional[str] = None
    wind_direction: Optional[str] = None
    availability: Optional[str] = None
    activation_power: Optional[str] = None
    rpm: Optional[str] = None
    temperature: Optional[str] = None
    nacelle_position: Optional[str] = None
    power_reference: Optional[str] = None
    pitch_pale1: Optional[str] = None
    pitch_pale2: Optional[str] = None
    pitch_pale3: Optional[str] = None


@dataclass()
class TurbineLogMapping:
    start_date: Any  # str ou list[str] pour ["date", "time"]
    end_date: Any  # str ou list[str] pour ["date", "time"]
    name: Optional[str] = None
    oper: Optional[str] = None
    status: Optional[str] = None

    def get_start_date_columns(self) -> list[str]:
        """
        Retourne la liste des colonnes pour start_date.

        Returns:
            Liste de colonnes (ex: ["date", "time"] ou ["timestamp"])
        """
        if isinstance(self.start_date, list):
            return self.start_date
        return [self.start_date]

    def get_end_date_columns(self) -> list[str]:
        """
        Retourne la liste des colonnes pour end_date.

        Returns:
            Liste de colonnes (ex: ["date", "time"] ou ["timestamp"])
        """
        if isinstance(self.end_date, list):
            return self.end_date
        return [self.end_date]


@dataclass()
class TurbineConfig:
    turbine_id: str
    general_information: Optional[TurbineGeneralInformation] = None
    mapping_operation_data: Optional[TurbineMappingOperationData] = None
    mapping_log_data: Optional[TurbineLogMapping] = None
    test_start: Optional[Union[str, pd.Timestamp]] = None
    test_end: Optional[Union[str, pd.Timestamp]] = None


@dataclass()
class TurbineFarm:
    farm: Optional[dict[str, TurbineConfig]] = field(default_factory=dict)
