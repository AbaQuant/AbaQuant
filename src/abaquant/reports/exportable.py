"""Exportable Markdown, HTML, and PDF reports for AbaQuant objects.

Purpose
-------
The module provides one small dependency-light reporting primitive used by
option models, portfolio objects, credit assessments, and integrated risk
summaries. Reports are intentionally structured as plain text, scalar mappings,
and tabular data so they can be exported consistently without requiring a web
framework or notebook runtime.

Conventions
-----------
Markdown and HTML exports are always available. PDF export writes a compact
text-based PDF using the standard library only. The PDF output is designed for
portable archival of report contents, not pixel-perfect chart reproduction.

Scope and limitations
---------------------
The reporting layer formats already-computed diagnostics. It does not recalculate
prices, portfolio allocations, financial-statement metrics, or market data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from textwrap import wrap

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance, merge_provenance

ReportValue = object


@dataclass(frozen=True)
class ReportTable:
    """One tabular block inside an exportable report.

    Parameters
    ----------
    title : str
        Human-readable table title.
    data : pandas.DataFrame or mapping or sequence of mappings
        Table-like content converted to a pandas DataFrame for rendering.
    description : str, optional
        Short explanatory text printed before the table.
    max_rows : int, optional
        Maximum number of rows to render. Remaining rows are omitted from the
        exported preview rather than changing the underlying data object.
    """

    title: str
    data: pd.DataFrame | Mapping[str, object] | Sequence[Mapping[str, object]]
    description: str | None = None
    max_rows: int | None = None

    def frame(self) -> pd.DataFrame:
        """Return this table as a defensive pandas DataFrame copy."""
        if isinstance(self.data, pd.DataFrame):
            frame = self.data.copy(deep=True)
        elif isinstance(self.data, Mapping):
            if all(
                not isinstance(value, (Mapping, Sequence)) or isinstance(value, str)
                for value in self.data.values()
            ):
                frame = pd.DataFrame([dict(self.data)])
            else:
                frame = pd.DataFrame(self.data)
        else:
            frame = pd.DataFrame(list(self.data))
        if self.max_rows is not None:
            frame = frame.head(int(self.max_rows))
        return frame


@dataclass(frozen=True)
class ReportSection:
    """One titled narrative section inside an exportable report.

    Parameters
    ----------
    title : str
        Section heading.
    body : str, optional
        Narrative body text.
    metrics : Mapping[str, object], optional
        Scalar key-value diagnostics displayed below the body.
    tables : Sequence[ReportTable], optional
        Tables rendered within this section.
    """

    title: str
    body: str | None = None
    metrics: Mapping[str, object] = field(default_factory=dict)
    tables: Sequence[ReportTable] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExportableReport:
    """Structured report that can be exported as Markdown, HTML, or PDF.

    Parameters
    ----------
    title : str
        Report title.
    subtitle : str, optional
        Short subtitle shown beneath the title.
    sections : Sequence[ReportSection], optional
        Ordered report sections.
    metadata : Mapping[str, object], optional
        Report-level metadata such as object type, generated-at timestamp, or
        model convention details.
    """

    title: str
    subtitle: str | None = None
    sections: Sequence[ReportSection] = field(default_factory=tuple)
    metadata: Mapping[str, object] = field(default_factory=dict)
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Attach report provenance when no explicit record was supplied."""
        if self.provenance is None:
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="derived",
                    dataset="exportable_report",
                    transformation_steps=("structured report rendering",),
                    request={"title": self.title, "metadata": dict(self.metadata)},
                ),
            )

    def to_markdown(self, path: str | Path | None = None) -> str:
        """Return the report as Markdown and optionally write it to disk.

        Parameters
        ----------
        path : str or pathlib.Path, optional
            Destination path. Parent directories are created when needed.

        Returns
        -------
        str
            Markdown representation of the report.
        """
        lines: list[str] = [f"# {self.title}", ""]
        if self.subtitle:
            lines.extend([str(self.subtitle), ""])
        if self.metadata:
            lines.extend(["## Metadata", ""])
            for key, value in self.metadata.items():
                lines.append(f"- **{_humanize_key(key)}:** {_format_value(value)}")
            lines.append("")
        lines.extend(["## Provenance", ""])
        for key, value in self.provenance.as_dict().items():
            lines.append(f"- **{_humanize_key(key)}:** {_format_value(value)}")
        lines.append("")
        for section in self.sections:
            lines.extend(_section_to_markdown(section))
        text = "\n".join(lines).rstrip() + "\n"
        if path is not None:
            _write_text(path, text)
        return text

    def to_html(self, path: str | Path | None = None) -> str:
        """Return the report as standalone HTML and optionally write it to disk.

        Parameters
        ----------
        path : str or pathlib.Path, optional
            Destination path. Parent directories are created when needed.

        Returns
        -------
        str
            Standalone HTML document.
        """
        parts = [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            f"<title>{escape(self.title)}</title>",
            "<style>",
            "body{font-family:Arial,Helvetica,sans-serif;margin:2rem;line-height:1.45;color:#222;}",
            "table{border-collapse:collapse;margin:1rem 0;width:100%;font-size:0.92rem;}",
            "th,td{border:1px solid #ddd;padding:0.35rem 0.5rem;text-align:right;}",
            "th:first-child,td:first-child{text-align:left;}",
            "th{background:#f5f5f5;}",
            "code{background:#f6f6f6;padding:0.1rem 0.2rem;}",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{escape(self.title)}</h1>",
        ]
        if self.subtitle:
            parts.append(f"<p>{escape(str(self.subtitle))}</p>")
        if self.metadata:
            parts.extend(["<h2>Metadata</h2>", "<dl>"])
            for key, value in self.metadata.items():
                parts.append(
                    f"<dt>{escape(_humanize_key(key))}</dt><dd>{escape(_format_value(value))}</dd>"
                )
            parts.append("</dl>")
        parts.extend(["<h2>Provenance</h2>", "<dl>"])
        for key, value in self.provenance.as_dict().items():
            parts.append(
                f"<dt>{escape(_humanize_key(key))}</dt><dd>{escape(_format_value(value))}</dd>"
            )
        parts.append("</dl>")
        for section in self.sections:
            parts.extend(_section_to_html(section))
        parts.extend(["</body>", "</html>"])
        html = "\n".join(parts) + "\n"
        if path is not None:
            _write_text(path, html)
        return html

    def to_pdf(self, path: str | Path) -> Path:
        """Write a simple text PDF representation of the report.

        Parameters
        ----------
        path : str or pathlib.Path
            Destination PDF path. Parent directories are created when needed.

        Returns
        -------
        pathlib.Path
            Resolved destination path.
        """
        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        text_lines = _markdown_to_plain_lines(self.to_markdown())
        target.write_bytes(_build_text_pdf(text_lines, title=self.title))
        return target

    def save(
        self, directory: str | Path, stem: str, formats: Sequence[str] = ("markdown", "html")
    ) -> dict[str, Path]:
        """Export this report to several formats in one directory.

        Parameters
        ----------
        directory : str or pathlib.Path
            Destination directory.
        stem : str
            Base filename without extension.
        formats : Sequence[str], default=("markdown", "html")
            Output format labels. Supported values are ``"markdown"``,
            ``"md"``, ``"html"``, and ``"pdf"``.

        Returns
        -------
        dict[str, pathlib.Path]
            Mapping from requested format label to written path.
        """
        destination = Path(directory).expanduser()
        destination.mkdir(parents=True, exist_ok=True)
        outputs: dict[str, Path] = {}
        for output_format in formats:
            normalized = str(output_format).lower().strip()
            if normalized in {"markdown", "md"}:
                path = destination / f"{stem}.md"
                self.to_markdown(path)
            elif normalized == "html":
                path = destination / f"{stem}.html"
                self.to_html(path)
            elif normalized == "pdf":
                path = destination / f"{stem}.pdf"
                self.to_pdf(path)
            else:
                raise ValueError("formats may contain only 'markdown', 'md', 'html', or 'pdf'.")
            outputs[normalized] = path
        return outputs

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-friendly nested representation of the report."""
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "metadata": dict(self.metadata),
            "provenance": self.provenance.as_dict(),
            "sections": [
                {
                    "title": section.title,
                    "body": section.body,
                    "metrics": dict(section.metrics),
                    "tables": [table.frame().to_dict("records") for table in section.tables],
                }
                for section in self.sections
            ],
        }


def generated_metadata(report_type: str, **extra: object) -> dict[str, object]:
    """Return standard metadata used by AbaQuant generated reports."""
    metadata: dict[str, object] = {
        "report_type": report_type,
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
    }
    metadata.update(extra)
    return metadata


def build_option_model_report(model: object, option_type: str = "call") -> ExportableReport:
    """Build an exportable report for one vanilla option pricing model."""
    diagnostics = model.diagnostics(option_type)
    model_inputs = {
        "spot_price": getattr(model, "spot_price", None),
        "strike_price": getattr(model, "strike_price", None),
        "maturity_years": getattr(model, "maturity_years", None),
        "risk_free_rate": getattr(model, "risk_free_rate", None),
        "volatility": getattr(model, "volatility", None),
        "dividend_yield": getattr(model, "dividend_yield", None),
    }
    return ExportableReport(
        title=f"Option Model Report: {model.__class__.__name__}",
        subtitle="Scalar pricing diagnostics for one vanilla option contract.",
        metadata=generated_metadata("option_model", option_type=option_type),
        provenance=merge_provenance(
            [diagnostics.provenance],
            provider="derived",
            dataset="option_model_report",
            transformation_steps=("option diagnostics report generation",),
            request={"model_class": model.__class__.__name__, "option_type": option_type},
        ),
        sections=(
            ReportSection(
                "Model inputs",
                metrics={key: value for key, value in model_inputs.items() if value is not None},
            ),
            ReportSection(
                "Pricing diagnostics",
                metrics={
                    "option_type": diagnostics.option_type,
                    "price": diagnostics.price,
                    "intrinsic_value": diagnostics.intrinsic_value,
                    "extrinsic_value": diagnostics.extrinsic_value,
                    "moneyness": diagnostics.moneyness,
                    "forward_moneyness": diagnostics.forward_moneyness,
                    "break_even_price": diagnostics.break_even_price,
                },
            ),
            ReportSection(
                "Greeks",
                tables=(ReportTable("Selected Greeks", pd.DataFrame([diagnostics.greeks])),),
            ),
        ),
    )


def build_portfolio_allocator_report(
    allocator: object, *, backtest_kwargs: Mapping[str, object] | None = None
) -> ExportableReport:
    """Build an exportable report for a portfolio allocator object."""
    context = allocator.context
    returns = context.periodic_returns.copy(deep=True)
    asset_summary = pd.DataFrame(
        {
            "mean_periodic_return": returns.mean(),
            "annualized_return": returns.mean() * context.periods_per_year,
            "annualized_volatility": returns.std(ddof=1) * np.sqrt(context.periods_per_year),
            "minimum_period_return": returns.min(),
            "maximum_period_return": returns.max(),
        }
    )
    kwargs = dict(backtest_kwargs or {})
    kwargs.setdefault("weights", "equal_weight")
    kwargs.setdefault("rebalance", "monthly")
    kwargs.setdefault("benchmark", "equal_weight")
    backtest = allocator.backtest(**kwargs)
    return ExportableReport(
        title="Portfolio Report",
        subtitle="Return panel, default allocation diagnostics, and deterministic backtest summary.",
        metadata=generated_metadata(
            "portfolio",
            assets=len(context.asset_symbols),
            observations=len(returns),
            periods_per_year=context.periods_per_year,
        ),
        provenance=merge_provenance(
            [getattr(context, "provenance", None), getattr(backtest, "provenance", None)],
            provider="derived",
            dataset="portfolio_report",
            transformation_steps=("portfolio report generation",),
            request={"assets": len(context.asset_symbols), "observations": len(returns)},
        ),
        sections=(
            ReportSection(
                "Portfolio context",
                metrics={
                    "asset_count": len(context.asset_symbols),
                    "observation_count": len(returns),
                    "annual_risk_free_rate": context.annual_risk_free_rate,
                    "allow_short_positions": context.allow_short_positions,
                },
            ),
            ReportSection(
                "Asset return summary", tables=(ReportTable("Asset metrics", asset_summary),)
            ),
            ReportSection("Backtest summary", metrics=backtest.summary()),
            ReportSection(
                "Drawdown events",
                tables=(ReportTable("Largest drawdowns", backtest.drawdown_events(top=5)),),
            ),
        ),
    )


def build_backtest_report(backtest: object) -> ExportableReport:
    """Build an exportable report for a deterministic portfolio backtest result."""
    sections: list[ReportSection] = [
        ReportSection("Performance summary", metrics=backtest.summary()),
        ReportSection("Cost summary", metrics=backtest.cost_summary()),
        ReportSection(
            "Drawdown events",
            tables=(ReportTable("Largest drawdowns", backtest.drawdown_events(top=10)),),
        ),
        ReportSection(
            "Contribution summary",
            tables=(ReportTable("Asset contributions", backtest.contribution_summary()),),
        ),
        ReportSection(
            "Return table", tables=(ReportTable("Calendar returns", backtest.return_table()),)
        ),
    ]
    benchmark_summary = backtest.benchmark_summary()
    if benchmark_summary:
        sections.insert(1, ReportSection("Benchmark summary", metrics=benchmark_summary))
    return ExportableReport(
        title="Portfolio Backtest Report",
        subtitle="Deterministic rebalanced portfolio simulation diagnostics.",
        metadata=generated_metadata(
            "portfolio_backtest",
            rebalance=getattr(backtest, "rebalance", None),
            weight_policy=getattr(backtest, "weight_policy", None),
            periods_per_year=getattr(backtest, "periods_per_year", None),
        ),
        sections=tuple(sections),
        provenance=merge_provenance(
            [getattr(backtest, "provenance", None)],
            provider="derived",
            dataset="portfolio_backtest_report",
            transformation_steps=("backtest report generation",),
            request={"rebalance": getattr(backtest, "rebalance", None)},
        ),
    )


def build_credit_report(assessment: object) -> ExportableReport:
    """Build an exportable report for a credit-proxy assessment."""
    metrics = dict(getattr(assessment, "metrics", {}))
    piotroski = dict(getattr(assessment, "piotroski_signals", {}))
    disclosures = tuple(getattr(assessment, "disclosures", ()))
    return ExportableReport(
        title="Credit Proxy Report",
        subtitle="Transparent fundamental credit-proxy diagnostics; not a credit rating or probability of default.",
        metadata=generated_metadata("credit_proxy"),
        provenance=merge_provenance(
            [getattr(assessment, "provenance", None)],
            provider="derived",
            dataset="credit_proxy_report",
            transformation_steps=("credit report generation",),
        ),
        sections=(
            ReportSection(
                "Synthetic score",
                metrics={
                    "synthetic_credit_proxy_score": getattr(
                        assessment, "synthetic_credit_proxy_score", None
                    ),
                    "synthetic_credit_proxy_band": getattr(
                        assessment, "synthetic_credit_proxy_band", None
                    ),
                    "available_score_weight": getattr(assessment, "available_score_weight", None),
                },
            ),
            ReportSection(
                "Metrics",
                tables=(
                    ReportTable(
                        "Credit metrics", pd.DataFrame([metrics]).T.rename(columns={0: "value"})
                    ),
                ),
            ),
            ReportSection(
                "Piotroski signals",
                tables=(
                    ReportTable(
                        "Signals", pd.DataFrame([piotroski]).T.rename(columns={0: "signal"})
                    ),
                ),
            ),
            ReportSection("Disclosures", body="\n".join(f"- {item}" for item in disclosures)),
        ),
    )


def build_risk_dashboard_report(dashboard: object) -> ExportableReport:
    """Build an exportable report for an integrated risk dashboard."""
    summary = dashboard.summary()
    sections = [
        ReportSection("Portfolio summary", metrics=summary.get("portfolio", {})),
        ReportSection("Risk-contribution summary", metrics=summary.get("risk_contribution", {})),
        ReportSection("Correlation summary", metrics=summary.get("correlation", {})),
        ReportSection("Credit summary", metrics=summary.get("credit", {})),
        ReportSection(
            "Risk contribution",
            tables=(ReportTable("Risk contribution by asset", dashboard.risk_contribution()),),
        ),
        ReportSection(
            "Credit scores", tables=(ReportTable("Credit scores", dashboard.credit_scores()),)
        ),
        ReportSection(
            "Correlation matrix",
            tables=(ReportTable("Asset correlation", dashboard.correlation()),),
        ),
    ]
    return ExportableReport(
        title="Integrated Risk Dashboard Report",
        subtitle="Combined portfolio, drawdown, correlation, and credit-proxy diagnostics.",
        metadata=generated_metadata("risk_dashboard"),
        sections=tuple(sections),
        provenance=merge_provenance(
            [getattr(dashboard, "provenance", None)],
            provider="derived",
            dataset="risk_dashboard_report",
            transformation_steps=("risk dashboard report generation",),
        ),
    )


def _section_to_markdown(section: ReportSection) -> list[str]:
    """Render one section as Markdown lines."""
    lines = [f"## {section.title}", ""]
    if section.body:
        lines.extend([str(section.body), ""])
    if section.metrics:
        for key, value in section.metrics.items():
            lines.append(f"- **{_humanize_key(key)}:** {_format_value(value)}")
        lines.append("")
    for table in section.tables:
        lines.append(f"### {table.title}")
        if table.description:
            lines.extend(["", str(table.description)])
        lines.extend(["", _frame_to_markdown(table.frame()), ""])
    return lines


def _section_to_html(section: ReportSection) -> list[str]:
    """Render one section as HTML fragments."""
    parts = [f"<h2>{escape(section.title)}</h2>"]
    if section.body:
        parts.append(
            "".join(
                f"<p>{escape(line)}</p>" for line in str(section.body).splitlines() if line.strip()
            )
        )
    if section.metrics:
        parts.append("<dl>")
        for key, value in section.metrics.items():
            parts.append(
                f"<dt>{escape(_humanize_key(key))}</dt><dd>{escape(_format_value(value))}</dd>"
            )
        parts.append("</dl>")
    for table in section.tables:
        parts.append(f"<h3>{escape(table.title)}</h3>")
        if table.description:
            parts.append(f"<p>{escape(table.description)}</p>")
        parts.append(_frame_to_html(table.frame()))
    return parts


def _format_value(value: object) -> str:
    """Return a compact human-readable representation of one report value."""
    if value is None:
        return "n/a"
    if isinstance(value, (float, np.floating)):
        numeric = float(value)
        if np.isnan(numeric):
            return "n/a"
        if np.isinf(numeric):
            return "inf" if numeric > 0 else "-inf"
        return f"{numeric:.6g}"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Mapping):
        return ", ".join(
            f"{_humanize_key(key)}={_format_value(item)}" for key, item in value.items()
        )
    return str(value)


def _humanize_key(key: object) -> str:
    """Convert a machine key into a readable label."""
    return str(key).replace("_", " ").strip().title()


def _write_text(path: str | Path, text: str) -> Path:
    """Write text to a path using UTF-8 and return the destination."""
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def _frame_to_markdown(frame: pd.DataFrame) -> str:
    """Return a dependency-free Markdown table for a DataFrame."""
    formatted = _format_frame(frame)
    columns = ["index"] + [str(column) for column in formatted.columns]
    rows = [
        [str(index)] + [str(value) for value in formatted.loc[index].tolist()]
        for index in formatted.index
    ]
    widths = [len(column) for column in columns]
    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row, strict=True)]
    header = (
        "| "
        + " | ".join(column.ljust(width) for column, width in zip(columns, widths, strict=True))
        + " |"
    )
    divider = "| " + " | ".join("-" * width for width in widths) + " |"
    body = [
        "| " + " | ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)) + " |"
        for row in rows
    ]
    return "\n".join([header, divider, *body])


def _frame_to_html(frame: pd.DataFrame) -> str:
    """Return a dependency-free HTML table for a DataFrame."""
    formatted = _format_frame(frame)
    columns = ["index"] + [str(column) for column in formatted.columns]
    parts = ["<table>", "<thead><tr>"]
    parts.extend(f"<th>{escape(column)}</th>" for column in columns)
    parts.append("</tr></thead>")
    parts.append("<tbody>")
    for index, row in formatted.iterrows():
        parts.append("<tr>")
        parts.append(f"<td>{escape(str(index))}</td>")
        for value in row.tolist():
            parts.append(f"<td>{escape(str(value))}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def _format_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Format DataFrame values for textual reports."""
    clean = frame.copy(deep=True)
    if isinstance(clean.columns, pd.MultiIndex):
        clean.columns = [" / ".join(map(str, column)).strip() for column in clean.columns]
    if isinstance(clean.index, pd.MultiIndex):
        clean.index = [" / ".join(map(str, index)).strip() for index in clean.index]
    if hasattr(clean, "map"):
        return clean.map(_format_value)
    return clean.applymap(_format_value)


