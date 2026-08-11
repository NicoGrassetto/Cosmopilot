from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from io import TextIOWrapper
from pathlib import Path
from threading import Lock
from typing import Any, Callable
from uuid import uuid4
from zipfile import BadZipFile, ZipFile


_DATA_ARCHIVE = (
	Path(__file__).resolve().parents[3]
	/ "data"
	/ "eu_resilience"
	/ "documents"
	/ "data.zip"
)
_PLAYBOOK_NAME = "EU Cross-Agency Coordination Playbook"
_PLAYBOOK_VERSION = "1.0-demo"
_REQUIRED_CRITERIA = 3
_CASE_REGISTER: dict[str, dict[str, Any]] = {}
_CASE_REGISTER_LOCK = Lock()


def _coerce_csv_value(value: str | None) -> Any:
	if value is None:
		return None

	value = value.strip()
	if not value:
		return None

	try:
		return int(value)
	except ValueError:
		try:
			return float(value)
		except ValueError:
			return value


def _read_csv(member: str) -> list[dict[str, Any]]:
	try:
		with ZipFile(_DATA_ARCHIVE) as archive:
			with archive.open(member) as raw_stream:
				with TextIOWrapper(raw_stream, encoding="utf-8-sig", newline="") as stream:
					return [
						{
							key: _coerce_csv_value(value)
							for key, value in row.items()
							if key is not None
						}
						for row in csv.DictReader(stream)
					]
	except (FileNotFoundError, KeyError, BadZipFile) as exc:
		raise RuntimeError(
			f"Unable to read resilience evidence member {member!r} from {_DATA_ARCHIVE}."
		) from exc


def _resolve_country(country: str) -> dict[str, Any]:
	if not isinstance(country, str) or not country.strip():
		raise ValueError("country must be a non-empty EU country name or ISO code")

	lookup = country.strip().casefold()
	aliases = {
		"czechia": "CZE",
		"gr": "GRC",
	}
	lookup = aliases.get(lookup, lookup).casefold()

	for region in _read_csv("data/regions.csv"):
		identifiers = {
			str(region[field]).casefold()
			for field in ("country", "iso2", "iso3")
			if region.get(field)
		}
		if lookup in identifiers:
			return region

	raise ValueError(f"Unknown EU27 country or ISO code: {country!r}")


def _country_rows(member: str, iso3: str) -> list[dict[str, Any]]:
	return [row for row in _read_csv(member) if row.get("iso3") == iso3]


def _single_country_row(member: str, iso3: str) -> dict[str, Any] | None:
	rows = _country_rows(member, iso3)
	if len(rows) > 1:
		raise RuntimeError(f"Expected one {member} record for {iso3}, found {len(rows)}.")
	return rows[0] if rows else None


def _evidence_package_id(scorecard: dict[str, Any]) -> str:
	date = str(scorecard["date"]).replace("-", "")
	return f"EU27-{date}-{scorecard['iso3']}"


def _evidence_section(
	record: dict[str, Any],
	*,
	source_label: str,
	classification: str,
	snapshot_date: str,
) -> dict[str, Any]:
	identity_fields = {"date", "iso2", "iso3", "country", "zone"}
	return {
		"source_label": source_label,
		"classification": classification,
		"observation_date": record.get("date") or snapshot_date,
		"geographic_grain": "country",
		"values": {
			key: value
			for key, value in record.items()
			if key not in identity_fields
		},
	}


def get_resilience_priorities(limit: int) -> dict[str, Any]:
	"""Return the highest-risk countries in the static EU27 demo snapshot."""
	if isinstance(limit, bool) or not isinstance(limit, int):
		raise TypeError("limit must be an integer")
	if not 1 <= limit <= 27:
		raise ValueError("limit must be between 1 and 27")

	scorecard = _read_csv("data/region_scorecard.csv")
	ranked = sorted(
		scorecard,
		key=lambda row: (-float(row["overall_risk"]), str(row["country"])),
	)
	snapshot_dates = sorted({str(row["date"]) for row in ranked})
	limitations = [
		"The values are a static demo snapshot, not live operational data.",
		"Overall and domain risk scores are synthetic derived composites.",
		"All observations have country-level geographic grain.",
	]
	if len(snapshot_dates) != 1:
		limitations.append(
			"The scorecard contains conflicting observation dates: "
			+ ", ".join(snapshot_dates)
		)

	priorities = []
	for rank, row in enumerate(ranked[:limit], start=1):
		priorities.append(
			{
				"rank": rank,
				"country": row["country"],
				"iso3": row["iso3"],
				"zone": row["zone"],
				"priority_score": row["overall_risk"],
				"severity": row["severity"],
				"observation_date": row["date"],
				"evidence_package_id": _evidence_package_id(row),
				"lead_response_agency": row["lead_response_agency"],
				"classification": "synthetic-derived composite",
				"domain_scores": {
					"environmental_risk": row["environmental_risk"],
					"population_vulnerability": row["population_vulnerability"],
					"health_pressure": row["health_pressure"],
					"food_risk": row["food_risk"],
					"economic_stress": row["economic_stress"],
					"financial_exposure": row["financial_exposure"],
				},
			}
		)

	return {
		"snapshot_date": snapshot_dates[0] if len(snapshot_dates) == 1 else None,
		"snapshot_type": "static demo snapshot",
		"source_label": "Curated EU27 resilience scorecard",
		"geographic_grain": "country",
		"ranking_metric": "overall_risk descending",
		"available_country_count": len(ranked),
		"returned_country_count": len(priorities),
		"priorities": priorities,
		"limitations": limitations,
	}


