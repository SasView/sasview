"""
Format SASBDB metadata for dialogs, logs, and data summary panels.
"""

import ast
import re

from .sasbdb_api import SASBDBDatasetInfo


def is_sasbdb_data(data) -> bool:
    meta = getattr(data, "meta_data", None) or {}
    return "SASBDB_code" in meta


def metadata_summary(info: SASBDBDatasetInfo) -> str:
    """Format dataset metadata for dialog status and logging."""
    lines = []
    if info.title:
        lines.append(f"Title: {info.title}")
    if info.sample_name:
        lines.append(f"Sample: {info.sample_name}")
    if info.molecule_name:
        lines.append(f"Molecule: {info.molecule_name}")
    if info.concentration:
        lines.append(f"Concentration: {info.concentration} {info.concentration_unit}")
    if info.buffer_description:
        lines.append(f"Buffer: {info.buffer_description}")
    if info.instrument:
        lines.append(f"Instrument: {info.instrument}")
    if info.wavelength:
        lines.append(f"Wavelength: {info.wavelength} {info.wavelength_unit}")
    if info.temperature:
        lines.append(f"Temperature: {info.temperature} {info.temperature_unit}")
    if info.rg is not None:
        lines.append(_format_rg_line(info.rg, info.rg_error, style="label"))
    if info.i0 is not None:
        lines.append(_format_i0_line(info.i0, info.i0_error, style="label"))
    if info.dmax is not None:
        lines.append(f"Dmax: {info.dmax} Å")
    if info.molecular_weight is not None:
        lines.append(f"MW: {info.molecular_weight:.1f} kDa")
    if info.publication_doi:
        lines.append(f"DOI: {info.publication_doi}")
    return "\n".join(lines)


def append_sasbdb_data_summary(text: str, data) -> str:
    """Clean dict repr lines and append SASBDB metadata for data summary panels."""
    if not is_sasbdb_data(data):
        return text
    return _clean_dict_lines(text) + format_data_panel(data)


def format_data_panel(data) -> str:
    """Format SASBDB metadata from a loaded data object."""
    meta = getattr(data, "meta_data", None) or {}
    if "SASBDB_code" not in meta:
        return ""

    lines = [
        "\n" + "=" * 50,
        "SASBDB Metadata",
        "=" * 50,
    ]

    header_parts = []
    if meta.get("SASBDB_code"):
        header_parts.append(f"Code: {meta['SASBDB_code']}")

    instrument_str, location_str = _instrument_from_data(data, meta)
    if instrument_str:
        header_parts.append(f"Instrument: {instrument_str}")
    if location_str:
        header_parts.append(location_str)

    detector_info = _detector_from_meta(meta)
    if detector_info:
        header_parts.append(f"Detector: {detector_info}")

    if header_parts:
        lines.append(" | ".join(header_parts))

    sample_line = _sample_line_from_data(data)
    if sample_line:
        lines.append(sample_line)

    if hasattr(data, "source") and data.source:
        source = data.source
        if hasattr(source, "wavelength") and source.wavelength is not None:
            wl_unit = getattr(source, "wavelength_unit", "Å") or "Å"
            lines.append(f"Wavelength: {source.wavelength} {wl_unit}")

    structural = _structural_lines_from_meta(meta)
    if structural:
        lines.append("Structural: " + " | ".join(structural))

    publication = _publication_lines_from_meta(meta)
    if publication:
        lines.append("Publication: " + " | ".join(publication))

    lines.extend(["=" * 50, ""])
    return "\n".join(line + "\n" for line in lines)


def _format_rg_line(rg, rg_error=None, style="label") -> str:
    if style == "panel":
        text = f"Rg = {rg:.2f}"
        if rg_error is not None:
            text += f" ± {rg_error:.2f}"
        return text + " Å"
    rg_text = f"Rg: {rg:.2f}"
    if rg_error:
        rg_text += f" ± {rg_error:.2f}"
    return f"{rg_text} Å"


def _format_i0_line(i0, i0_error=None, style="label") -> str:
    if style == "panel":
        text = f"I(0) = {i0:.4e}"
        if i0_error is not None:
            text += f" ± {i0_error:.4e}"
        return text
    text = f"I(0): {i0}"
    if i0_error:
        text += f" ± {i0_error}"
    return text


def _instrument_parts_from_dict(parsed_dict: dict) -> list[str]:
    parts = []
    if parsed_dict.get("name"):
        parts.append(parsed_dict["name"])
    if parsed_dict.get("beamline_name"):
        parts.append(f"Beamline: {parsed_dict['beamline_name']}")
    if parsed_dict.get("type_of_source"):
        parts.append(f"Source: {parsed_dict['type_of_source']}")
    if parsed_dict.get("city"):
        city = parsed_dict["city"]
        if parsed_dict.get("country"):
            parts.append(f"{city}, {parsed_dict['country']}")
        else:
            parts.append(city)
    elif parsed_dict.get("country"):
        parts.append(parsed_dict["country"])

    detector_info = None
    detector = parsed_dict.get("detector")
    if isinstance(detector, dict):
        detector_info = detector.get("name") or detector.get("type")
    elif detector:
        detector_info = str(detector)
    if detector_info:
        parts.append(f"Detector: {detector_info}")
    return parts