def _markdown_to_plain_lines(markdown: str) -> list[str]:
    """Convert Markdown report text into wrapped plain lines for PDF export."""
    plain_lines: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.replace("**", "").replace("#", "").strip()
        if not line:
            plain_lines.append("")
            continue
        if line.startswith("|"):
            line = line.replace("|", " ")
        wrapped = wrap(line, width=95) or [""]
        plain_lines.extend(wrapped)
    return plain_lines


def _build_text_pdf(lines: Sequence[str], *, title: str) -> bytes:
    """Build a small valid PDF document from plain text lines."""
    lines_per_page = 48
    pages = [
        list(lines[index : index + lines_per_page])
        for index in range(0, len(lines), lines_per_page)
    ] or [[title]]
    objects: list[bytes] = []
    catalog_id = 1
    pages_id = 2
    font_id = 3
    page_ids: list[int] = []
    content_ids: list[int] = []
    next_id = 4
    for _ in pages:
        page_ids.append(next_id)
        content_ids.append(next_id + 1)
        next_id += 2
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("latin-1"))
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for _page_id, content_id, page_lines in zip(page_ids, content_ids, pages, strict=True):
        stream = _pdf_text_stream(page_lines)
        objects.append(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode(
                "latin-1"
            )
        )
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode("latin-1")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, payload in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode("latin-1"))
        output.extend(payload)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "latin-1"
        )
    )
    return bytes(output)


def _pdf_text_stream(lines: Sequence[str]) -> bytes:
    """Return one PDF text stream for a page of report lines."""
    commands = ["BT", "/F1 10 Tf", "50 750 Td", "14 TL"]
    first = True
    for line in lines:
        if first:
            first = False
        else:
            commands.append("T*")
        commands.append(f"({_escape_pdf_text(line)}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _escape_pdf_text(text: str) -> str:
    """Escape text for a literal PDF string."""
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


__all__ = [
    "ExportableReport",
    "ReportSection",
    "ReportTable",
    "build_backtest_report",
    "build_credit_report",
    "build_option_model_report",
    "build_portfolio_allocator_report",
    "build_risk_dashboard_report",
    "generated_metadata",
]