def get_country_resilience_evidence(country: str) -> dict[str, Any]:
	"""Return a joined, provenance-labelled evidence package for one EU country."""
	region = _resolve_country(country)
	iso3 = str(region["iso3"])
	scorecard = _single_country_row("data/region_scorecard.csv", iso3)
	if scorecard is None:
		raise RuntimeError(f"No resilience scorecard record is available for {iso3}.")

	snapshot_date = str(scorecard["date"])
	evidence: dict[str, Any] = {}
	missing_sources: list[str] = []
	section_specs = (
		(
			"environmental",
			"data/copernicus_environment_daily.csv",
			"Copernicus curated environmental observations",
			"source-derived",
		),
		(
			"wildfire",
			"data/effis_wildfire_country_2026.csv",
			"EFFIS curated wildfire observations",
			"source-derived",
		),
		(
			"food_supply",
			"data/efsa_food_supply_daily.csv",
			"EFSA curated food-supply observations",
			"source-derived",
		),
		(
			"health",
			"data/ecdc_health_daily.csv",
			"ECDC curated health observations",
			"source-derived",
		),
		(
			"economic",
			"data/esm_macro_stability.csv",
			"ESM curated macro-stability observations",
			"source-derived",
		),
		(
			"banking_exposure",
			"data/eba_banking_exposure.csv",
			"Curated EBA-aligned banking exposure",
			"synthetic",
		),
		(
			"banking_stress_test",
			"data/eba_2025_stress_test_country_synthetic.csv",
			"EBA 2025 aggregates with a synthetic country overlay",
			"mixed derived and synthetic",
		),
	)
	for section_name, member, source_label, classification in section_specs:
		record = _single_country_row(member, iso3)
		if record is None:
			missing_sources.append(source_label)
			continue
		evidence[section_name] = _evidence_section(
			record,
			source_label=source_label,
			classification=classification,
			snapshot_date=snapshot_date,
		)

	evidence["population"] = _evidence_section(
		region,
		source_label="Curated EU27 demographic reference",
		classification="mixed source-derived and synthetic composite",
		snapshot_date=snapshot_date,
	)

	alerts = []
	for alert in _country_rows("data/realtime_alerts.csv", iso3):
		alerts.append(
			{
				"event_id": alert["event_id"],
				"event_time": alert["event_time"],
				"source_label": alert["source_agency"],
				"alert_type": alert["alert_type"],
				"severity": alert["severity"],
				"confidence": alert["confidence"],
				"summary": alert["summary"],
				"classification": "synthetic",
			}
		)

	limitations = [
		f"Evidence is a static demo snapshot observed on {snapshot_date}.",
		"Geographic grain is country level; no regional or local precision is implied.",
		"Overall risk, domain scores, and population vulnerability are synthetic derived composites.",
		"Banking records and climate-credit losses are synthetic overlays.",
		"EBA adverse-scenario values are stress-test scenarios, not forecasts of bank failure or evidence of current distress.",
	]
	stress_test = evidence.get("banking_stress_test", {}).get("values", {})
	if str(stress_test.get("stress_data_basis", "")).startswith("Synthetic EU27 fallback"):
		limitations.append(
			"Banking stress values use a synthetic EU27 fallback because no EBA reference bank was available for this country."
		)
	if missing_sources:
		limitations.append("Missing evidence sources: " + ", ".join(missing_sources))

	return {
		"evidence_package_id": _evidence_package_id(scorecard),
		"snapshot_date": snapshot_date,
		"snapshot_type": "static demo snapshot",
		"country": {
			"name": region["country"],
			"iso2": region["iso2"],
			"iso3": iso3,
			"zone": region["zone"],
		},
		"geographic_grain": "country",
		"priority": {
			"severity": scorecard["severity"],
			"overall_risk": scorecard["overall_risk"],
			"lead_response_agency": scorecard["lead_response_agency"],
			"classification": "synthetic-derived composite",
			"domain_scores": {
				"environmental_risk": scorecard["environmental_risk"],
				"population_vulnerability": scorecard["population_vulnerability"],
				"health_pressure": scorecard["health_pressure"],
				"food_risk": scorecard["food_risk"],
				"economic_stress": scorecard["economic_stress"],
				"financial_exposure": scorecard["financial_exposure"],
			},
		},
		"evidence": evidence,
		"alerts": alerts,
		"confidence": {
			"alert_confidence_values": [alert["confidence"] for alert in alerts],
			"note": "Alert confidence is source metadata, not model certainty or an independently calibrated package score.",
		},
		"classifications": {
			"source_derived": [
				"environmental observations",
				"wildfire observations",
				"food-supply observations",
				"health observations",
				"macroeconomic observations",
			],
			"derived": ["EBA country aggregates where reference banks are available"],
			"synthetic": [
				"alerts",
				"banking records",
				"climate-credit losses",
				"composite vulnerability and risk scores",
				"country fallback estimates where disclosed",
			],
		},
		"limitations": limitations,
	}