def _instrument_from_data(data, meta: dict) -> tuple[str | None, str | None]:
    instrument_str = None
    location_str = None

    if hasattr(data, "instrument") and data.instrument:
        if isinstance(data.instrument, str):
            instrument_str = data.instrument
        elif isinstance(data.instrument, dict):
            instrument_str = data.instrument.get("name") or data.instrument.get("beamline_name")
            if data.instrument.get("city") and data.instrument.get("country"):
                location_str = f"{data.instrument['city']}, {data.instrument['country']}"
            elif data.instrument.get("city"):
                location_str = data.instrument["city"]

    if not instrument_str:
        for key, val in meta.items():
            if isinstance(val, dict) and (
                "beamline_name" in val or "name" in val or "type_of_source" in val
            ):
                instrument_str = val.get("beamline_name") or val.get("name")
                if val.get("city") and val.get("country"):
                    location_str = f"{val['city']}, {val['country']}"
                elif val.get("city"):
                    location_str = val["city"]
                break
            if key in ("instrument", "source", "beamline") and isinstance(val, str):
                instrument_str = val
                break

    return instrument_str, location_str


def _detector_from_meta(meta: dict) -> str | None:
    for key, val in meta.items():
        if isinstance(val, dict) and ("detector" in key.lower() or "type" in val):
            detector_name = val.get("name") or val.get("type")
            if detector_name:
                return detector_name
        if "detector" in key.lower() and isinstance(val, str):
            return val
    return None


def _sample_line_from_data(data) -> str | None:
    if not hasattr(data, "sample") or not data.sample:
        return None

    sample = data.sample
    sample_parts = []
    if hasattr(sample, "name") and sample.name:
        sample_parts.append(sample.name)
    if hasattr(sample, "temperature") and sample.temperature is not None:
        temp_unit = getattr(sample, "temperature_unit", "K") or "K"
        sample_parts.append(f"T = {sample.temperature} {temp_unit}")
    if hasattr(sample, "details") and sample.details:
        for detail in sample.details:
            if detail.startswith("Concentration:"):
                sample_parts.append(detail.replace("Concentration: ", ""))
            elif detail.startswith("Buffer:"):
                sample_parts.append(detail.replace("Buffer: ", ""))

    if sample_parts:
        return f"Sample: {' | '.join(sample_parts)}"
    return None


def _structural_lines_from_meta(meta: dict) -> list[str]:
    lines = []
    if meta.get("SASBDB_Rg") is not None:
        lines.append(_format_rg_line(meta["SASBDB_Rg"], meta.get("SASBDB_Rg_error"), style="panel"))
    if meta.get("SASBDB_I0") is not None:
        lines.append(_format_i0_line(meta["SASBDB_I0"], meta.get("SASBDB_I0_error"), style="panel"))
    if meta.get("SASBDB_Dmax") is not None:
        lines.append(f"Dmax = {meta['SASBDB_Dmax']:.2f} Å")
    if meta.get("SASBDB_MW") is not None:
        mw = f"MW = {meta['SASBDB_MW']:.2f} kDa"
        if meta.get("SASBDB_MW_method"):
            mw += f" ({meta['SASBDB_MW_method']})"
        lines.append(mw)
    if meta.get("SASBDB_Porod_volume") is not None:
        lines.append(f"Porod Volume = {meta['SASBDB_Porod_volume']:.0f} Å³")
    return lines


def _publication_lines_from_meta(meta: dict) -> list[str]:
    lines = []
    if meta.get("SASBDB_authors"):
        lines.append(f"Authors: {_truncate_authors(meta['SASBDB_authors'])}")
    if meta.get("SASBDB_DOI"):
        lines.append(f"DOI: {meta['SASBDB_DOI']}")
    if meta.get("SASBDB_PMID"):
        lines.append(f"PMID: {meta['SASBDB_PMID']}")
    return lines


def _truncate_authors(authors: str, max_len: int = 50) -> str:
    if len(authors) <= max_len:
        return authors

    names = [name.strip() for name in authors.split(",") if name.strip()]
    if not names:
        return authors

    shown = names[0]
    for name in names[1:]:
        candidate = f"{shown}, {name}"
        if len(candidate) + len(" et al.") > max_len:
            return f"{shown} et al."
        shown = candidate

    if len(shown) > max_len:
        return f"{shown[: max_len - len(' et al.')].rstrip(', ')} et al."
    return shown


def _format_dict_line(line: str) -> str:
    stripped = line.strip()
    if not ("{" in stripped and "'" in stripped and ":" in stripped):
        return line

    label_match = re.match(r"^(\w+)\s*:\s*(.+)", stripped)
    if label_match:
        label = label_match.group(1)
        dict_str = label_match.group(2)
    elif stripped.startswith("{'") or stripped.startswith("{"):
        label = None
        dict_str = stripped
    else:
        return line

    try:
        parsed_dict = ast.literal_eval(dict_str)
        if not isinstance(parsed_dict, dict):
            return line

        parts = _instrument_parts_from_dict(parsed_dict)
        if parts:
            formatted = " | ".join(parts)
            return f"{label}: {formatted}" if label else formatted

        simple_parts = [
            f"{key}: {value}"
            for key, value in parsed_dict.items()
            if value is not None and not isinstance(value, dict)
        ]
        if simple_parts and len(simple_parts) <= 5:
            formatted = " | ".join(simple_parts)
            return f"{label}: {formatted}" if label else formatted
    except (ValueError, SyntaxError):
        pass

    return line


def _clean_dict_lines(text: str) -> str:
    cleaned_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if (
            "{" in stripped
            and "'" in stripped
            and ":" in stripped
            and (
                stripped.startswith("{'")
                or re.search(r":\s*\{", stripped)
                or re.search(r"\{'[^']+':", stripped)
            )
        ):
            if stripped.count("{") > 0 and stripped.count("}") > 0:
                cleaned_lines.append(_format_dict_line(line))
            else:
                cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)