def evaluate_coordination_playbook(
	country: str,
	evidence_package_id: str,
) -> dict[str, Any]:
	"""Apply the deterministic illustrative coordination criteria."""
	package = get_country_resilience_evidence(country)
	if evidence_package_id != package["evidence_package_id"]:
		raise ValueError(
			"evidence_package_id does not match the current country evidence package"
		)

	criterion_specs = (
		(
			"environmental_pressure",
			"Environmental risk",
			"environmental",
			"environmental_risk",
			70,
			"Copernicus",
		),
		(
			"health_system_pressure",
			"Health-system pressure",
			"health",
			"health_pressure",
			75,
			"ECDC",
		),
		(
			"food_system_pressure",
			"Food-system pressure",
			"food_supply",
			"food_risk",
			75,
			"EFSA",
		),
		(
			"financial_exposure",
			"Financial exposure",
			"banking_exposure",
			"financial_exposure",
			60,
			"EBA",
		),
		(
			"economic_stress",
			"Economic stress",
			"economic",
			"economic_stress",
			60,
			"ESM",
		),
	)

	criteria = []
	for criterion_id, name, section_name, metric, threshold, agency in criterion_specs:
		section = package["evidence"].get(section_name)
		value = section["values"].get(metric) if section else None
		if isinstance(value, (int, float)) and not isinstance(value, bool):
			status = "met" if value >= threshold else "not_met"
		else:
			status = "indeterminate"
		criteria.append(
			{
				"criterion_id": criterion_id,
				"name": name,
				"status": status,
				"observed_value": value,
				"threshold": threshold,
				"comparison": "greater_than_or_equal",
				"responsible_agency": agency,
				"source_label": section["source_label"] if section else None,
				"observation_date": section["observation_date"] if section else None,
			}
		)

	criteria_met = [item for item in criteria if item["status"] == "met"]
	criteria_not_met = [item for item in criteria if item["status"] == "not_met"]
	criteria_indeterminate = [item for item in criteria if item["status"] == "indeterminate"]
	if len(criteria_met) >= _REQUIRED_CRITERIA:
		eligibility = "eligible"
		coordination_eligible: bool | None = True
	elif len(criteria_met) + len(criteria_indeterminate) >= _REQUIRED_CRITERIA:
		eligibility = "indeterminate"
		coordination_eligible = None
	else:
		eligibility = "not_eligible"
		coordination_eligible = False

	lead_agency = (
		str(package["priority"]["lead_response_agency"])
		if coordination_eligible
		else None
	)
	participating_agencies = []
	if lead_agency:
		for criterion in criteria_met:
			agency = str(criterion["responsible_agency"])
			if agency != lead_agency and agency not in participating_agencies:
				participating_agencies.append(agency)

	review_steps = []
	if lead_agency:
		review_steps = [
			"Validate the evidence package, provenance, and disclosed limitations.",
			f"Convene {lead_agency} and the participating agencies for an internal coordination review.",
			"Confirm the country-level observations with the responsible national authorities.",
			"Record the coordination decision, follow-up owners, and review date.",
		]

	limitations = list(package["limitations"])
	limitations.append(
		"This is illustrative demo logic, not formal EU policy, legal advice, or an emergency-response mandate."
	)

	return {
		"playbook_name": _PLAYBOOK_NAME,
		"playbook_version": _PLAYBOOK_VERSION,
		"evidence_package_id": package["evidence_package_id"],
		"snapshot_date": package["snapshot_date"],
		"country": package["country"],
		"priority_level": package["priority"]["severity"],
		"eligibility": eligibility,
		"coordination_eligible": coordination_eligible,
		"required_criteria_count": _REQUIRED_CRITERIA,
		"criteria": criteria,
		"criteria_met": [item["criterion_id"] for item in criteria_met],
		"criteria_not_met": [item["criterion_id"] for item in criteria_not_met],
		"criteria_indeterminate": [
			item["criterion_id"] for item in criteria_indeterminate
		],
		"lead_agency": lead_agency,
		"participating_agencies": participating_agencies,
		"recommended_review_steps": review_steps,
		"limitations": limitations,
	}


def open_coordination_case(
	country: str,
	evidence_package_id: str,
	playbook_version: str,
	reason: str,
	lead_agency: str,
	participating_agencies: list[str],
	review_steps: list[str],
) -> dict[str, Any]:
	"""Record a validated, application-approved decision-card payload in memory."""
	if not isinstance(reason, str) or not reason.strip():
		raise ValueError("reason must be a non-empty string")
	if not isinstance(lead_agency, str) or not lead_agency.strip():
		raise ValueError("lead_agency must be a non-empty string")
	if not isinstance(participating_agencies, list) or not all(
		isinstance(agency, str) and agency.strip()
		for agency in participating_agencies
	):
		raise ValueError("participating_agencies must be a list of non-empty strings")
	if not isinstance(review_steps, list) or not all(
		isinstance(step, str) and step.strip()
		for step in review_steps
	):
		raise ValueError("review_steps must be a list of non-empty strings")

	evaluation = evaluate_coordination_playbook(country, evidence_package_id)
	if evaluation["coordination_eligible"] is not True:
		raise ValueError("the current evidence package is not eligible for coordination")
	if playbook_version != evaluation["playbook_version"]:
		raise ValueError("playbook_version does not match the current playbook evaluation")
	if lead_agency.casefold() != str(evaluation["lead_agency"]).casefold():
		raise ValueError("lead_agency does not match the current playbook evaluation")

	expected_agencies = [str(agency) for agency in evaluation["participating_agencies"]]
	provided_agencies = [agency.strip() for agency in participating_agencies]
	if len({agency.casefold() for agency in provided_agencies}) != len(provided_agencies):
		raise ValueError("participating_agencies must not contain duplicates")
	if {agency.casefold() for agency in provided_agencies} != {
		agency.casefold() for agency in expected_agencies
	}:
		raise ValueError(
			"participating_agencies do not match the current playbook evaluation"
		)

	expected_steps = [str(step) for step in evaluation["recommended_review_steps"]]
	if [" ".join(step.split()).casefold() for step in review_steps] != [
		" ".join(step.split()).casefold() for step in expected_steps
	]:
		raise ValueError("review_steps do not match the current playbook evaluation")

	submitted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
	case_id = f"EU-CRC-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:8].upper()}"
	canonical_country = str(evaluation["country"]["name"])
	receipt = {
		"coordination_case_id": case_id,
		"submission_status": "submitted",
		"submitted_at": submitted_at,
		"country": canonical_country,
		"lead_agency": evaluation["lead_agency"],
		"participating_agencies": expected_agencies,
		"evidence_correlation_id": evidence_package_id,
		"playbook_version": evaluation["playbook_version"],
		"business_link": f"/coordination-cases/{case_id}",
	}
	with _CASE_REGISTER_LOCK:
		_CASE_REGISTER[case_id] = {
			"approved_payload": {
				"country": canonical_country,
				"evidence_package_id": evidence_package_id,
				"playbook_version": evaluation["playbook_version"],
				"reason": reason.strip(),
				"lead_agency": evaluation["lead_agency"],
				"participating_agencies": expected_agencies,
				"review_steps": expected_steps,
			},
			"receipt": receipt,
		}

	return dict(receipt)


LOCAL_FUNCTIONS: dict[str, Callable[..., dict[str, Any]]] = {
	"get_resilience_priorities": get_resilience_priorities,
	"get_country_resilience_evidence": get_country_resilience_evidence,
	"evaluate_coordination_playbook": evaluate_coordination_playbook,
	"open_coordination_case": open_coordination_case,
}


def call_local_function(
	name: str,
	arguments: str | dict[str, Any],
	*,
	allow_side_effects: bool = False,
) -> str:
	"""Dispatch one Responses API function call and return JSON output."""
	try:
		payload = json.loads(arguments or "{}") if isinstance(arguments, str) else arguments
		if not isinstance(payload, dict):
			raise TypeError("function arguments must decode to a JSON object")

		function = LOCAL_FUNCTIONS.get(name)
		if function is None:
			raise ValueError(f"No local function is registered for {name!r}")
		if name == "open_coordination_case" and not allow_side_effects:
			raise PermissionError(
				"open_coordination_case requires explicit application approval"
			)

		return json.dumps(function(**payload), ensure_ascii=True)
	except (PermissionError, TypeError, ValueError, RuntimeError) as exc:
		return json.dumps(
			{
				"error": str(exc),
				"error_type": type(exc).__name__,
				"function": name,
			},
			ensure_ascii=True,
		)